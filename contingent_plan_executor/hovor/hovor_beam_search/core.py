from cmath import log
from typing import List, Union, Dict
from hovor.hovor_beam_search.data_structs import *
from hovor.hovor_beam_search.init_stubs import *
from hovor.hovor_beam_search.graph_setup import BeamSearchGraphGenerator
import json


EPSILON = log(0.00000001)


class BeamSearchExecutor:
    """Class that houses all information needed to execute the beam search
    algorithm.

    Args:
        k (int): The number of beams to use.
        max_fallbacks (int): The maximum number of fallbacks that can occur
            in any beam before the probability is tanked by resetting the
            score to the log of a low number epsilon.
        conversation (List[Dict[str, str]]): The conversation to be
            explored. Should be in the format

            .. code-block:: python

                [
                    {"AGENT": "Hi!"},
                    {"USER": "Hello."}
                ]

        build_graph (bool): Indicates if diagrams are to be compiled.
            Defaults to True.
        graphs_path (str): The path where the graphs and output stats will be stored.
        **kwargs Any parameters necessary to instantiate your
            Rollout class.
    """

    def __init__(
        self,
        k: int,
        max_fallbacks: int,
        conversations: List[List[Dict[str, str]]],
        graphs_path: str = None,
        **kwargs,
    ):
        self.k = k
        self.max_fallbacks = max_fallbacks
        self.conversations = self._preprocess_conversations(conversations)
        self.graphs_path = graphs_path
        self.rollout_param = kwargs

    @property
    def k(self):
        return self._k

    @k.setter
    def k(self, value: int):
        if value < 1:
            raise ValueError("The value of k must be a positive integer.")
        self._k = value

    @property
    def max_fallbacks(self):
        return self._max_fallbacks

    @max_fallbacks.setter
    def max_fallbacks(self, value: int):
        if value < 1:
            raise ValueError(
                "The number of fallbacks needed to tank a beam must be a positive integer."
            )
        self._max_fallbacks = value

    def _preprocess_conversations(self, conversations):
        new_convos = []
        for conv in conversations:
            messages = []
            for msg_cfg in conv["messages"]:
                if msg_cfg["agent_message"]:
                    messages.append({"AGENT": msg_cfg["agent_message"]})
                if msg_cfg["user_message"]:
                    messages.append({"USER": msg_cfg["user_message"]})
            new_convos.append(messages)
        return new_convos

    def _prep_for_new_search(self):
        """Resets the beams and graph generator to begin a new search."""
        self.beams = []
        self.graph_gen = BeamSearchGraphGenerator(self.k)

    def _handle_message_actions(self):
        """Handles "message actions" for all beams.

        A "message action" occurs when an action only has one possible outcome.
        In that case, that outcome should be immediately executed as the action
        doesn't take (or need) any user input to execute that outcome.
        """
        # iterate through all the beams
        for i in range(len(self.beams)):
            # if result is not None, then the last action was a message action
            result = self.beams[i].rollout.update_if_message_action(
                self.beams[i].last_action.name
            )
            if result:
                # create an intent from the message action.
                intent = Intent(
                    name=result["intent"],
                    probability=result["confidence"],
                    beam=i,
                    score=log(result["confidence"]) + self.beams[i].last_action.score,
                    outcome=result["outcome"],
                )
                # update the last intent and rankings and add it to the beam
                self.beams[i].last_intent = intent
                self.beams[i].rankings.append(intent)
                self.graph_gen.create_nodes_highlight_k(
                    {intent.name: round(intent.score.real, 4)},
                    "lightgoldenrod1",
                    self.beams[i].last_action.name,
                    i,
                    [intent.name],
                )

    def _reconstruct_beam_w_output(
        self, outputs: List[Union[Action, Intent]]
    ) -> List[Beam]:
        """Reconstructs/creates new beams given the top k outputs determined.
        Note: The outputs cannot simply be appended to the appropriate beam
        as it often occurs that a single beam will be "extended" more than once
        and those options need to be stored as new, separate beams.

        Args:
            outputs (List[Union[Action, Intent]]): The top k actions or
                intents that match the last utterance.

        Returns:
            List[Beam]: The new Beams with the outputs added.
        """
        new_beams = []
        actions = isinstance(outputs[0], Action)
        for i in range(len(outputs)):
            # grab the beam that the output came from
            at_beam = outputs[i].beam
            # grab that beam's fallbacks
            fallbacks = self.beams[at_beam].fallbacks
            # if we're dealing with actions
            if actions:
                # set the last action to the output and keep the last intent
                # the same
                last_action = outputs[i]
                last_intent = self.beams[at_beam].last_intent
            # otherwise, do the reverse and update the # of fallbacks
            # if necessary
            else:
                last_intent = outputs[i]
                last_action = self.beams[at_beam].last_action
                if outputs[i].is_fallback():
                    fallbacks += 1
            # update the rankings and scores and create a new Beam
            new_beams.append(
                Beam(
                    last_action,
                    last_intent,
                    self.beams[at_beam].rankings + [outputs[i]],
                    self.beams[at_beam].rollout.copy(),
                    self.beams[at_beam].scores + [log(outputs[i].probability)],
                    fallbacks,
                )
            )
        return new_beams

    def beam_search(self):
        """The main beam search algorithm.

        NOTE: We assume that the provided conversation begins with an action,
        due to the fact that in dialogue-as-planning, agents use actions and
        users respond to those actions with one of a set of given intents.

        Beam search is executed on all the conversations provided.
        A JSON with statistics that indicates which conversations failed/passed
        is returned.
        """
        json_out = []
        for idx in range(len(self.conversations)):
            # resets the beams and creates a new "Rollout"
            self._prep_for_new_search()
            start_rollout = HovorRollout(**self.rollout_param)
            # generates the starting values.
            starting_values = start_rollout.get_action_confidences(self.conversations[idx][0])
            outputs = [
                Action(name=key, probability=val, beam=index, score=log(val))
                for index, (key, val) in enumerate(starting_values.items())
            ]
            # if there are less starting actions than there are beams, duplicate
            # the best action until we reach self.k
            while len(outputs) < self.k:
                outputs.append(outputs[0])

            for beam in range(self.k):
                # create the initial beams
                self.beams.append(
                    Beam(
                        outputs[beam],
                        None,
                        [outputs[beam]],
                        HovorRollout(**self.rollout_param),
                        [log(outputs[beam].probability)],
                        0,
                    )
                )
                # add the k actions to the graph
                self.graph_gen.create_nodes_highlight_k(
                    {outputs[beam].name: round(outputs[beam].score.real, 4)},
                    "skyblue",
                    "START",
                    beam,
                    [outputs[beam].name],
                )
            self._handle_message_actions()
            # add the (total actions - k) nodes that won't be picked to the graph
            self.graph_gen.create_from_parent(
                {
                    action.name: round(action.score.real, 4)
                    for action in outputs[self.k :]
                },
                "skyblue",
            )
            # iterate through all utterances (the first was already observed)
            for utterance in self.conversations[idx][1:]:
                # denotes if this is a user utterance or an agent action
                user = "USER" in utterance
                outputs = []
                # iterate through all the beams
                for beam in range(len(self.beams)):
                    # if this is a user utterance, get the k highest intents by
                    # observing the utterance in the context of the last action
                    if user:
                        all_intent_confs = self.beams[
                            beam
                        ].rollout.get_intent_confidences(
                            self.beams[beam].last_action.name, utterance
                        )
                        # create beam search "Intents" given the output
                        for intent_cfg in all_intent_confs:
                            # find the score by taking the sum of the current
                            # beam thread which should be a list of log(prob)
                            outputs.append(
                                Intent(
                                    name=intent_cfg["intent"],
                                    probability=intent_cfg["confidence"],
                                    beam=beam,
                                    score=sum(self.beams[beam].scores)
                                        + log(intent_cfg["confidence"])
                                    ,
                                    outcome=intent_cfg["outcome"],
                                )
                            )
                    # otherwise, do the same, but get the k highest actions instead
                    # and convert those into beam search "Actions"
                    else:
                        all_act_confs = self.beams[beam].rollout.get_action_confidences(
                            utterance,
                            self.beams[beam].last_action.name,
                            self.beams[beam].last_intent.name,
                            self.beams[beam].last_intent.outcome,
                        )
                        for act, conf in all_act_confs.items():
                            outputs.append(
                                Action(
                                    name=act,
                                    probability=conf,
                                    beam=beam,
                                    score=sum(self.beams[beam].scores) + log(conf),
                                )
                            )
                # sort the outputs (k highest actions or intents) by score
                outputs.sort()
                # store all the outputs (only to use in graph creation) before
                # splicing the top k
                all_outputs = outputs
                outputs = outputs[0 : self.k]

                # for the graph: track which nodes are "chosen" for each beam
                node_color = "lightgoldenrod1" if user else "skyblue"
                graph_beam_chosen_map = {idx: [] for idx in range(self.k)}
                for output in outputs:
                    graph_beam_chosen_map[output.beam].append(output.name)
                for beam, chosen in graph_beam_chosen_map.items():
                    self.graph_gen.create_nodes_highlight_k(
                        # filter ALL outputs by outputs belonging to the
                        # current beam
                        # using the filtered outputs, map intents to
                        # probabilities to use in the graph
                        {
                            output.name: round(output.score.real, 4)
                            for output in all_outputs
                            if output.beam == beam
                        },
                        node_color,
                        self.beams[beam].rankings[-1].name,
                        beam,
                        chosen,
                    )
                # update the graph's beams so that the parent/id map matches
                # the reconstructed beams. we have to do this because again,
                # outputs cannot just be appended to beams, as multiple outputs
                # could have been chosen from a single previous beam. so, the
                # "graph" beams need to be updated to match the current
                # structure.
                self.graph_gen.beams = [
                    BeamSearchGraphGenerator.GraphBeam(
                        self.graph_gen.beams[output.beam].parent_nodes_id_map
                    )
                    for output in outputs
                ]
                # add the outputs to the beams
                self.beams = self._reconstruct_beam_w_output(outputs)
                # if we're dealing with a user utterance, update the state
                # for all beams; otherwise, check if we're dealing with any message
                # actions
                if user:
                    for beam in self.beams:
                        beam.rollout.update_state(
                            beam.last_action.name,
                            beam.last_intent.outcome,
                        )
                else:
                    self._handle_message_actions()
                # tank the scores if we've hit the max fallbacks
                for beam in self.beams:
                    if beam.fallbacks == self.max_fallbacks:
                        beam.scores = [EPSILON]
            # once we've reached the end of the conversation, iterate through all
            # beams
            for i in range(len(self.beams)):
                # add a "GOAL REACHED" node if necessary
                if self.beams[i].rollout.get_reached_goal():
                    self.graph_gen.set_last_chosen(
                        self.beams[i].rankings[-1].name, i
                    )
                    self.graph_gen.complete_conversation(
                        round(self.beams[i].rankings[-1].score.real, 4)
                    )
                # highlight all the "final" beams
                head = "0"
                for elem in self.beams[i].rankings:
                    tail = head
                    # beam_id must be > than the head to prevent referencing
                    # previous nodes with the same name
                    head = (
                        self.graph_gen.beams[i]
                        .parent_nodes_id_map[elem.name]
                        .pop(0)
                    )
                    while int(head) <= int(tail):
                        head = (
                            self.graph_gen.beams[i]
                            .parent_nodes_id_map[elem.name]
                            .pop(0)
                        )
                    self.graph_gen.graph.edge(
                        tail,
                        head,
                        color="forestgreen",
                        penwidth="10.0",
                        arrowhead="normal",
                    )
            self.graph_gen.graph.render(f"{self.graphs_path}/convo_{idx}", cleanup=True)
            # sort the beams by total score (largest first)
            self.beams.sort(reverse=True)
            # we consider the conversation to not be handled if the best beam
            # is <= the epsilon value
            json_out.append(
                {
                    "conversation": self.conversations[idx],
                    "status": "failure"
                    if self.beams[0].scores[-1].real <= EPSILON.real
                    else "success",
                }
            )
        with open(f"{self.graphs_path}/output_stats.json", "w") as out:
            out.write(json.dumps(json_out, indent=4))

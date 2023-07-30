from cmath import log
from typing import List, Union, Dict
from hovor.hovor_beam_search.data_structs import *
from hovor.hovor_beam_search.init_stubs import *
from hovor.hovor_beam_search.graph_setup import BeamSearchGraph, NodeType
from hovor.configuration.json_configuration_postprocessing import (
    map_action_to_outcome_determiner,
)
import json
import matplotlib.pyplot as plt
import os


EPSILON = 0.000000000000000000001


class ConversationAlignmentExecutor:
    """Class that houses all information needed to execute the beam search
    algorithm.

    Args:
        k (int): The number of beams to use.
        max_fallbacks (int): The maximum number of fallbacks that can occur
            in any beam before the probability is tanked by resetting the
            score to the log of a low number epsilon.
        conversation_paths (List[str]): Paths that store the conversations to be
            explored. `preprocess_conversations` should convert conversations
            to the format

            .. code-block:: python

            [
                [
                    {"AGENT": "Hi!"},
                    {"USER": "Hello."}
                ]
            ]

        build_graph (bool): Indicates if diagrams are to be compiled.
            Defaults to True.
        graphs_path (str): The path where the graphs and output stats will be stored.
        rollout_param (**kwargs): Any parameters necessary to instantiate your
            Rollout class.
    """

    def __init__(
        self,
        k: int,
        max_fallbacks: int,
        conversation_paths: str,
        graphs_path: str = None,
        **kwargs,
    ):
        self.k = k
        self.max_fallbacks = max_fallbacks
        self.conversations = preprocess_conversations(conversation_paths)
        self.conversation_paths = conversation_paths
        self.graphs_path = graphs_path
        self.rollout_param = kwargs
        self.in_run = True
        self.json_data = []

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

    def _sum_scores(self, beam, confidence):
        # avoid math error when taking the log
        if confidence == 0:
            confidence = EPSILON
        return sum(self.beams[beam].scores) + log(confidence)

    @staticmethod
    def _get_action_node_type(action):
        return (
            NodeType.MESSAGE_ACTION
            if HovorRollout.is_message_action(action)
            else NodeType.DEFAULT_ACTION
        )

    def _prep_for_new_search(self):
        """Resets the beams and graph generator to begin a new search."""
        self.beams = []
        self.graph_gen = BeamSearchGraph(self.k)

    def _get_last_head_from_action(self, beam):
        return (
            self.beams[beam].last_action.name
            if HovorRollout.is_message_action(self.beams[beam].last_action.name)
            else self.beams[beam].rankings[-1].name
        )

    def _is_drop_off(self, beam: int, node_score: float, prev_idx: int):
        """Determines if the difference between the scores of two rankings (the node
        provided and the node that precedes it in the list of rankings) is big enough
        to determine a "drop-off."

        Args:
            beam (int): The beam where the rankings are being compared.
            node_score (float): The score of the node to be compared against the
                last ranking.
            prev_idx (int): The index of the node preceding this one.
        
        Returns:
            (bool) True if the difference between the scores of two rankings is big
            enough to determine a "drop-off," False otherwise.
        """
        return (node_score - self.beams[beam].rankings[prev_idx].score).real <= log(EPSILON).real

    def _determine_node_type(self, beam: int, node_score: float, default_type: NodeType):
        """Returns the DROP_OFF NodeType if the node is determined to be a "drop-off"
        point and the given NodeType otherwise. This is only used within the algorithm
        as the beams are being generated, so we can just pass -1 to :py:func:`_is_drop_off
        <beam_search.core._is_drop_off>` (use the last node as reference).
        
        Args:
            beam (int): The beam where the rankings are being compared.
            node_score (float): The score of the node to be compared against the
                last ranking.
            default_type (NodeType): The NodeType that will be otherwise set if a
                "drop-off" is not detected.
        """
        return NodeType.DROP_OFF if self._is_drop_off(beam, node_score, -1) else default_type

    def _handle_message_actions(self):
        """Handles "message actions" for all beams.

        A "message action" occurs when an action only has one possible outcome.
        In that case, that outcome should be immediately executed as the action
        doesn't take (or need) any user input to execute that outcome.
        NOTE: message actions don't have intents (like dialogue actions) or meaningful
        outcomes (like system/api actions) so we don't add these to the graph.
        """
        # iterate through all the beams
        for beam in range(len(self.beams)):
            # if result is not None, then the last action was a message action
            result = self.beams[beam].rollout.update_if_message_action(
                self.beams[beam].last_action.name, self.in_run
            )
            if result:
                # create an intent from the message action.
                intent = Intent(
                    name=result["intent"],
                    probability=result["confidence"],
                    beam=beam,
                    score=self._sum_scores(
                        beam, result["confidence"]
                    ),
                    outcome=result["outcome"],
                )
                # update the last intent and rankings and add it to the beam
                self.beams[beam].last_intent = intent
                self.beams[beam].rankings.append(intent)

    def _handle_system_actions(self, beam: int):
        # before we begin, check if we have the valid case for
        # executing a system/api action (it is the only applicable
        # action) and iterate until this is no longer the case.
        # we also want to break if we reach the goal along the way!
        while (
            self.beams[beam].rollout.check_system_case()
            and not self.beams[beam].rollout.get_reached_goal()
        ):
            action = list(self.beams[beam].rollout.applicable_actions)[0]
            # execute the action
            ranked_groups = self.beams[beam].rollout.call_outcome_determiner(
                action,
                HovorRollout.configuration_provider._create_outcome_determiner(
                    action,
                    {
                        "outcome_determiner": map_action_to_outcome_determiner(
                            HovorRollout.data["actions"][action]
                        )
                    },
                ),
            )
            # update the state and beam
            action = Action(
                name=action,
                probability=1.0,
                beam=beam,
                score=self._sum_scores(
                    beam, 1.0
                ),
            )

            # get the intents from the ranked group (outcome, confidence) tuples
            # note that we use the outcome name for system/api actions as they have no intent (note that we use a shortened version)
            all_intents = [
                Intent(
                    name=group[0].name.split("-EQ-")[1],
                    probability=group[1],
                    beam=beam,
                    score=self._sum_scores(
                        beam, group[1]
                    ),
                    outcome=group[0].name,
                )
                for group in ranked_groups
            ]

            all_intents.sort()

            self.beams[beam].rollout.update_state(
                action.name, all_intents[0].outcome, self.in_run
            )
            # update the graph
            # add action node (node that we don't check for drop-offs since the confidence is always 1.0)
            self.graph_gen.create_nodes_from_beams(
                {action.name: (round(action.score.real, 4), NodeType.SYSTEM_API)},
                beam,
                self._get_last_head_from_action(beam),
                [action.name],
            )
            self.beams[beam].last_action = action
            self.beams[beam].rankings.append(action)
            # add "intent" (again, here we use the outcome name) nodes
            self.graph_gen.create_nodes_from_beams(
                {intent.name: (round(intent.score.real, 4), self._determine_node_type(beam, intent.score, NodeType.SYSTEM_API)) for intent in all_intents},
                beam,
                action.name,
                [all_intents[0].name],
            )
            
            self.beams[beam].last_intent = all_intents[0]
            self.beams[beam].rankings.append(all_intents[0])

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
                    self.beams[at_beam].fallbacks += 1
            # update the rankings and scores and create a new Beam.
            # note that for the rollout, we have to use a COPY because
            # otherwise, in the case where multiple beams extend from
            # one outcome, aliasing can occur where we don't want it.
            new_beams.append(
                Beam(
                    last_action,
                    last_intent,
                    self.beams[at_beam].rankings + [outputs[i]],
                    self.beams[at_beam].rollout.copy(),
                    self.beams[at_beam].scores + [log(outputs[i].probability)],
                    self.beams[at_beam].fallbacks,
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

        NOTE ABOUT THE HANDLING OF ACTION TYPES:
            There are currently limitations on the types of actions the
            algorithm can handle. While the algorithm can handle all dialogue actions,
            system and api actions pose a problem as they do not directly rely on user
            input to execute. This leds to ambiguity in terms of which action to
            execute if multiple system or api actions are applicable in a given state
            and there may not be enough beams to cover all possibilities.

            It is likely possible to extend the algorithm to handle these cases. In the
            meantime, though, we implemented a workaround to at least handle some system
            actions so that the possibility for agent complexity is maintained. The
            rules are as follows:
            - A system/api action will only be executed if it is the only applicable action
              in the state. The process is iterated until we are no longer in that state
              (i.e. have some dialogue/message action to execute).
            - When a system/api action is executed, we just take the highest-confidence outcome
              (pretty much always 1.0) and use that to extend the relevant beam. Since
              these actions are meant to perform some logic, the results are typically binary
              and/or only one applies in the current state (i.e. we can't "explore" the
              other return results of an api call by giving it the same input, or explore
              the other outcomes in the context-dependent outcome determiner). so, we don't
              restructure the beams here, only append to the existing ones.
            - System/api actions, where there exist applicable dialogue action(s), are
              ignored for the rest of the iteration. This is because system/api actions have
              no messages to compare against.
            - If the algorithm comes across a case where you have multiple applicable
              system/api actions and no dialogue or message actions, an error is raised.
              This is because it is ambiguous which system/api action to execute.
            - The algorithm will time out if it spends too long running system actions. (This
              can especially happen if a system action does not "deactivate" itself and thus
              runs forever).

            We also make the assumption that a system action that executes automatically
            has a confidence of 1.0 (since it is not being compared against any messages).
            However, the outcomes have their own confidences returned by the outcome
            determiner.

            Finally, we note the difference between system/api actions and message actions.
            Although message actions are handled in a similar fashion in that we update the
            state and applicable actions through the singular deterministic outcome, message
            actions still "absorb" a dialogue from the input conversation while system/api
            actions do not. So, message actions update the state AFTER being compared against
            an utterance whereas the case for system/api actions needs to be checked BEFORE
            continuing the iteration.
        """
        for idx in range(len(self.conversations)):
            self.json_data.append(
                {
                    "conversation": self.conversations[idx],
                    "status": None,
                    "drop-off nodes": []
                }
            )
            # resets the beams and creates a new "Rollout"
            self._prep_for_new_search()
            start_rollout = HovorRollout(**self.rollout_param)
            # generates the starting values.
            starting_values = start_rollout.get_action_confidences(
                self.conversations[idx][0]
            )
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
                self.graph_gen.create_nodes_from_beams(
                    {outputs[beam].name: (round(outputs[beam].score.real, 4), ConversationAlignmentExecutor._get_action_node_type(outputs[beam].name))},
                    beam,
                    "START",
                    [outputs[beam].name],
                )

            self._handle_message_actions()

            # add the (total actions - k) nodes that won't be picked to the graph
            for action in outputs[self.k :]:
                self.graph_gen.create_nodes_outside_beams(
                    {action.name: (round(action.score.real, 4), ConversationAlignmentExecutor._get_action_node_type(action.name))},
                    "0",
                )
            # iterate through all utterances (the first was already observed)
            for utterance_idx in range(1, len(self.conversations[idx])):
                # denotes if this is a user utterance or an agent action
                utterance = self.conversations[idx][utterance_idx]
                # we are "in run" as long as there are more utterances following
                # the current one
                self.in_run = utterance_idx == len(self.conversations[idx]) - 2
                user = "USER" in utterance
                outputs = []
                # iterate through all the beams
                for beam in range(len(self.beams)):
                    # first handle system actions if we can
                    self._handle_system_actions(beam)

                    # if this is a user utterance, get the k highest intents by
                    # observing the utterance in the context of the last action
                    if user:
                        all_intent_confs = self.beams[
                            beam
                        ].rollout.get_intent_confidences(
                            self.beams[beam].last_action.name, utterance
                        )
                        for intent_cfg in all_intent_confs:
                            outputs.append(
                                # create beam search "Intents" given the output
                                Intent(
                                    name=intent_cfg["intent"],
                                    probability=intent_cfg["confidence"],
                                    beam=beam,
                                    # find the score by taking the sum of the current
                                    # beam thread which should be a list of log(prob)
                                    score=self._sum_scores(
                                        beam,
                                        intent_cfg["confidence"],
                                    ),
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
                                    score=self._sum_scores(
                                        beam, conf
                                    ),
                                )
                            )
                # sort the outputs (k highest actions or intents) by score
                outputs.sort()
                # store all the outputs (only to use in graph creation) before
                # splicing the top k
                all_outputs = outputs
                outputs = outputs[0 : self.k]

                # for the graph: track which nodes are "chosen" for each beam
                graph_beam_chosen_map = {idx: [] for idx in range(self.k)}
                for output in outputs:
                    if user:
                        # tank the score if necessary (need to do this before adding nodes
                        # to the graph)
                        if output.is_fallback():
                            # we don't actually want to change the fallback value until
                            # we restructure the beams because of the case where multiple
                            # outputs stem from one beam (only one resulting beam would have
                            # the increase, not all).
                            if self.beams[output.beam].fallbacks + 1 == self.max_fallbacks:
                                output.probability = EPSILON
                                output.score = self._sum_scores(output.beam, EPSILON)
                    graph_beam_chosen_map[output.beam].append(output)
                for beam, chosen in graph_beam_chosen_map.items():
                    # don't add message action intents/outcomes to the graph
                    last_action_message = HovorRollout.is_message_action(
                        self.beams[beam].last_action.name
                    )
                    if not (user and last_action_message):
                        self.graph_gen.create_nodes_from_beams(
                            # filter ALL outputs by outputs belonging to the
                            # current beam
                            # using the filtered outputs, map intents to
                            # probabilities to use in the graph
                            {
                                output.name: (round(output.score.real, 4), self._determine_node_type(
                                        beam,
                                        output.score,
                                        NodeType.INTENT
                                        if user
                                        else (
                                            ConversationAlignmentExecutor._get_action_node_type(
                                                output.name
                                            )
                                        )
                                    )
                                )
                                for output in all_outputs
                                if output.beam == beam
                            },
                            beam,
                            # for actions succeeding message actions, use the last action as the head
                            self._get_last_head_from_action(beam),
                            [c.name for c in chosen],
                        )
                # update the graph's beams so that the parent/id map matches
                # the reconstructed beams. we have to do this because again,
                # outputs cannot just be appended to beams, as multiple outputs
                # could have been chosen from a single previous beam. so, we
                # have to create copies because in that case aliasing will occur.
                self.graph_gen.beams = [
                    self.graph_gen.beams[output.beam].copy() for output in outputs
                ]
                # add the outputs to the beams
                self.beams = self._reconstruct_beam_w_output(outputs)
                # if we're dealing with a user utterance, update the state
                # for all beams; otherwise, check if we're dealing with any message
                # actions
                if user:
                    for beam in self.beams:
                        beam.rollout.update_state(
                            beam.last_action.name, beam.last_intent.outcome, self.in_run
                        )
                else:
                    self._handle_message_actions()

            # we've reached the end of the conversation
            for beam in range(len(self.beams)):
                # run any straggling system actions (often this is needed to reach the goal).
                self._handle_system_actions(beam)

                # add a "GOAL REACHED" node if necessary
                if self.beams[beam].rollout.get_reached_goal():
                    self.graph_gen.create_nodes_from_beams(
                        {
                            "GOAL REACHED": (round(
                                self.beams[beam].rankings[-1].score.real, 4
                            ), NodeType.GOAL)
                        },
                        beam,
                        self._get_last_head_from_action(beam),
                        ["GOAL REACHED"],
                    )
                    self.beams[beam].rankings.append(Output("GOAL REACHED", 1.0, beam, self.beams[beam].rankings[-1].score))
                # highlight all the "final" beams
                head = "0"
                for node in self.beams[beam].rankings:
                    tail = head
                    # beam_id must be > than the head to prevent referencing
                    # previous nodes with the same name

                    # exclude the intents of message actions (and anything else that we decided
                    # to ignore in the graph)
                    if node.name in self.graph_gen.beams[beam].parent_nodes_id_map:
                        head = (
                            self.graph_gen.beams[beam].parent_nodes_id_map[node.name].pop(0)
                        )
                        while int(head) <= int(tail):
                            head = (
                                self.graph_gen.beams[beam]
                                .parent_nodes_id_map[node.name]
                                .pop(0)
                            )
                        self.graph_gen.graph.edge(
                            tail,
                            head,
                            color="forestgreen",
                            penwidth="10.0",
                            arrowhead="normal",
                        )
                # collect the drop-off points in the final beams
                for i in range(1, len(self.beams[beam].rankings)):
                    if self._is_drop_off(beam, self.beams[beam].rankings[i].score, i - 1):
                        self.json_data[-1]["drop-off nodes"].append(f"{self.beams[beam].rankings[i-1].name} -> {self.beams[beam].rankings[i].name}")
            self.graph_gen.graph.render(os.path.join(self.graphs_path, *("graphs", os.path.splitext(os.path.basename(self.conversation_paths[idx]))[0])), cleanup=True)
            # move the "covered" conversation to the output folder (saves headaches when you need multiple runs)
            os.mkdir(os.path.join(self.graphs_path, "convos"))
            os.replace(self.conversation_paths[idx], os.path.join(self.graphs_path, *("convos", os.path.basename(self.conversation_paths[idx]))))
            # sort the beams by total score (largest first)
            self.beams.sort(reverse=True)
            # we consider the conversation to be handled if the best beam
            # total score is >= the log(epsilon) value and the goal was reached
            self.json_data[-1]["status"] = "passed" if (sum(self.beams[0].scores).real >= log(EPSILON).real and self.beams[beam].rollout.get_reached_goal()) else "failed"

        # store the # of successes and failures and the ratio
        successes = len([conv for conv in self.json_data if conv["status"] == "passed"])
        failures = len(self.conversations) - successes
        self.json_data = {"conversation data": self.json_data}
        self.json_data["results"] = {"successes": successes, "failures": failures, "total": len(self.conversations), "ratio": f"{(round(successes/len(self.conversations), 2) * 100)}% conversations passed."}
        # collect the drop-off nodes
        self.json_data["results"]["drop-off nodes"] = {}
        for conv in self.json_data["conversation data"]:
            for node in set(conv["drop-off nodes"]):
                self.json_data["results"]["drop-off nodes"][node] = conv["drop-off nodes"].count(node)
        with open(f"{self.graphs_path}/output_stats.json", "w") as out:
            out.write(json.dumps(self.json_data, indent=4))

    def plot(self):
        if self.json_data == []:
            raise ValueError("You need to run the beam search algorithm before plotting results!")
        # plot the ratio of successes to failures
        s, f, t = self.json_data["results"]["successes"], self.json_data["results"]["failures"], len(self.conversations)
        
        plt.figure(0)
        plt.title("Status of Conversations")
        plt.pie([s, f], labels = [f"{(round(s/t, 2)) * 100}% passed", f"{round(f/t, 2) * 100}% failed"], colors=["green", "red"], explode = [0.2, 0], shadow = True)

        plt.figure(1)
        plt.title("Drop-off nodes")
        nodes = self.json_data["results"]["drop-off nodes"]
        plt.pie(nodes.values(), labels = nodes.keys(), shadow = True)
        plt.show()
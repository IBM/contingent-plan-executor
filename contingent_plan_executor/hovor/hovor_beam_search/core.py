from cmath import log
from typing import List, Union
from hovor.hovor_beam_search.data_structs import *
from hovor.hovor_beam_search.init_stubs import *
from hovor.hovor_beam_search.graph_setup import BeamSearchGraph, NodeType
from hovor.configuration.json_configuration_postprocessing import (
    map_action_to_outcome_determiner,
)
import json
import matplotlib.pyplot as plt
import os
import shutil


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
        output_path (str): The path where the graphs and output stats will be stored.
        rollout_param (**kwargs): Any parameters necessary to instantiate your
            Rollout class.
    """

    def __init__(
        self,
        k: int,
        max_fallbacks: int,
        conversation_paths: str,
        output_path: str,
        **kwargs,
    ):
        self.k = k
        self.max_fallbacks = max_fallbacks
        self.conversations = ConversationAlignmentExecutor.preprocess_conversations(
            conversation_paths
        )
        self.conversation_paths = conversation_paths
        self.output_path = output_path
        self.rollout_param = kwargs
        # indicates if we are in the middle of aligning a conversation
        self._in_run = True
        try:
            json_path = os.path.join(self.output_path, "output_stats.json")
            with open(json_path, "r") as f:
                self.json_data = json.load(f)
        except FileNotFoundError:
            self.json_data = {"conversation data": []}


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

    @staticmethod
    def preprocess_conversations(conversation_paths: List[str]):
        """Preprocesses conversations generated from `local_main_simulated_many`
        for use within the algorithm.

        Args:
            conversation_paths (List[str]): Paths that store the conversations to be
                explored.

        Returns:
            (List[List[Dict[str, str]]]): Formatted conversation data.
        """
        conversations = [
            json.loads(open(out, "r").read()) for out in conversation_paths
        ]
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
    
    @staticmethod
    def plot(json_data_path, out_path):
        with open(json_data_path, "r") as f:
            json_data = json.load(f)
        if json_data == {"conversation data": []}:
            raise ValueError(
                "You need to run the beam search algorithm before plotting results!"
            )
        # plot the ratio of successes to failures
        tp, fp, tn, fn, t = (
            json_data["results"]["tp"],
            json_data["results"]["fp"],
            json_data["results"]["tn"],
            json_data["results"]["fn"],
            len(json_data["conversation data"]),
        )

        plt.figure(0, figsize=(20, 20))
        plt.title("Status of Conversations")
        plt.xlabel("Confusion Matrix Categories")
        plt.ylabel("Number of Conversations")
        bars = plt.bar(
            [
                f"{(round(tp/t, 2)) * 100}% TP (true alignments)",
                f"{round(fp/t, 2) * 100}% FP (false alignments)",
                f"{round(tn/t, 2) * 100}% TN (true misalignments)",
                f"{round(fn/t, 2) * 100}% FN (false misalignments)",
            ],
            [tp, fp, tn, fn],
        )
        bars[0].set_color("green")
        bars[1].set_color("darkseagreen")
        bars[2].set_color("red")
        bars[3].set_color("darksalmon")
        plt.savefig(os.path.join(out_path, "confusion_stats.pdf"))
        plt.clf()
        plt.figure(1, figsize=(60, 35))
        plt.title("Drop-off nodes")
        nodes = json_data["results"]["drop-off nodes"]
        plt.pie(nodes.values(), labels=nodes.keys(), shadow=True, textprops={'fontsize': 50})
        plt.savefig(os.path.join(out_path, "drop-off_nodes.pdf"))
        plt.clf()

    def _sum_scores(self, beam, confidence):
        # avoid math error when taking the log
        if confidence == 0:
            confidence = EPSILON
        return sum(self.beams[beam].scores) + log(confidence)

    @staticmethod
    def _set_conf(confidence):
        # avoid math error when taking the log
        if confidence == 0:
            confidence = EPSILON
        return confidence

    @staticmethod
    def _get_action_node_type(action):
        return NodeType.MESSAGE_ACTION if HovorRollout.is_message_action(action) else NodeType.DEFAULT_ACTION

    def _prep_for_new_search(self):
        """Resets the beams and graph generator to begin a new search."""
        self.beams = []
        self.graph_gen = BeamSearchGraph(self.k)

    def _get_last_head_from_action(self, beam):
        return (
            (self.beams[beam].last_action.name
            if HovorRollout.is_message_action(self.beams[beam].last_action.name)
            else self.beams[beam].rankings[-1].name)
            if isinstance(self.beams[beam].last_action, Action)
            else  self.beams[beam].rankings[-1].name
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
        return (node_score - self.beams[beam].rankings[prev_idx].score).real <= log(
            EPSILON
        ).real

    def _determine_node_type(
        self, beam: int, node_score: float, default_type: NodeType
    ):
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
        return (
            NodeType.DROP_OFF
            if self._is_drop_off(beam, node_score, -1)
            else default_type
        )
    
    def _handle_state_update_cases(self, beam: int):
        self._append_ending_node(beam, self.beams[beam].rollout.applicable_actions)
        if self.beams[beam].rollout.applicable_actions != "WARNING: The goal was reached, but there are still utterances left!":
            self._append_ending_node(beam, "finishing off...")

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
            # don't want to run for "ending" nodes
            if isinstance(self.beams[beam].last_action, Action):
                # if result is not None, then the last action was a message action
                result = self.beams[beam].rollout.update_if_message_action(
                    self.beams[beam].last_action.name, self._in_run
                )
                if result:
                    # create an intent from the message action.
                    intent = Intent(
                        name=result["intent"],
                        probability=ConversationAlignmentExecutor._set_conf(
                            result["confidence"]
                        ),
                        beam=beam,
                        score=self._sum_scores(beam, result["confidence"]),
                        outcome=result["outcome"],
                    )
                    # update the last intent and rankings and add it to the beam
                    self.beams[beam].last_intent = intent
                    self.beams[beam].rankings.append(intent)
                    self.beams[beam].scores.append(log(intent.probability))

                    # returned an error message
                    if type(self.beams[beam].rollout.applicable_actions) == str:
                        self._handle_state_update_cases(beam)

    def _handle_system_actions(self, beam: int):
        # before we begin, check if we have the valid case for
        # executing a system/api action (it is the only applicable
        # action) and iterate until this is no longer the case.
        # we also want to break if we reach the goal along the way!
        while (
            self.beams[beam].rollout.check_system_case()
            and not self.beams[beam].rollout.get_reached_goal()
        ):
            prev_app_acts = self.beams[beam].rollout.applicable_actions
            action = list(prev_app_acts)[0]
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
                score=self._sum_scores(beam, 1.0),
            )

            # get the intents from the ranked group (outcome, confidence) tuples
            # note that we use the outcome name for system/api actions as they have no intent (note that we use a shortened version)
            all_intents = [
                Intent(
                    name=group[0].name.split("-EQ-")[1],
                    probability=ConversationAlignmentExecutor._set_conf(group[1]),
                    beam=beam,
                    score=self._sum_scores(beam, group[1]),
                    outcome=group[0].name,
                )
                for group in ranked_groups
            ]

            all_intents.sort()

            self.beams[beam].rollout.update_state(
                action.name, all_intents[0].outcome, self._in_run
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
            self.beams[beam].scores.append(log(action.probability))
            # add "intent" (again, here we use the outcome name) nodes
            self.graph_gen.create_nodes_from_beams(
                {
                    intent.name: (
                        round(intent.score.real, 4),
                        self._determine_node_type(
                            beam, intent.score, NodeType.SYSTEM_API
                        ),
                    )
                    for intent in all_intents
                },
                beam,
                action.name,
                [all_intents[0].name],
            )

            self.beams[beam].last_intent = all_intents[0]
            self.beams[beam].rankings.append(all_intents[0])
            self.beams[beam].scores.append(log(all_intents[0].probability))
            
            # returned an error message
            if type(self.beams[beam].rollout.applicable_actions) == str:
                self._handle_state_update_cases(beam)
            # if the system action fails to "complete" itself (it is still applicable)
            # once it has executed and we have not reached the goal,
            # we will end up in an infinite loop!
            if self.beams[beam].rollout.applicable_actions == prev_app_acts:
                if not self.beams[beam].rollout.get_reached_goal():
                    return "The preceding system action failed to complete itself!"
                else:
                    return "We reached the goal through the preceding system action and there is nothing else to do now!"


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
        actions = not isinstance(outputs[0], Intent)
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
                    0
                )
            )
        # fallback values need to be recounted from the beginning because
        # of the restructuring (beams can also "lose" fallback values).
        for beam in new_beams:
            for ranking in beam.rankings:
                if isinstance(ranking, Intent):
                    if ranking.is_fallback():
                        beam.fallbacks += 1
        return new_beams
    
    def _append_ending_node(self, beam: int, node: str):
        self.graph_gen.create_nodes_from_beams(
            {
                node: (
                    round(self.beams[beam].rankings[-1].score.real, 4),
                    NodeType.GOAL,
                )
            },
            beam,
            self._get_last_head_from_action(beam),
            [node],
        )
        self.beams[beam].rankings.append(
            Output(
                node,
                1.0,
                beam,
                self.beams[beam].rankings[-1].score,
            )
        )
        self.beams[beam].scores.append(self.beams[beam].rankings[-1].score)
    
    def _wrap_up_convo(self):
        # we've reached the end of the conversation
        for beam in range(len(self.beams)):
            # run any straggling system actions (often this is needed to reach the goal).
            system_result = self._handle_system_actions(beam)
            # returned an error message
            if type(system_result) == "str":
                self._append_ending_node(beam, system_result)
                continue

            # add a "GOAL REACHED" node if necessary
            if self.beams[beam].rollout.get_reached_goal() and self.beams[beam].rankings[-1].name != "GOAL REACHED":
                self._append_ending_node(beam, "GOAL REACHED")


    def _highlight_final_beams(self):
        for beam in range(len(self.beams)):
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
                        self.graph_gen.beams[beam]
                        .parent_nodes_id_map[node.name]
                        .pop(0)
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

    def _collect_drop_off_nodes(self):
        for beam in range(len(self.beams)):
            # collect the drop-off points in the final beams
            for i in range(1, len(self.beams[beam].rankings)):
                if self._is_drop_off(
                    beam, self.beams[beam].rankings[i].score, i - 1
                ):
                    self.json_data["conversation data"][-1]["drop-off nodes"].append(
                        f"{self.beams[beam].rankings[i-1].name} -> {self.beams[beam].rankings[i].name}"
                    )

    def _generate_graph(self, idx: int):
        self.graph_gen.graph.render(
            os.path.join(
                self.output_path,
                *(
                    "graphs",
                    os.path.splitext(
                        os.path.basename(self.conversation_paths[idx])
                    )[0],
                ),
            ),
            cleanup=True,
        )

    def _store_single_convo_data(self, idx: int):
        self.json_data["conversation data"][-1]["name"] = self.conversation_paths[idx]
        # based on the pass/fail assessment and our knowledge of what is missing in the model, categorize the conversation on the confusion matrix.
        self.json_data["conversation data"][-1]["status"] = self._get_confusion_matrix()
        # we only care about drop-off nodes for failing conversations
        if self.json_data["conversation data"][-1]["status"] in ["tp", "fp"]:
            self.json_data["conversation data"][-1]["drop-off nodes"] = []
        with open(os.path.join(self.output_path, "output_stats.json"), "w") as out:
            out.write(json.dumps(self.json_data, indent=4))

    def _create_graph_store_convo(self, idx: int):
        self._wrap_up_convo()
        self._highlight_final_beams()
        self._collect_drop_off_nodes()
        self._generate_graph(idx)
        self._store_single_convo_data(idx)

    def _beam_search_single_conv(self, idx: int):
        # iterate through all utterances (the first was already observed)
        for utterance_idx in range(1, len(self.conversations[idx])):
            # denotes if this is a user utterance or an agent action
            utterance = self.conversations[idx][utterance_idx]
            self._generate_graph(idx)
            # we are "in run" as long as there are more utterances following
            # the current one
            self._in_run = utterance_idx < len(self.conversations[idx]) - 1
            user = "USER" in utterance
            outputs = []
            # iterate through all the beams
            for beam in range(len(self.beams)):
                if not isinstance(self.beams[beam].rankings[-1], Action) and not isinstance(self.beams[beam].rankings[-1], Intent):
                    continue
                # a message action or simple state update can result in the goal being added
                # if self.beams[beam].rollout.get_reached_goal():
                #     self._append_ending_node(beam, "GOAL REACHED")
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
                                probability=ConversationAlignmentExecutor._set_conf(
                                    intent_cfg["confidence"]
                                ),
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
                    # first handle system actions if we can. need to put this here
                    # because user intents should only be extracted directly after
                    # dialogue actions!
                    system_result = self._handle_system_actions(beam)
                    # returned error (or reached the goal)
                    if type(system_result) == str:
                        self._append_ending_node(beam, system_result)
                        if system_result == "We reached the goal through the preceding system action and there is nothing else to do now!":
                            outputs.append(            
                                Output(
                                    "GOAL REACHED",
                                    1.0,
                                    beam,
                                    self.beams[beam].rankings[-1].score,
                                )
                            )
                        self._append_ending_node(beam, "finishing off...")                        
                    # pruning can happen either from updating the state from
                    # within _handle_system_actions, or from a system action
                    # error!
                    if self.beams[beam].rankings[-1].name == "finishing off...":
                        continue
                    
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
                                probability=ConversationAlignmentExecutor._set_conf(
                                    conf
                                ),
                                beam=beam,
                                score=self._sum_scores(beam, conf),
                            )
                        )
            if not outputs:
                return
            # sort the outputs (k highest actions or intents) by score
            outputs.sort()
            # store all the outputs (only to use in graph creation) before
            # splicing the top k
            all_outputs = outputs
            outputs = outputs[0 : self.k]

            # for the graph: track which nodes are "chosen" for each beam
            graph_beam_chosen_map = {idx: [] for idx in range(len(self.beams))}
            for output in outputs:
                if user:
                    # tank the score if necessary (need to do this before adding nodes
                    # to the graph)
                    if output.is_fallback():
                        # we don't actually want to change the fallback value until
                        # we restructure the beams because of the case where multiple
                        # outputs stem from one beam (only one resulting beam would have
                        # the increase, not all).
                        if (
                            self.beams[output.beam].fallbacks + 1
                            == self.max_fallbacks
                        ):
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
                            output.name: (
                                round(output.score.real, 4),
                                NodeType.GOAL if not isinstance(output, Intent) and not isinstance(output, Action) else (
                                    self._determine_node_type(
                                        beam,
                                        output.score,
                                        NodeType.INTENT
                                        if user
                                        else (
                                            ConversationAlignmentExecutor._get_action_node_type(
                                                output.name
                                            )
                                        ),
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
                for beam in range(len(self.beams)):
                    self.beams[beam].rollout.update_state(
                        self.beams[beam].last_action.name, self.beams[beam].last_intent.outcome, self._in_run
                    )
                    # returned an error message
                    if type(self.beams[beam].rollout.applicable_actions) == str:
                        self._handle_state_update_cases(beam)
            else:
                self._handle_message_actions()


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
            - The algorithm will raise an exception if the system action fails to "complete"
              itself (that is, it runs infinitely because it is still applicable after it
              is executed!).

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
            print(idx)
            self.json_data["conversation data"].append(
                {
                    "conversation": self.conversations[idx],
                    "status": None,
                    "drop-off nodes": [],
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
                Action(
                    name=key,
                    probability=ConversationAlignmentExecutor._set_conf(val),
                    beam=index,
                    score=log(val),
                )
                for index, (key, val) in enumerate(starting_values.items())
            ]
            outputs.sort()

            if len(outputs) > self.k:
                starting = self.k
            else:
                starting = len(outputs)

            for beam in range(starting):
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
                    {
                        outputs[beam].name: (
                            round(outputs[beam].score.real, 4),
                            ConversationAlignmentExecutor._get_action_node_type(
                                outputs[beam].name
                            ),
                        )
                    },
                    beam,
                    "START",
                    [outputs[beam].name],
                )

            self._handle_message_actions()

            if len(outputs) > self.k:
                # add the (total actions - k) nodes that won't be picked to the graph
                for action in outputs[self.k :]:
                    self.graph_gen.create_nodes_outside_beams(
                        {
                            action.name: (
                                round(action.score.real, 4),
                                ConversationAlignmentExecutor._get_action_node_type(
                                    action.name
                                ),
                            )
                        },
                        "0",
                    )

            self._beam_search_single_conv(idx)

            self._create_graph_store_convo(idx)

        # store the confusion matrix
        self.json_data["results"] = {
            "tp": len([conv for conv in self.json_data["conversation data"] if conv["status"] == "tp"]),
            "fp": len([conv for conv in self.json_data["conversation data"] if conv["status"] == "fp"]),
            "tn": len([conv for conv in self.json_data["conversation data"] if conv["status"] == "tn"]),
            "fn": len([conv for conv in self.json_data["conversation data"] if conv["status"] == "fn"]),
            "total": len(self.json_data["conversation data"]),
        }
        # collect the drop-off nodes
        self.json_data["results"]["drop-off nodes"] = {node: 0 for conv in self.json_data["conversation data"] for node in conv["drop-off nodes"]}
        for conv in self.json_data["conversation data"]:
            for node in set(conv["drop-off nodes"]):
                self.json_data["results"]["drop-off nodes"][node] += conv[
                    "drop-off nodes"
                ].count(node)
        with open(os.path.join(self.output_path, "output_stats.json"), "w") as out:
            out.write(json.dumps(self.json_data, indent=4))

    def _get_confusion_matrix(self):
        # "positive" = conversation aligned (passed)
        # true positive = true alignment = conversation aligned and in at least one passing beam, there were no outcomes run that were meddled with.
        # false positive = false alignment = conversation aligned but should have misaligned because there are outcomes in ALL of the passing beams that were meddled with.
        # true negative = true misalignment = conversation misaligned and at least one meddled outcome was executed in any beam (one meddled outcome
        #   can result in an otherwise correct beam getting tanked, which then forces the exploration of "useless" branches)
        # false negative = false misalignment = conversation misaligned but should have aligned because none of the beams used outcomes that were meddled with
        partial = HovorRollout.rollout_cfg["partial"]
        beam_results = {
            beam: {"passing": False, "should misalign": False}
            for beam in range(len(self.beams))
        }
        # we consider the conversation to be handled if the best beam
        # total score is >= the log(epsilon) value and the goal was reached
        for beam in range(len(self.beams)):
            last_action = None
            if partial:
                for ranking in self.beams[beam].rankings:
                    if isinstance(ranking, Action):
                        last_action = ranking
                    # ignore "Output" goal node
                    elif isinstance(ranking, Intent):
                        if ranking.outcome in partial[last_action.name]:
                            beam_results[beam]["should misalign"] = True
                            break
            if (
                sum(self.beams[beam].scores).real >= log(EPSILON).real
                and self.beams[beam].rollout.get_reached_goal()
            ):
                beam_results[beam]["passing"] = True
        passing_beams = set([beam for beam, beam_cfg in beam_results.items() if beam_cfg["passing"]])
        failing_beams = set(beam_results.keys()).difference(passing_beams)
        if passing_beams:
            # determine true positive
            for beam in passing_beams:
                if not beam_results[beam]["should misalign"]:
                    return "tp"
            # determine false positive
            if [beam_results[beam]["should misalign"] for beam in passing_beams] == [
                True for _ in range(len(passing_beams))
            ]:
                return "fp"
        else:
            # determine true negative
            for beam in failing_beams:
                if beam_results[beam]["should misalign"]:
                    return "tn"
            # determine false negative
            if [beam_results[beam]["should misalign"] for beam in failing_beams] == [
                False for _ in range(len(failing_beams))
            ]:
                return "fn"



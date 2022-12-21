from cmath import log
from typing import List, Union, Dict
from hovor.hovor_beam_search.beam_srch_data_structs import *
from hovor.hovor_beam_search.init_stubs import *
from hovor.hovor_beam_search.graph_setup import BeamSearchGraphGenerator


class BeamSearchExecutor:
    def __init__(self, k: int, max_fallbacks: int, conversation: List[Dict[str, str]], build_graph: bool = True, graph_file: str = None, **kwargs):
        """Class that houses all information needed to execute the beam search
        algorithm.

        Args:
            k (int): The number of beams to use.
            max_fallbacks (int): The maximum number of fallbacks that can occur
                in any beam before the probability is tanked by resetting the 
                score to the log of a low number epsilon.
            conversation (List[Dict[str, str]]): The self.conversation to be 
                explored. Should be in the format
                    [
                        {"AGENT": "Hi!"},
                        {"USER": "Hello."}
                    ]
            build_graph (bool): Indicates if diagrams are to be compiled. 
                Defaults to True.
            graph_file (str): The file where the image will be 
                generated.
            **kwargs: Any parameters necessary to instantiate your 
                RolloutBase class.
        """
        self.k = k
        self.max_fallbacks = max_fallbacks
        self.conversation = conversation
        self.graph_file = graph_file
        self.build_graph = build_graph
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
            raise ValueError("The number of fallbacks needed to tank a beam must be a positive integer.")
        self._max_fallbacks = value   

    def prep_for_new_search(self):
        self.beams = []
        if self.build_graph:
            self.graph_gen = BeamSearchGraphGenerator(self.k)

    def _handle_message_actions(self):
        for i in range(len(self.beams)):
            result = self.beams[i].rollout.update_if_message_action(
                self.beams[i].last_action.name
            )
            if result:
                intent = Intent(
                    name=result["intent"],
                    probability=result["confidence"],
                    beam=i,
                    score=log(result["confidence"]) + self.beams[i].last_action.score,
                    outcome=result["outcome"]
                )
                self.beams[i].last_intent = intent
                self.beams[i].rankings.append(intent)
                if self.build_graph:
                    self.graph_gen.create_nodes_highlight_k(
                        {intent.name: round(intent.score.real, 4)},
                        "lightgoldenrod1",
                        self.beams[i].last_action.name,
                        i,
                        [intent.name],
                    )


    def _reconstruct_beam_w_output(self, outputs: List[Union[Action, Intent]]):
        new_beams = []
        for i in range(len(outputs)):
            # beam that the output came from
            at_beam = outputs[i].beam
            fallbacks = self.beams[at_beam].fallbacks
            if isinstance(outputs[i], Action):
                last_action = outputs[i]
                last_intent = self.beams[at_beam].last_intent
            else:
                last_intent = outputs[i]
                last_action = self.beams[at_beam].last_action
                if outputs[i].is_fallback():
                    fallbacks += 1
            new_beams.append(Beam(
                last_action,
                last_intent,
                self.beams[at_beam].rankings + [outputs[i]],
                self.beams[at_beam].rollout.copy(),
                self.beams[at_beam].scores + [log(outputs[i].probability)],
                fallbacks
            ))
        return new_beams


    def beam_search(self):
        self.prep_for_new_search()
        start_rollout = HovorRollout(**self.rollout_param)
        starting_values = start_rollout.get_action_confidences(self.conversation[0])
        outputs = [
            Action(name=key, probability=val, beam=index, score=log(val))
            for index, (key, val) in enumerate(starting_values.items())
        ]
        # if there are less starting actions than there are beams, duplicate the best action until we reach self.k
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
                    0
                )
            )
            if self.build_graph:
                # add the k actions to the graph
                self.graph_gen.create_nodes_highlight_k(
                    {outputs[beam].name: round(outputs[beam].score.real, 4)},
                    "skyblue",
                    "START",
                    beam,
                    [outputs[beam].name],
                )
        self._handle_message_actions()
        if self.build_graph:
            # add the (total actions - k) nodes that won't be picked to the graph
            self.graph_gen.create_from_parent(
                {action.name: round(action.score.real, 4) for action in outputs[self.k:]},
                "skyblue",
            )
        for utterance in self.conversation[1:]:
            user = "USER" in utterance
            outputs = []
            for beam in range(len(self.beams)):
                if user:
                    all_intent_confs = self.beams[beam].rollout.get_highest_intents(
                        self.beams[beam].last_action.name, utterance
                    )
                    for intent_cfg in all_intent_confs:
                        # find the score by taking the sum of the current beam thread which should be a list of log(prob)
                        outputs.append(
                            Intent(
                                name=intent_cfg["intent"],
                                probability=intent_cfg["confidence"],
                                beam=beam,
                                score=(
                                    sum(self.beams[beam].scores)
                                    + log(intent_cfg["confidence"])
                                ).real,
                                outcome=intent_cfg["outcome"],
                            )
                        )
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
                                score=(sum(self.beams[beam].scores) + log(conf)).real,
                            )
                        )
            # sort the new list keeping track of each thread instead of the outputs
            outputs.sort()
            all_outputs = outputs
            outputs = outputs[0:self.k]

            node_color = "lightgoldenrod1" if user else "skyblue"
            graph_beam_chosen_map = {idx: [] for idx in range(self.k)}
            for output in outputs:
                graph_beam_chosen_map[output.beam].append(output.name)

            if self.build_graph:
                for beam, chosen in graph_beam_chosen_map.items():
                    self.graph_gen.create_nodes_highlight_k(
                        # filter ALL outputs by outputs belonging to the current beam
                        # using the filtered outputs, map intents to probabilities to use in the graph
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
                self.graph_gen.beams = [
                    BeamSearchGraphGenerator.GraphBeam(
                        {
                            key: val
                            for key, val in self.graph_gen.beams[
                                output.beam
                            ].parent_nodes_id_map.items()
                        }
                    )
                    for output in outputs
                ]
            self.beams = self._reconstruct_beam_w_output(outputs)
            if user:
                for beam in self.beams:
                    beam.rollout.update_state(
                        beam.last_action.name,
                        beam.last_intent.outcome,
                    )
            else:
                self._handle_message_actions()

            for beam in self.beams:
                if beam.fallbacks >= self.max_fallbacks:
                    beam.scores = [log(0.00000001)]
        if self.build_graph:
            for i in range(len(self.beams)):
                if self.beams[i].rollout.get_reached_goal():
                    self.graph_gen.set_last_chosen(self.beams[i].rankings[-1].name, i)
                    self.graph_gen.complete_conversation(
                        round(self.beams[i].rankings[-1].score.real, 4)
                    )
                head = "0"
                for elem in self.beams[i].rankings:
                    tail = head
                    # beam_id must be > than the head to prevent referencing previous nodes with the same name
                    head = self.graph_gen.beams[i].parent_nodes_id_map[elem.name].pop(0)
                    while int(head) <= int(tail):
                        head = self.graph_gen.beams[i].parent_nodes_id_map[elem.name].pop(0)
                    self.graph_gen.graph.edge(
                        tail, head, color="forestgreen", penwidth="10.0", arrowhead="normal"
                    )
            self.graph_gen.graph.render(f"{self.graph_file}.gv", view=True)

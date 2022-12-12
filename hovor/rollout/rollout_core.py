from hovor.outcome_determiners.rasa_outcome_determiner import RasaOutcomeDeterminer
from hovor.rollout.semantic_similarity import softmax_confidences, semantic_similarity, normalize_confidences
from hovor.rollout.graph_setup import GraphGenerator
from hovor.rollout.rollout_stub import RolloutBase
from hovor.planning.outcome_groups.deterministic_outcome_group import DeterministicOutcomeGroup
from hovor.planning.outcome_groups.or_outcome_group import OrOutcomeGroup
from copy import deepcopy
from local_run_utils import create_validate_json_config_prov
import json
from environment import initialize_local_environment



class HovorRollout(RolloutBase):
    def __init__(self, output_files_path):
        initialize_local_environment()
        self._output_files_path = output_files_path
        self._configuration_provider = create_validate_json_config_prov(output_files_path)
        with open(f"{output_files_path}/rollout_config.json") as f:
            rollout_cfg = json.load(f)
        # convert conditions/effects to sets
        for act_cfg in rollout_cfg["actions"].values():
            act_cfg["condition"] = set(act_cfg["condition"])
            for out, out_vals in act_cfg["effect"].items():
                act_cfg["effect"][out] = set(out_vals)
        self._rollout_cfg = rollout_cfg
        self._current_state = set(self._rollout_cfg["initial_state"])
        self._applicable_actions = set()
        self._update_applicable_actions()

    def copy(self):
        new = HovorRollout(self._output_files_path)
        new._current_state = deepcopy(self._current_state)
        new._applicable_actions = deepcopy(self._applicable_actions)
        return new

    
    def get_reached_goal(self):
        return "(goal)" in self._current_state

    def get_highest_intents(self, action, utterance):
        data = self._configuration_provider._configuration_data
        rasa_outcome_determiner = RasaOutcomeDeterminer(
            action,
            data["actions"][action]["effect"]["outcomes"],
            data["context_variables"],
            data["intents"],
        )
        outcome_group_config = self._configuration_provider._create_outcome_group(
            action, data["actions"][action]["effect"]
        )
        if type(outcome_group_config) == DeterministicOutcomeGroup:
            outcome_groups = [outcome_group_config]
        elif type(outcome_group_config) == OrOutcomeGroup:
            outcome_groups = self._configuration_provider._create_outcome_group(
                action, data["actions"][action]["effect"]
            )._outcome_groups
        else:
            raise AssertionError(f"Cannot handle the outcome group of type {type(outcome_group_config)}")
        _, _, ranked_groups = rasa_outcome_determiner.get_final_rankings(
            utterance["USER"], outcome_groups
        )
        ranked_groups = sorted(ranked_groups, key=lambda item: item["confidence"], reverse=True)
        softmax_rankings = softmax_confidences({ranking["intent"] : ranking["confidence"] for ranking in ranked_groups})
        for ranking in ranked_groups:
            ranking["confidence"] = softmax_rankings[ranking["intent"]]
            ranking["outcome"] = ranking["outcome"].name
        return ranked_groups


    def _update_applicable_actions(self):
        # get all applicable actions, disqualifying non-dialogue actions
        applicable_actions = {act for act in self._rollout_cfg["actions"] if self._rollout_cfg["actions"][act]["condition"].issubset(self._current_state) and self._configuration_provider._configuration_data["actions"][act]["type"]
            in ["dialogue", "message"]}
        if len(applicable_actions) == 0:
            raise NotImplementedError(
                "No applicable actions found past this point. Note that api and system actions are not currently handled."
            )
        self._applicable_actions = applicable_actions

    def _update_state_fluents(self, new_fluents):
        for f in new_fluents:
            if f[:6] == "(not (" and f[-2:] == "))":
                raw_f = f.split("(not ")[1][:-1]
                if raw_f in self._current_state:
                    self._current_state.remove(raw_f)
                self._current_state.add(f)
            else:
                if f"(not {f})" in self._current_state:
                    self._current_state.remove(f"(not {f})")
                self._current_state.add(f)

    # given an outcome, update the state, then the applicable actions in the new state
    def update_state(self, 
        last_action,
        chosen_outcome
    ):
        self._update_state_fluents(
            self._rollout_cfg["actions"][last_action]["effect"][chosen_outcome],
        )
        self._update_applicable_actions()

    def get_action_confidences(self, source_sentence, prev_action = None, prev_intent = None, prev_outcome = None):
        self._check_for_message_updates(prev_action, prev_intent, prev_outcome)
        action_message_map = {act: self._configuration_provider._configuration_data["actions"][act]["message_variants"] for act in self._applicable_actions if self._configuration_provider._configuration_data["actions"][act]["message_variants"]}
        confidences = {}
        for action, messages in action_message_map.items():
            confidences[action] = semantic_similarity(source_sentence["HOVOR"], messages)
        return normalize_confidences({k: v for k, v in sorted(confidences.items(), key=lambda item: item[1], reverse=True)})


    def _check_for_message_updates(self, 
        prev_action = None,
        prev_intent = None,
        prev_outcome = None
    ):
        if prev_action and prev_intent and prev_outcome:
            data = self._configuration_provider._configuration_data
            # if a dialogue statement is possible, update the message variants according to the previous action
            if "dialogue_statement" in self._applicable_actions:
                if prev_intent == "fallback":
                    if "fallback_message_variants" in data["actions"][prev_action]:
                        data["actions"][
                            "dialogue_statement"
                        ]["message_variants"] = data["actions"][prev_action][
                            "fallback_message_variants"
                        ]
                else:
                    for outcome in data["actions"][prev_action]["effect"]["outcomes"]:
                        if outcome["name"] == prev_outcome:
                            data["actions"]["dialogue_statement"][
                                "message_variants"
                            ] = outcome["response_variants"]


    def update_if_message_action(self, most_conf_act):
        act_type = self._configuration_provider._configuration_data["actions"][most_conf_act]["type"]
        if act_type == "message":
            action_eff =  self._configuration_provider._configuration_data["actions"][most_conf_act]["effect"]
            self.update_state(
                most_conf_act,
                self._configuration_provider._create_outcome_group(
                    most_conf_act, action_eff
                ).name
            )
            return {"intent": action_eff["outcomes"][0]["intent"],
                    "outcome": action_eff["outcomes"][0]["name"],
                    "confidence": 1.0}


    # can use for partial conversation in a more elaborate version of beam search someday
    # NOTE: since it just takes the highest confidence at each step, the graph shows confidence, not cumulative score
    def rollout_conversation_greedy(self, conversation, build_graph: bool = False):
        most_conf_intent_out = {"intent": None, "outcome": None, "confidence": None}
        most_conf_act = None
        if build_graph:
           graph_gen = GraphGenerator()
        while len(conversation) > 0:
            utterance = conversation.pop(0)
            if "HOVOR" in utterance:
                all_acts = self.get_action_confidences(
                    utterance,
                    most_conf_act,
                    most_conf_intent_out["intent"],
                    most_conf_intent_out["outcome"]
                )
                # update if either when the conversation is not yet over, OR if there is only one last action
                if len(conversation) > 0 or len(all_acts) == 1:
                    most_conf_act = list(all_acts.keys())[0]
                    message_act = False
                    # doesn't need/take user input; state/applicable actions must be updated manually
                    intent_updated = self.update_if_message_action(most_conf_act)
                    if intent_updated:
                        most_conf_intent_out = intent_updated
                        message_act = True
                    if build_graph:
                        # add to the graph all the applicable actions, with the path to the chosen node highlighted
                        graph_gen.create_from_parent({act: round(conf, 4) for act, conf in all_acts.items()}, "skyblue", most_conf_act)
                        if message_act:
                            graph_gen.create_from_parent({most_conf_intent_out["intent"]: round(most_conf_intent_out["confidence"], 4)}, "lightgoldenrod1", most_conf_intent_out["intent"])
            else:
                all_intents = self.get_highest_intents(most_conf_act, utterance)
                # update if either when the conversation is not yet over, OR if there is only one last intent
                if len(conversation) > 0 or len(all_intents) == 1:
                    most_conf_intent_out = all_intents[0]
                    self.update_state(
                        most_conf_act,
                        most_conf_intent_out["outcome"],
                    )
                    if build_graph:
                        graph_gen.create_from_parent({intent["intent"]: round(intent["confidence"], 4) for intent in all_intents}, "lightgoldenrod1", most_conf_intent_out["intent"])
        final = most_conf_act if "HOVOR" in utterance and not message_act else most_conf_intent_out
        if build_graph:
            if self.get_reached_goal():
                graph_gen.complete_conversation(1.0)
            graph_gen.graph.render("rollout.gv", view=True)
        return final

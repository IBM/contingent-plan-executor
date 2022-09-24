from hovor.outcome_determiners.rasa_outcome_determiner import RasaOutcomeDeterminer
from hovor.rollout.semantic_similarity import softmax_confidences, semantic_similarity, normalize_confidences
from hovor.planning.outcome_groups.deterministic_outcome_group import DeterministicOutcomeGroup
from hovor.planning.outcome_groups.or_outcome_group import OrOutcomeGroup


class Rollout:
    def __init__(self, configuration_provider, rollout_cfg):
        self.configuration_provider = configuration_provider
        # convert conditions/effects to sets
        for act_cfg in rollout_cfg["actions"].values():
            act_cfg["condition"] = set(act_cfg["condition"])
            for out, out_vals in act_cfg["effect"].items():
                act_cfg["effect"][out] = set(out_vals)
        self.rollout_cfg = rollout_cfg
        self.current_state = set(self.rollout_cfg["initial_state"])
        self.applicable_actions = set()
        self.update_applicable_actions()

    def get_reached_goal(self):
        return "(goal)" in self.current_state

    def get_highest_intents(self, action, utterance):
        data = self.configuration_provider._configuration_data
        rasa_outcome_determiner = RasaOutcomeDeterminer(
            data["actions"][action]["effect"]["outcomes"],
            data["context_variables"],
            data["intents"],
        )
        outcome_group_config = self.configuration_provider._create_outcome_group(
            action, data["actions"][action]["effect"]
        )
        if type(outcome_group_config) == DeterministicOutcomeGroup:
            outcome_groups = [outcome_group_config]
        elif type(outcome_group_config) == OrOutcomeGroup:
            outcome_groups = self.configuration_provider._create_outcome_group(
                action, data["actions"][action]["effect"]
            )._outcome_groups
        else:
            raise AssertionError(f"Cannot handle the outcome group of type {type(outcome_group_config)}")
        chosen_intent, entities, ranked_groups = rasa_outcome_determiner.get_final_rankings(
            utterance["USER"], outcome_groups
        )
        ranked_groups = sorted(ranked_groups, key=lambda item: item["confidence"], reverse=True)
        softmax_rankings = softmax_confidences({ranking["intent"] : ranking["confidence"] for ranking in ranked_groups})
        for ranking in ranked_groups:
            ranking["confidence"] = softmax_rankings[ranking["intent"]]
            ranking["outcome"] = ranking["outcome"].name
        return ranked_groups


    def update_applicable_actions(self):
        # get all applicable actions, disqualifying non-dialogue actions
        applicable_actions = {act for act in self.rollout_cfg["actions"] if self.rollout_cfg["actions"][act]["condition"].issubset(self.current_state) and self.configuration_provider._configuration_data["actions"][act]["type"]
            in ["dialogue", "message"]}
        if len(applicable_actions) == 0:
            raise NotImplementedError(
                "No applicable actions found past this point. Note that api and system actions are not currently handled."
            )
        self.applicable_actions = applicable_actions

    def update_state(self, new_fluents):
        for f in new_fluents:
            if f[:6] == "(not (" and f[-2:] == "))":
                raw_f = f.split("(not ")[1][:-1]
                if raw_f in self.current_state:
                    self.current_state.remove(raw_f)
                self.current_state.add(f)
            else:
                if f"(not {f})" in self.current_state:
                    self.current_state.remove(f"(not {f})")
                self.current_state.add(f)

    def update_state_applicable_actions(self, 
        most_conf_act,
        outcome_group_name
    ):
        self.update_state(
            self.rollout_cfg["actions"][most_conf_act]["effect"][outcome_group_name],
        )
        self.update_applicable_actions()

    def get_action_confidences(self, source_sentence):
        action_message_map = {act: self.configuration_provider._configuration_data["actions"][act]["message_variants"] for act in self.applicable_actions if self.configuration_provider._configuration_data["actions"][act]["message_variants"]}
        confidences = {}
        for action, messages in action_message_map.items():
            confidences[action] = semantic_similarity(source_sentence, messages)
        return normalize_confidences({k: v for k, v in sorted(confidences.items(), key=lambda item: item[1], reverse=True)})


    def update_action_get_confidences(self, 
        utterance,
        prev_action=None,
        prev_intent=None,
        prev_outcome=None
    ):
        if prev_action and prev_intent and prev_outcome:
            data = self.configuration_provider._configuration_data
            # if a dialogue statement is possible, update the message variants according to the previous action
            if "dialogue_statement" in self.applicable_actions:
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

        return self.get_action_confidences(utterance["HOVOR"])

    def update_if_message_action(self, most_conf_act, most_conf_intent_out=None):
        if most_conf_intent_out:
            act_type = self.configuration_provider._configuration_data["actions"][most_conf_act]["type"]
            if act_type == "message":
                action_eff =  self.configuration_provider._configuration_data["actions"][most_conf_act]["effect"]
                self.update_state_applicable_actions(
                    most_conf_act,
                    self.configuration_provider._create_outcome_group(
                        most_conf_act, action_eff
                    ).name
                )
                return {"intent": action_eff["outcomes"][0]["intent"],
                        "outcome": action_eff["outcomes"][0]["name"],
                        "confidence": 1.0}
            else:
                return most_conf_intent_out

    def run_partial_conversation(self, conversation):
        most_conf_intent_out = {"intent": None, "outcome": None, "confidence": None}
        most_conf_act = None
        while len(conversation) > 0:
            utterance = conversation.pop(0)
            if "HOVOR" in utterance:
                most_conf_act = self.update_action_get_confidences(
                    utterance,
                    most_conf_act,
                    most_conf_intent_out["intent"],
                    most_conf_intent_out["outcome"]
                )
                # update if either when the conversation is not yet over, OR if there is only one last action
                if len(conversation) > 0 or len(most_conf_act) == 1:
                    most_conf_act = list(most_conf_act.keys())[0]
                    # doesn't need/take user input; state/applicable actions must be updated manually
                    most_conf_intent_out = self.update_if_message_action(most_conf_act, most_conf_intent_out)
            else:
                most_conf_intent_out = self.get_highest_intents(most_conf_act, utterance)
                # update if either when the conversation is not yet over, OR if there is only one last intent
                if len(conversation) > 0 or len(most_conf_intent_out) == 1:
                    most_conf_intent_out = most_conf_intent_out[0]
                    self.update_state_applicable_actions(
                        most_conf_act,
                        most_conf_intent_out["outcome"],
                    )
        return most_conf_act if "HOVOR" in utterance else most_conf_intent_out

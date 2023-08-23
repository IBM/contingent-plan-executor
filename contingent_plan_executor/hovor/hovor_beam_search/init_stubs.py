from hovor.outcome_determiners.rasa_outcome_determiner import NLUOutcomeDeterminer
from hovor.hovor_beam_search.semantic_similarity import (
    softmax_confidences,
    semantic_similarity,
    normalize_confidences,
)
from hovor.hovor_beam_search.data_structs import RolloutBase, Output
from hovor.outcome_determiners.outcome_determiner_base import OutcomeDeterminerBase
from hovor.planning.outcome_groups.or_outcome_group import OrOutcomeGroup
from hovor.planning.outcome_groups.deterministic_outcome_group import (
    DeterministicOutcomeGroup,
)
from hovor.core import initialize_session
from hovor.runtime.outcome_determination_progress import OutcomeDeterminationProgress
from hovor.runtime.action_result import ActionResult
from environment import initialize_local_environment
from local_run_utils import create_validate_json_config_prov
from typing import List
from copy import deepcopy
import json


class Intent(Output):
    """Describes an Intent.
    Args:
        outcome (str): The outcome chosen from the intent."""

    def __init__(
        self, name: str, probability: float, beam: int, score: float, outcome: str
    ):
        super().__init__(name, probability, beam, score)
        self.outcome = outcome

    def is_fallback(self) -> bool:
        """Determines if the provided intent is a fallback.

        Returns:
            bool: True if the intent is a fallback, False otherwise.
        """
        return self.name == "fallback"


class HovorRollout(RolloutBase):
    def __init__(self, output_files_path, progress=None):
        initialize_local_environment()
        HovorRollout._output_files_path = output_files_path
        HovorRollout.configuration_provider = create_validate_json_config_prov(
            output_files_path
        )
        HovorRollout.data = HovorRollout.configuration_provider._configuration_data
        with open(f"{output_files_path}/rollout_config.json") as f:
            rollout_cfg = json.load(f)
        # convert conditions/effects to sets
        for act_cfg in rollout_cfg["actions"].values():
            act_cfg["condition"] = set(act_cfg["condition"])
            for out, out_vals in act_cfg["effect"].items():
                act_cfg["effect"][out] = set(out_vals)
        HovorRollout.rollout_cfg = rollout_cfg
        self._current_state = set(HovorRollout.rollout_cfg["initial_state"])
        self.applicable_actions = set()
        self._update_applicable_actions(True)
        # note that we use the built-in notion of progress because for some outcome
        # determinations, the context and history is needed (context dependent
        # determination is one) and using the built-in progress was the easiest way.
        # the built-in progress comes with a lot of functions we don't need (ditto
        # for the configuration_provider), but we can just ignore these.
        if progress:
            self._progress = progress
        else:
            self._progress = OutcomeDeterminationProgress(
                initialize_session(HovorRollout.configuration_provider), ActionResult()
            )

    def copy(self):
        new = HovorRollout(HovorRollout._output_files_path, OutcomeDeterminationProgress(
                    initialize_session(HovorRollout.configuration_provider), ActionResult()
                )
            )
        new._progress.actual_context._fields = {f: v for f, v in self._progress.actual_context._fields.items()}
        new._progress._actual_determination_result._fields = {f: v for f, v in self._progress._actual_determination_result._fields.items()} if self._progress._actual_determination_result._fields else {}
        new._current_state = deepcopy(self._current_state)
        new.applicable_actions = deepcopy(self.applicable_actions)
        return new

    def get_reached_goal(self):
        return "(goal)" in self._current_state

    def check_system_case(self):
        if len(self.applicable_actions) == 1:
            action = list(self.applicable_actions)[0]
            if HovorRollout.data["actions"][action]["type"] in ["system", "api"]:
                return True
        return False

    def call_outcome_determiner(self, action: str, determiner: OutcomeDeterminerBase):
        # execute the action
        outcome_group_config = (
            HovorRollout.configuration_provider._create_outcome_group(
                action, HovorRollout.data["actions"][action]["effect"]
            )
        )
        if type(outcome_group_config) in [DeterministicOutcomeGroup, OrOutcomeGroup]:
            if type(outcome_group_config) == OrOutcomeGroup:
                outcome_group_config = outcome_group_config._outcome_groups
            # run the determiner and update the progress
            ranked_groups, self._progress = determiner.rank_groups(
                outcome_group_config, self._progress
            )
            return ranked_groups
        else:
            raise AssertionError(
                f"Cannot handle the outcome group of type {type(outcome_group_config)}"
            )

    def get_intent_confidences(self, action, utterance):
        data = HovorRollout.data
        # if we're dealing with a message action, we can just return
        # the single outcome immediately
        if data["actions"][action]["type"] == "message":
            out = data["actions"][action]["effect"]["outcomes"][0]
            return [{"intent": out["intent"], "outcome": out["name"], "confidence": 1}]
        # update the progress action input (aka user utterance) manually
        self._progress.json["action_result"]["fields"]["input"] = utterance["USER"]
        ranked_groups = self.call_outcome_determiner(
            action,
            NLUOutcomeDeterminer(
                action,
                data["actions"][action]["effect"]["outcomes"],
                data["context_variables"],
                data["intents"],
            ),
        )
        # reformat
        ranked_groups = [
            {"outcome": g[0], "confidence": g[1], "intent": out["intent_cfg"] if "intent_cfg" in out else out["intent"]}
            for g in ranked_groups
            for out in HovorRollout.data["actions"][action]["effect"]["outcomes"]
            if out["name"] == g[0].name
        ]
        ranked_groups = sorted(
            ranked_groups, key=lambda item: item["confidence"], reverse=True
        )
        softmax_confidences(ranked_groups)
        for ranking in ranked_groups:
            ranking["outcome"] = ranking["outcome"].name
        return ranked_groups

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

    def _update_applicable_actions(self, in_run: bool):
        # get all applicable actions, disqualifying non-dialogue actions
        applicable_actions = {
            act
            for act in HovorRollout.rollout_cfg["actions"]
            if HovorRollout.rollout_cfg["actions"][act]["condition"].issubset(
                self._current_state
            )
        }
        if in_run:
            if self.get_reached_goal():
                self.applicable_actions = "WARNING: The goal was reached, but there are still utterances left!"
            if len(applicable_actions) == 0:
                self.applicable_actions = "No applicable actions found past this point!"
                return
        # raise an error if there are multiple applicable system/api actions but no dialogue/message actions as it is ambiguous which should be executed.
        # otherwise, remove the system/api actions from the pool of applicable actions as they have no messages to compare against.
        if len(applicable_actions) > 1:
            applicable_actions = {
                act
                for act in applicable_actions
                if HovorRollout.data["actions"][act]["type"] in ["dialogue", "message"]
            }
            if len(applicable_actions) == 0:
                applicable_actions = """There were multiple applicable actions, but none of them were dialogue or message actions. 
                    We are currently not handling the ambiguous case of selecting which system or api action to 
                    execute when multiple are applicable and we are forced to choose. Please see the docstring 
                    under `beam_search` for more details."""
        self.applicable_actions = applicable_actions

    # given an outcome, update the state + applicable actions in the new state + progress/context
    def update_state(self, last_action, chosen_outcome, in_run: bool):
        self._update_state_fluents(
            HovorRollout.rollout_cfg["actions"][last_action]["effect"][chosen_outcome],
        )
        self._update_applicable_actions(in_run)
        outcome_group_config = (
            HovorRollout.configuration_provider._create_outcome_group(
                last_action, HovorRollout.data["actions"][last_action]["effect"]
            )
        )
        if type(outcome_group_config) == OrOutcomeGroup:
            outcome_group_config = outcome_group_config._outcome_groups
            for g in outcome_group_config:
                if g.name == chosen_outcome:
                    outcome_group_config = g
                    break

        self._progress, _ = outcome_group_config.update_progress(self._progress)

    def get_action_confidences(
        self, source_sentence, prev_action=None, prev_intent=None, prev_outcome=None
    ):
        self._check_for_message_updates(prev_action, prev_intent, prev_outcome)
        print(self.applicable_actions)
        action_message_map = {
            act: HovorRollout.data["actions"][act]["message_variants"]
            for act in self.applicable_actions
            if HovorRollout.data["actions"][act]["message_variants"]
        }
        confidences = {}
        for action, messages in action_message_map.items():
            confidences[action] = semantic_similarity(
                source_sentence["AGENT"], messages
            )
        return normalize_confidences(
            {
                k: v
                for k, v in sorted(
                    confidences.items(), key=lambda item: item[1], reverse=True
                )
            }
        )

    def _check_for_message_updates(
        self, prev_action=None, prev_intent=None, prev_outcome=None
    ):
        if prev_action and prev_intent and prev_outcome:
            data = HovorRollout.data
            # if a dialogue statement is possible, update the message variants according to the previous action
            if "dialogue_statement" in self.applicable_actions:
                if prev_intent == "fallback":
                    if "fallback_message_variants" in data["actions"][prev_action]:
                        data["actions"]["dialogue_statement"][
                            "message_variants"
                        ] = data["actions"][prev_action]["fallback_message_variants"]
                else:
                    for outcome in data["actions"][prev_action]["effect"]["outcomes"]:
                        if (
                            outcome["name"] == prev_outcome
                            and "response_variants" in outcome
                        ):
                            data["actions"]["dialogue_statement"][
                                "message_variants"
                            ] = outcome["response_variants"]
                            break

    @staticmethod
    def is_message_action(act):
        # skip over "ending" nodes
        return HovorRollout.data["actions"][act]["type"] == "message" if act in HovorRollout.data["actions"] else False

    def update_if_message_action(self, most_conf_act, in_run: bool):
        if self.is_message_action(most_conf_act):
            action_eff = HovorRollout.data["actions"][most_conf_act]["effect"]
            self.update_state(
                most_conf_act,
                HovorRollout.configuration_provider._create_outcome_group(
                    most_conf_act, action_eff
                ).name,
                in_run,
            )
            return {
                "intent": action_eff["outcomes"][0]["intent"],
                "outcome": action_eff["outcomes"][0]["name"],
                "confidence": 1.0,
            }

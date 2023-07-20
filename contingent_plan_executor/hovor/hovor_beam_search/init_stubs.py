from hovor.outcome_determiners.rasa_outcome_determiner import RasaOutcomeDeterminer
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
from copy import deepcopy
import json


def preprocess_conversations(conversations):
    """Preprocesses conversations generated from `local_main_simulated_many`
    for use within the algorithm.

    Args:
        conversations (Dict): The generated conversations, in JSON/Dict format.

    Returns:
        (List[List[Dict[str, str]]]): Formatted conversation data.
    """
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
        HovorRollout._rollout_cfg = rollout_cfg
        self._current_state = set(HovorRollout._rollout_cfg["initial_state"])
        self.applicable_actions = set()
        self._update_applicable_actions()
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
        new = HovorRollout(HovorRollout._output_files_path, self._progress)
        new._current_state = deepcopy(self._current_state)
        new.applicable_actions = deepcopy(self.applicable_actions)
        return new

    def get_reached_goal(self):
        return "(goal)" in self._current_state

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
            RasaOutcomeDeterminer(
                action,
                data["actions"][action]["effect"]["outcomes"],
                data["context_variables"],
                data["intents"],
            ),
        )
        # reformat
        ranked_groups = [
            {"outcome": g[0], "confidence": g[1], "intent": out["intent"]}
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

    def _update_applicable_actions(self):
        # get all applicable actions, disqualifying non-dialogue actions
        applicable_actions = {
            act
            for act in HovorRollout._rollout_cfg["actions"]
            if HovorRollout._rollout_cfg["actions"][act]["condition"].issubset(
                self._current_state
            )
        }
        if len(applicable_actions) == 0:
            raise ValueError("No applicable actions found past this point.")
        # raise an error if there are multiple applicable system/api actions but no dialogue/message actions as it is ambiguous which should be executed.
        # otherwise, remove the system/api actions from the pool of applicable actions as they have no messages to compare against.
        if len(applicable_actions) > 1:
            applicable_actions = {
                act
                for act in applicable_actions
                if HovorRollout.data["actions"][act]["type"] in ["dialogue", "message"]
            }
            if len(applicable_actions) == 0:
                raise NotImplementedError(
                    """There were multiple applicable actions, but none of them were dialogue or message actions. 
                    We are currently not handling the ambiguous case of selecting which system or api action to 
                    execute when multiple are applicable and we are forced to choose. Please see the docstring 
                    under `beam_search` for more details."""
                )
        self.applicable_actions = applicable_actions

    # given an outcome, update the state + applicable actions in the new state + progress/context
    def update_state(self, last_action, chosen_outcome):
        self._update_state_fluents(
            HovorRollout._rollout_cfg["actions"][last_action]["effect"][chosen_outcome],
        )
        self._update_applicable_actions()
        # TODO: use functions
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
                        if outcome["name"] == prev_outcome:
                            data["actions"]["dialogue_statement"][
                                "message_variants"
                            ] = outcome["response_variants"]
                            break

    def update_if_message_action(self, most_conf_act):
        act_type = HovorRollout.data["actions"][most_conf_act]["type"]
        if act_type == "message":
            action_eff = HovorRollout.data["actions"][most_conf_act]["effect"]
            self.update_state(
                most_conf_act,
                HovorRollout.configuration_provider._create_outcome_group(
                    most_conf_act, action_eff
                ).name,
            )
            return {
                "intent": action_eff["outcomes"][0]["intent"],
                "outcome": action_eff["outcomes"][0]["name"],
                "confidence": 1.0,
            }

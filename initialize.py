import json
from hovor.local_run_utils import initialize_local_run
from hovor.core import initialize_session
from hovor.execution_monitor import run_outcome_determination
from hovor.outcome_determiners.rasa_outcome_determiner import RasaOutcomeDeterminer
from hovor.rollout.semantic_similarity import softmax_confidences
from hovor.planning.outcome_groups.deterministic_outcome_group import DeterministicOutcomeGroup
from hovor.planning.outcome_groups.or_outcome_group import OrOutcomeGroup


def run(user_inputs):
    json_cfg = initialize_local_run("C:\\Users\\Rebecca\\Desktop\\plan4dial\\plan4dial\\local_data\\gold_standard_bot\\output_files", True)
    session = initialize_session(json_cfg)
    while session.current_action.action_type != "goal_achieved":
        cur_act = session.current_action
        if cur_act.action_type == "dialogue":
            if len(cur_act._hidden_outcome_group._outcome_groups) > 1:
                user_input =  user_inputs.pop(0)
                action_execution_result = {"input": user_input}
                intents_outcomes = get_highest_intents(json_cfg, cur_act.name, {"USER": user_input})
                extracted_out = intents_outcomes[0]["outcome"]
                # need to create outcome group here
                session.current_action._outcome_group = outcfg
                final_progress, confidence = run_outcome_determination(session, action_execution_result)
                print()

def get_highest_intents(configuration_provider, action, utterance):
    data = configuration_provider._configuration_data
    rasa_outcome_determiner = RasaOutcomeDeterminer(
        data["actions"][action]["effect"]["outcomes"],
        data["context_variables"],
        data["intents"],
    )
    outcome_group_config = configuration_provider._create_outcome_group(
        action, data["actions"][action]["effect"]
    )
    if type(outcome_group_config) == DeterministicOutcomeGroup:
        outcome_groups = [outcome_group_config]
    elif type(outcome_group_config) == OrOutcomeGroup:
        outcome_groups = configuration_provider._create_outcome_group(
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

run(["wfewefewfwe", "I have a high budget and I want a fun atmosphere"])
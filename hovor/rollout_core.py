from hovor.actions.rollout_action import RolloutAction
from hovor.outcome_determiners.rasa_outcome_determiner import RasaOutcomeDeterminer
import requests
import json

def get_applicable_actions(state, actions):
    return {act for act in actions if actions[act]["condition"].issubset(state)}

# def create_action(configuration_provider, action_name, state, context):
#     action_config = data["actions"][action_name]
#     builder = configuration_provider._create_action_builder(action_name, action_config)

#     return builder(state, context)

# def initialize_session(configuration_provider, initial_state):
#     session = InMemorySession(configuration_provider)
#     session._current_state = PartialState(initial_state)
#     session._current_context = Context()
#     initial_result = ActionResult()
#     initial_progress = OutcomeDeterminationProgress(session, initial_result)

#     for initial_effect in configuration_provider.create_initial_effects():
#         # initialization is done via context effects
#         initial_progress.run_effect(initial_effect)

#     if not initial_progress.is_valid():
#         raise AssertionError("Initialization failed.")

#     session.update_context_by(initial_progress)

#     return session

# def next_action(configuration_provider, session, action):
#     return RolloutAction(configuration_provider._configuration_data["actions"][action], session._current_state, session._current_context, configuration_provider._create_outcome_group(action, data["actions"][action]["effect"]))

def run_rollout(configuration_provider, rollout_cfg, conversation):
    data = configuration_provider._configuration_data
    print("RUNNING INTERACTION")
    print("-" * 20 + "\n")

    for act in data["actions"]:
        data["actions"][act]["name"] = act

    applicable_actions = set()
    for act_cfg in rollout_cfg["actions"].values():
        act_cfg["condition"] = set(act_cfg["condition"])
        for out, out_vals in act_cfg["effect"].items():
            act_cfg["effect"][out] = set(out_vals)
    applicable_actions = get_applicable_actions(set(rollout_cfg["initial_state"]), rollout_cfg["actions"])
    if len(applicable_actions) == 0:
        raise AssertionError("No valid initial state.")
    elif len(applicable_actions) > 1:
        raise AssertionError("Initial state is ambiguous.")
    else:
        initial_action = list(applicable_actions)[0]

    rasa_outcome_determiner = RasaOutcomeDeterminer(data["actions"][initial_action]["effect"]["outcomes"], data["context-variables"], data["intents"])
    outcome_groups = configuration_provider._create_outcome_group(initial_action, data["actions"][initial_action]["effect"])._outcome_groups
    chosen_intent, ranked_groups, entities = rasa_outcome_determiner.get_final_rankings(conversation[1]["USER"], outcome_groups)
    print()
#     session = initialize_session(configuration_provider, rollout_cfg["initial_state"])
#     session._current_action = next_action(configuration_provider, session, initial_action)
    
#     while True:
#         run_partial_convo(configuration_provider, session, conversation)
#         action = session._current_action
#         if action is None:
#             break

#         # external call simulation
#         last_execution_result = action.start_execution()
#         action.end_execution(last_execution_result)
#         if action.action_type == "goal_achieved":
#             break

#     print("\n" + "-" * 20)
#     print("INTERACTION END")

#     # session._current_action.execute(conversation[1]["USER"])
#     # initial_progress = OutcomeDeterminationProgress(session, {"input": conversation[1]["USER"]})
#     # final_progress, confidence = session._current_action.outcome_group.update_progress(initial_progress)

# def run_partial_convo(configuration_provider, session, conversation):
#     accumulated_messages = None
#     diagnostics = []
#     reached_goal = False

#     session._current_action.execute(conversation[1]["USER"])  # initial action execution
#     while not reached_goal:
#         ranked_groups, updated_progress = RasaOutcomeDeterminer.rank_groups(session._current_action.outcome_group._outcome_groups, session._delta_history[-1])

        # # incorporates state/context changes that happend after action execution
        # final_progress, confidence = run_outcome_determination(session, action_execution_result)

        # # Add the diagnostics required
        # diagnostics.append(compute_diagnostic(final_progress, session._current_action, action_execution_result))

        # # next we change state accordingly
        # action = progress_with_outcome(session, final_progress, rollout = True)
        # session._current_action = next_action(configuration_provider, session, )

        # # if the outcome is foreordained, execute locally and proceed to the next action
        # if action.is_deterministic() and action.action_type != "goal_achieved":
        #     reached_goal = False

        # if reached_goal:
        #     return accumulated_messages, diagnostics, final_progress.final_outcome_name, confidence
        # else:
        #     action_execution_result = action.execute()
        #     if action_execution_result.get_field('type') == 'message':
        #         if accumulated_messages is None:
        #             accumulated_messages = action_execution_result.get_field('msg')
        #         else:
        #             accumulated_messages = accumulated_messages + '\n' + action_execution_result.get_field('msg')
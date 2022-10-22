from hovor.local_run_utils import initialize_local_run
from hovor.core import initialize_session
from hovor.execution_monitor import run_outcome_determination, progress_with_outcome
from hovor.runtime.action_result import ActionResult


def run_conversation(output_files_path, user_inputs):
    json_cfg = initialize_local_run(output_files_path, True)
    session = initialize_session(json_cfg)
    cur_act = session.current_action
    while session.current_action.action_type != "goal_achieved":
        if cur_act.action_type == "dialogue":
            user_input =  user_inputs[cur_act.name].pop(0)
            action_execution_result = ActionResult()
            action_execution_result.start_action()
            action_execution_result.set_field("input", user_input)
            action_execution_result.end_action()
            session.current_action._outcome_group = cur_act._hidden_outcome_group
        # message actions are handled the same as system actions
        elif cur_act.action_type in ["message", "system"]:
            action_execution_result = cur_act.execute()
        final_progress, _ = run_outcome_determination(session, action_execution_result)
        cur_act = progress_with_outcome(session, final_progress)

    


if __name__ == "__main__":
    run_conversation("C:\\Users\\Rebecca\\Desktop\\plan4dial\\plan4dial\\local_data\\gold_standard_bot\\output_files", ["wfewefewfwe", "I have a high budget and I want a fun atmosphere", "yes", "I have a gluten-free allergy", "I want to Mexico", "yes", "I want to eat Italian", "no"])
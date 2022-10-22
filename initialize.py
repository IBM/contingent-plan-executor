from hovor.local_run_utils import initialize_local_run
from hovor.core import initialize_session
from hovor.execution_monitor import run_outcome_determination, progress_with_outcome
from hovor.runtime.action_result import ActionResult
import random


def run_conversation(output_files_path, user_inputs, achieve_goal: bool = False):
    json_cfg = initialize_local_run(output_files_path, True)
    session = initialize_session(json_cfg)
    cur_act = session.current_action
    while True:
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
        if achieve_goal:
            if session.current_action.action_type == "goal_achieved":
                return "goal reached successfully"
        else:
            if len(user_inputs) == 0:
                return "end of inputs reached successfully"


def call_random_run(output_files_path, all_inputs):
    next_inputs = {}
    save_inputs = {act: [v for v in variants] for act, variants in all_inputs.items()}
    # iterate through all inputs while there are more options we haven't yet tried
    while len([v for variants in all_inputs.values() for v in variants]) > 0:
        # for each action, pick one variant randomly from the available pool and remove it from the pool
        # if all variants have been selected, pick one randomly that you already used 
        for act, variants in all_inputs.items():
            if len(variants) > 0:
                next_var = random.choice(variants)
                all_inputs[act].remove(next_var)
            else:
                random.choice(save_inputs[act])
            next_inputs[act] = next_var
        assert run_conversation(output_files_path, all_inputs, False)


def test_local_bot(output_files_path):
    all_inputs = {
        "get-location": ["wfeklwfeewf", "I am located in Toronto"],
        "get-cuisine": ["xvcbsdmv", "I want to Mexico", "I want to eat dessert"],
        "get-have-allergy": ["wlefgjwlfe", "yes", "no"],
        "get-allergy": ["lwkfjwelw", "I have a dairy-free allergy"],
        "get-outing": [
            "fwljwefklwe",
            "I have a low budget",
            "I want an exciting atmosphere",
            "I want a hIgh-enERGii atmosphere",
            "I have a low budget and I want a fun atmosphere",
            "I have a low budget and I want a relaxin atmosphere",
        ]
    }
    call_random_run(output_files_path, all_inputs)
    


if __name__ == "__main__":
    test_local_bot("C:\\Users\\Rebecca\\Desktop\\plan4dial\\plan4dial\\local_data\\gold_standard_bot\\output_files")
    #run("C:\\Users\\Rebecca\\Desktop\\plan4dial\\plan4dial\\local_data\\gold_standard_bot\\output_files", ["wfewefewfwe", "I have a high budget and I want a fun atmosphere", "yes", "I have a gluten-free allergy", "I want to Mexico", "yes", "I want to eat Italian", "no"])
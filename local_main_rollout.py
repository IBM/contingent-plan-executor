from hovor.rollout.rollout_core import Rollout
from environment import initialize_local_environment
from hovor.local_run_utils import create_validate_json_config_prov, initialize_local_run
import json

initialize_local_environment()

def create_rollout(output_files_path):
    with open(f"{output_files_path}/rollout_config.json") as f:
        rollout_cfg = json.load(f)
    return Rollout(create_validate_json_config_prov(output_files_path), rollout_cfg)


if __name__ == "__main__":
    dirname = "C:\\Users\\Rebecca\\Desktop\\plan4dial\\plan4dial\\local_data\\rollout_no_system_gold_standard_bot\\output_files"
    initialize_local_run(dirname, False)
    rollout = create_rollout(dirname)
    print(rollout.run_partial_conversation(
            [
                {"HOVOR": "Hello I am a Pizza bot what toppings do you want?"}, 
                {"USER": "I want it to have pepperoni"}, 
                {"HOVOR":"Ok what size do you want?"},
                {"USER": "I want a large pizza."}, 
                {"HOVOR": "What side do you want with your order?"},
                {"USER": "I want to have fries on the side."}, 
                {"HOVOR":"What drink do you want with your order?"},
                {"USER": "I want to drink coke."}, 
                {"HOVOR":"What base do you want for your pizza?"},
                {"USER": "I want a pizza with a ranch base"}, 
                {"HOVOR":"Ordering a pizza of size large with ranch as a base and pepperoni as toppings, as well as a coke and fries."},
                {"USER": "Thanks!"}, 
            ],
        )
    )
    print(rollout.get_reached_goal())

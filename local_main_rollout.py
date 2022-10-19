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
    dirname = "C:\\Users\\Rebecca\\Desktop\\output_files"
    initialize_local_run(dirname, False)
    rollout = create_rollout(dirname)
    print(rollout.run_partial_conversation(
        [
            {"HOVOR": "What do you want to order?"},
            {"USER": "sfsdfds"},
            {"HOVOR": "I didn't get that."},
            {"HOVOR": "What do you want to order?"},
            {"USER": "I want a cheese pizza with a coke and fries"},
            {"HOVOR": "Goal reached."},
            {"HOVOR": "Order has been logged as`:` cheese pizza with a coke to drink and fries on the side."},
            {"HOVOR": "Have a nice day!"}
        ],
    ))
    print(rollout.get_reached_goal())

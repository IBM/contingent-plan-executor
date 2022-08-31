from time import sleep
from hovor.rollout.rollout_core import Rollout
from hovor.configuration.json_configuration_provider import JsonConfigurationProvider
from environment import initialize_local_environment
import subprocess
import requests
from requests.exceptions import ConnectionError
import json
from pathlib import Path

initialize_local_environment()

def run_local_rollout(output_files_path, domain):
    with open(f"{output_files_path}/{domain}/{domain}_rollout_config.json") as f:
    #with open ('C:\\Users\\Rebecca\\Desktop\\files for natalie\\rollout_bot_no_system_rollout_config.json') as f:
    #ith open ('C:\Users\Rebecca\Desktop\plan4dial\output_files\end_message_v2\end_message_v2_rollout_config.json') as f:
        rollout_cfg = json.load(f)

    configuration_provider = JsonConfigurationProvider(f"{output_files_path}/{domain}/{domain}")
    #configuration_provider = JsonConfigurationProvider('C:\\Users\\Rebecca\\Desktop\\files for natalie\\pizza')
    #configuration_provider = JsonConfigurationProvider('C:\Users\Rebecca\Desktop\plan4dial\output_files\end_message_v2\end_message_v2')
    configuration_provider.check_all_action_builders()

    subprocess.Popen(["rasa", "run", "--enable-api", "-m", f"{output_files_path}/{domain}/{domain}-model.tar.gz"])
    #subprocess.Popen(["rasa", "run", "--enable-api", "-m", 'C:\\Users\\Rebecca\\Desktop\\files for natalie\\rollout_bot_no_system-model.tar.gz'])
    #subprocess.Popen(["rasa", "run", "--enable-api", "-m", 'C:\\Users\\Rebecca\\Desktop\\files for natalie\\rollout_bot_no_system-model.tar.gz'])
    while True:
        try:
            requests.post("http://localhost:5005/model/parse", json={"text": ""})
        except ConnectionError:
            sleep(0.1)
        else:
            break
    
    rollout = Rollout(configuration_provider, rollout_cfg)

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

if __name__ == "__main__":
    #run_local_rollout(str((Path(__file__).parent.parent / "plan4dial/output_files").resolve()), "pizza")
    run_local_rollout("C:\\Users\\Rebecca\\Desktop\\plan4dial\\output_files\\", "end_message_v2")

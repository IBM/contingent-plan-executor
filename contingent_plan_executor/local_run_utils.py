from hovor.configuration.json_configuration_provider import JsonConfigurationProvider
from environment import initialize_local_environment, initialize_local_environment_simulated
from time import sleep
import requests
import subprocess
import jsonpickle
from pathlib import Path


def create_validate_json_config_prov(output_files_path):
    configuration_provider = JsonConfigurationProvider(str(Path(output_files_path) / "data"))
    # test on recoded provider
    json = jsonpickle.encode(configuration_provider)
    configuration_provider = jsonpickle.decode(json)
    configuration_provider.check_all_action_builders()
    return configuration_provider

def run_model_server(output_files_path):
    # check if the model is already running before proceeding
    try:
        requests.post("http://localhost:5006/model/parse", json={"text": ""})
    except requests.exceptions.ConnectionError:
        raise NotImplementedError("Replace with new NLU model.")
        # subprocess.Popen(f"rasa run --enable-api -m {output_files_path}/nlu_model.tar.gz -p 5006", shell=True)
        # while True:
        #     try:
        #         requests.post("http://localhost:5006/model/parse", json={"text": ""})
        #     except requests.exceptions.ConnectionError:
        #         sleep(0.1)
        #     else:
        #         break

def initialize_local_run(output_files_path, get_cfg: bool = True):
    initialize_local_environment()
    run_model_server(output_files_path)
    if get_cfg:
        return create_validate_json_config_prov(output_files_path)
    
def initialize_local_run_simulated(output_files_path, get_cfg: bool = True):
    initialize_local_environment_simulated()
    run_model_server(output_files_path)
    if get_cfg:
        return create_validate_json_config_prov(output_files_path)

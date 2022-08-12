from time import sleep
from environment import initialize_rollout_environment
from hovor.rollout_core import run_rollout
from hovor.configuration.json_configuration_provider import JsonConfigurationProvider
import subprocess
import requests
from requests.exceptions import ConnectionError
import os
import json


initialize_rollout_environment()

with open("local_data/pizza/pizza_rollout_config.json") as f:
    rollout_cfg = json.load(f)
configuration_provider = JsonConfigurationProvider("local_data/pizza/pizza")

subprocess.Popen("rasa run --enable-api -m local_data/pizza/pizza-model.tar.gz")
while True:
    try:
        requests.post('http://localhost:5005/model/parse', json={"text": ""})
    except ConnectionError:
        sleep(0.1)
    else:
        break
run_rollout(configuration_provider, rollout_cfg, [{"HOVOR": "What would you like to order?"}, {"USER": "I want a cheese pizza with a coke and fries"}])

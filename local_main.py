from time import sleep
import jsonpickle
from environment import initialize_local_environment
from hovor.configuration.json_configuration_provider import JsonConfigurationProvider
from hovor.core import run_interaction
import subprocess
import requests
from requests.exceptions import ConnectionError
import json


initialize_local_environment()

#configuration_provider = JsonConfigurationProvider("local_data/pizza/pizza")
configuration_provider = JsonConfigurationProvider("C:\\Users\\Rebecca\\Desktop\\plan4dial\\output_files\\tutorial_bot_simplified\\tutorial_bot_simplified")

# test on recoded provider
json = jsonpickle.encode(configuration_provider)
configuration_provider = jsonpickle.decode(json)
configuration_provider.check_all_action_builders()

subprocess.Popen(["rasa", "run", "--enable-api", "-m", "C:\\Users\\Rebecca\\Desktop\\plan4dial\\output_files\\tutorial_bot_simplified\\tutorial_bot_simplified-model.tar.gz"])

while True:
    try:
        requests.post('http://localhost:5005/model/parse', json={"text": ""})
    except ConnectionError:
        sleep(0.1)
    else:
        break
run_interaction(configuration_provider)

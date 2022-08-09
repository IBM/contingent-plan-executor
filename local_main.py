from time import sleep
import jsonpickle
from environment import initialize_local_environment
from hovor.configuration.json_configuration_provider import JsonConfigurationProvider
from hovor.core import run_interaction
import subprocess
import requests
from requests.exceptions import ConnectionError

import json

import requests

initialize_local_environment()

subprocess.Popen("rasa run --enable-api -m pizza/pizza-model.tar.gz")

configuration_provider = JsonConfigurationProvider("./pizza/pizza")

# configuration_provider = JsonConfigurationProvider("./local_data/gold_standard_data/gold")

# test on recoded provider
json = jsonpickle.encode(configuration_provider)
configuration_provider = jsonpickle.decode(json)
configuration_provider.check_all_action_builders()

while True:
    try:
        requests.post('http://localhost:5005/model/parse', json={"text": ""})
    except ConnectionError:
        sleep(0.1)
    else:
        break
run_interaction(configuration_provider)

import jsonpickle
import json

from environment import initialize_local_environment
from hovor.configuration.json_configuration_provider import JsonConfigurationProvider
from hovor.core import run_interaction

initialize_local_environment()

with open("policy.out") as f:
    plan_data = json.load(f)
plan_data = {"plan": plan_data}
with open("./pizza/pizza.prp.json", 'w') as f:
    json.dump(plan_data, f, indent=4)
configuration_provider = JsonConfigurationProvider("./pizza/pizza")

# configuration_provider = JsonConfigurationProvider("./local_data/gold_standard_data/gold")

# test on recoded provider
json = jsonpickle.encode(configuration_provider)
configuration_provider = jsonpickle.decode(json)
configuration_provider.check_all_action_builders()

run_interaction(configuration_provider)

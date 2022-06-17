import jsonpickle
import json
from rasa.model_training import train_nlu
from environment import initialize_local_environment
from hovor.configuration.json_configuration_provider import JsonConfigurationProvider
from hovor.core import run_interaction
import requests

initialize_local_environment()

# with open("./pizza/policy.out") as f:
#     plan_data = json.load(f)
# plan_data = {"plan": plan_data}
# with open("./pizza/pizza.prp.json", 'w') as f:
#     json.dump(plan_data, f, indent=4)
# train rasa nlu
# train_nlu(
#     config="./pizza/config.yml",
#     nlu_data="./pizza/nlu.yml",
#     output="./pizza",
#     fixed_model_name="pizza-model"
# )
payload = {'text':'hi how are you?'}
r = json.loads(requests.post('http://localhost:5005/model/parse', json=payload).text)
configuration_provider = JsonConfigurationProvider("./pizza/pizza")

# configuration_provider = JsonConfigurationProvider("./local_data/gold_standard_data/gold")

# test on recoded provider
json = jsonpickle.encode(configuration_provider)
configuration_provider = jsonpickle.decode(json)
configuration_provider.check_all_action_builders()

run_interaction(configuration_provider)

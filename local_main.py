import jsonpickle

from environment import initialize_local_environment
from hovor.configuration.json_configuration_provider import JsonConfigurationProvider
from hovor.core import run_interaction

initialize_local_environment()

configuration_provider = JsonConfigurationProvider("./local_data/gold_standard_data/gold")
# configuration_provider = JsonConfigurationProvider("./pizza")

# test on recoded provider
json = jsonpickle.encode(configuration_provider)
configuration_provider = jsonpickle.decode(json)
configuration_provider.check_all_action_builders()

run_interaction(configuration_provider)

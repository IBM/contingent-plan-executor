from hovor.configuration.json_configuration_provider import JsonConfigurationProvider


class DirectJsonConfigurationProvider(JsonConfigurationProvider):
    def __init__(self, pid, configuration_data, plan_data):
        self._run_initialization(pid, configuration_data, plan_data)

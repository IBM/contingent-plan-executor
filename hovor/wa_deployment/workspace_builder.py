from ibm_watson import AssistantV1
from ibm_cloud_sdk_core.authenticators import IAMAuthenticator

from hovor.configuration.configuration_provider_base import ConfigurationProviderBase
from hovor.planning import controller
from hovor.planning.partial_state import PartialState
from hovor.runtime.context import Context
from hovor.wa_deployment.workspace_configuration_writer import WorkspaceConfigurationWriter


class WorkspaceBuilder(object):
    def __init__(self, workspace_name, api_url, key, version='2019-02-28'):
        self._assistant = AssistantV1(
            authenticator=IAMAuthenticator(key),
            version=version,
        )
        self._assistant.set_service_url(api_url)
        self._workspace_name = workspace_name
        self._assistant.set_http_config({'timeout': 100})

    def deploy(self, configuration_provider: ConfigurationProviderBase, debug_logging=False):
        plan: controller.Plan = configuration_provider.plan
        if not isinstance(plan, controller.Plan):
            raise NotImplementedError("Only hovor.controller.Plan plans are supported.")

        # writer that will collect plan structure
        writer = WorkspaceConfigurationWriter(configuration_provider, debug_logging)

        for entity, type_alias in plan.domain["entities"].items():
            type = plan.domain["types"][type_alias]
            config = plan.domain["entity_configs"][entity]
            writer.write_entity(entity, type, config)

        initial_node = plan.get_initial_node()
        writer.write_initial_node(initial_node)

        # plan traversal
        traversal_queue = [initial_node]
        processed_nodes = {initial_node}
        while len(traversal_queue) > 0:
            current_node = traversal_queue.pop()
            children = plan.get_children(current_node)
            for child in children:
                if child in processed_nodes:
                    continue

                traversal_queue.append(child)
                processed_nodes.add(child)

            # todo invalid state and context may hurt some actions
            node_action = configuration_provider.create_action(current_node,
                                                               PartialState(fluents=[]), Context())

            # todo for now we will access outcome group from hidden fields
            outcome_group = node_action._hidden_outcome_group
            writer.write_execution_step(current_node, node_action, outcome_group)

        writer.deploy_to(self._assistant, name=self._workspace_name)

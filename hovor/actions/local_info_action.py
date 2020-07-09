from hovor.actions.action_base import ActionBase
from hovor import DEBUG


class LocalInfoAction(ActionBase):
    def __init__(self, *args):
        super(LocalInfoAction, self).__init__(*args)
        self.is_external = False

    def _start_execution_callback(self, action_result):
        DEBUG("\t action simulation: " + str(self.config))

    def _end_execution_callback(self, action_result, info):
        pass

    def write_to_workspace(self, workspace_node, workspace_writer):
        if workspace_writer.is_debug_logging_enabled:
            workspace_node["output"] = "action simulation: " + str(self.config)
        return workspace_node

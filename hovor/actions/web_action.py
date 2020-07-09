import requests
import json

from hovor.actions.action_base import ActionBase
from hovor import DEBUG


class WebAction(ActionBase):
    """Web (i.e., REST API) type of action."""

    def __init__(self, *args):
        super().__init__(*args)

        self.url = self.config["url"]
        self.post_payload = dict(self.config["default_payload"])

        for posted_context_variable in self.config["posted_context_variables"]:
            value = self.context.get_field(posted_context_variable)
            self.post_payload[posted_context_variable] = value

        self.is_external = False

    def _start_execution_callback(self, action_result):

        HEADERS = {"Content-Type": "application/json", "Accept": "application/json"}

        DEBUG(f"\t calling {self.url}")
        DEBUG(f"\t payload {self.post_payload}")
        r = requests.post(self.url, headers=HEADERS, json=self.post_payload)
        DEBUG(f"\t {r.status_code} {r.reason}")

        data = json.loads(r.text)
        for key, value in data.items():
            action_result.set_field(key, value)

    def _end_execution_callback(self, action_result, info):
        pass

    def write_to_workspace(self, workspace_node, workspace_writer):
        payload = dict(self.config["default_payload"])  # static values that can be hardcoded to the payload
        for posted_context_variable in self.config["posted_context_variables"]:
            # create runtime reads of the dynamic variables
            payload[posted_context_variable] = f"<? $entities.{posted_context_variable} ?>"

        if workspace_writer.is_debug_logging_enabled:
            workspace_node["output"] = "Web call " + self.url + " " + str(payload)
        action_parameters = dict(payload)

        # todo remove the cloud function proxy
        action_parameters.update({
            "url": self.url,
            "openwhisk_user": "",
            "openwhisk_password": ""
        })

        workspace_node["actions"].append(
            {
                "name": "",
                "type": "server",
                "parameters": action_parameters,
                "result_variable": "context.action_result"
            }
        )
        return workspace_node

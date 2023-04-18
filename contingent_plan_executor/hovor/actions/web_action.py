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


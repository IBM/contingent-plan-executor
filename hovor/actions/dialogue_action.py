import random

from hovor.actions.action_base import ActionBase
from hovor.actions.local_dialogue_action import LocalDialogueAction


class DialogueAction(ActionBase):
    """Dialogue action that expects a response"""

    def __init__(self, *args):
        super().__init__(*args)

        self.is_external = True
        self._utterance = "HOVOR: " + random.choice(self.config["message_variants"])
        self._utterance = LocalDialogueAction.replace_pattern_entities(self._utterance, self.context)

    def _start_execution_callback(self, action_result):
        action_result.set_field("type", "message")
        action_result.set_field("msg", self._utterance)

    def _end_execution_callback(self, action_result, info):
        action_result.set_field("input", info)

    def write_to_workspace(self, workspace_node, workspace_writer):
        message_variants = self.config["message_variants"]
        return LocalDialogueAction.write_message_variants_to_workspace_node(message_variants, workspace_node)


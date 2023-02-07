import random
import re

from hovor.actions.action_base import ActionBase


class LocalDialogueAction(ActionBase):
    """Dialogue type of action - useful for local debugging."""

    _apply_message_grouping = False

    def __init__(self, *args):
        super().__init__(*args)
        self.is_external = False
        self._utterance = "HOVOR: " + random.choice(self.config["message_variants"])
        self._utterance = LocalDialogueAction.replace_pattern_entities(self._utterance, self.context)

    def _start_execution_callback(self, action_result):
        if not LocalDialogueAction._apply_message_grouping:
            print()

        print(self._utterance)

    def _end_execution_callback(self, action_result, info):
        if self.action_type == "dialogue":
            LocalDialogueAction._apply_message_grouping = False
            user_input = input("USER: ")
            action_result.set_field("input", user_input)
        else:
            LocalDialogueAction._apply_message_grouping = True

    @classmethod
    def replace_pattern_entities(cls, pattern, context):

        entity_tags = LocalDialogueAction.get_pattern_entities(pattern)
        entity_tags = sorted(entity_tags, key=lambda e: len(e), reverse=True)

        # replace entity tags in the text
        current_pattern = pattern
        for entity_tag in entity_tags:
            value = context.get_field(entity_tag[1:])
            current_pattern = current_pattern.replace(entity_tag, str(value))

        return current_pattern

    @classmethod
    def get_pattern_entities(cls, pattern):
        result = []
        for groups in re.findall("([$]([^$?,. ]+|[.][^$?,. ])+)", pattern):
            result.append(groups[0])

        return result

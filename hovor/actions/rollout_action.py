from hovor.actions.local_dialogue_action import LocalDialogueAction


class RolloutAction(LocalDialogueAction):
    def __init__(self, *args):
        super().__init__(*args)

    def _end_execution_callback(self, action_result, user_input, info):
        if self.action_type == "dialogue":
            LocalDialogueAction._apply_message_grouping = False
            action_result.set_field("input", user_input)
        else:
            LocalDialogueAction._apply_message_grouping = True

    def end_execution(self, result, user_input, info=None):
        self._end_execution_callback(result, user_input, info)
        result.end_action()


    def execute(self, user_input):
        # Can only monolithicly execute this if it is not external
        if self.is_external and not self.is_deterministic():
            raise ValueError("Cannot perform a complete execution for monolithic action of type %s" % self.action_type)

        result = self.start_execution()
        self.end_execution(result, user_input)

        return result
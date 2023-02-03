from hovor.actions.action_base import ActionBase


class GoalAchievedAction(ActionBase):
    """Action taken when goal is achieved."""

    def __init__(self, *args):
        super().__init__(*args)
        self.is_external = True  # the action is external so it breaks the inter loop

    def start_execution(self):
        pass

    def end_execution(self, result, info=None):
        print("GOAL ACHIEVED")

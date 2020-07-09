from hovor.actions.action_base import ActionBase


class WaitForUserAction(ActionBase):
    """Initial action for monitor to start with."""

    def __init__(self):
        super().__init__(None, None, None)
        self.is_external = True

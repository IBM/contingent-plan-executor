class Outcome(object):
    """Representation of an action outcome

    """

    def __init__(self, new_state, new_context, delta):
        self.new_state = new_state
        self.new_context = new_context
        self.delta = delta

    def is_valid(self):
        """Determine whether the defined outcome is valid. E.g. has all required context fields present."""

        return self.new_state.is_context_valid(self.new_context)

    def __repr__(self):
        return "[Outcome] " + str(self.new_state) + " [Context] " + str(self.new_context)

from hovor.planning.outcome_groups.outcome_group_base import OutcomeGroupBase


class AndOutcomeGroup(OutcomeGroupBase):
    def __init__(self, name, outcome_groups):
        super().__init__(name)

        self._outcome_groups = list(outcome_groups)

    def update_progress(self, initial_progress):
        raise NotImplementedError("Determination for AndOutcomeGroup")

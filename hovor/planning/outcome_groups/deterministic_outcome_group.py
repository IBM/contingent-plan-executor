from hovor.runtime.outcome_determination_progress import OutcomeDeterminationProgress
from hovor.planning.outcome_groups.outcome_group_base import OutcomeGroupBase


class DeterministicOutcomeGroup(OutcomeGroupBase):
    def __init__(self, name, entity_requirements):
        super().__init__(name)

        self._entity_requirements = list(entity_requirements)

    @property
    def entity_requirements(self):
        return list(self._entity_requirements)

    @property
    def required_present_entities(self):
        return set(e.entity for e in self._entity_requirements if e.must_have or e.maybe_have)

    @property
    def required_missing_entities(self):
        return set(e.entity for e in self._entity_requirements if e.dont_have)

    def update_progress(self, initial_progress: OutcomeDeterminationProgress):
        # todo this requires correct config semantic
        """
        for entity in self.required_present_entities:
            # check whether all required entities are present
            if not initial_progress.action_result.has_field(entity):
                initial_progress.invalidate()
                return initial_progress

        """

        initial_progress.remove_entities(self.required_missing_entities)
        initial_progress.apply_effect(self.name)
        initial_progress.finalize(self.name)
        return initial_progress, 1

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

    def write_to_workspace(self, workspace_node, workspace_writer):

        outcome_determination_info = workspace_writer.get_outcome_determination_info(self.name)
        group_node = workspace_writer.write_new_node(self.name + "-eff", parent=workspace_node)

        for effect in outcome_determination_info.context_effects:
            effect.write_to_workspace_node(group_node)

        target_node = None
        for name, child in workspace_writer.current_plan_node.named_children:
            if name == self.name:
                target_node = child

        if target_node is None:
            raise AssertionError("Cannot find child node.")

        if workspace_writer.has_parent(target_node):
            workspace_writer.write_jump(group_node, target_node)
        else:
            workspace_writer.write_direct_child(group_node, target_node)

from hovor.outcome_determiners.outcome_determiner_base import OutcomeDeterminerBase
from hovor.outcome_determiners.spel_evaluator import SpelEvaluator
from hovor.runtime.fields_container import FieldsContainer
from hovor.wa_deployment.workspace_configuration_writer import WorkspaceConfigurationWriter


class LogicOutcomeDeterminer(OutcomeDeterminerBase):
    def rank_groups(self, outcome_groups, progress):
        ranked_groups = []

        fields = FieldsContainer(progress.actual_context, progress.action_result)
        for group in outcome_groups:
            outcome_description = progress.get_description(group.name)
            condition = outcome_description["logic_condition"]
            evaluated_condition = SpelEvaluator.evaluate(condition, context=fields.dump())
            confidence = 1.0 if evaluated_condition else 0.0

            ranked_groups.append((group, confidence))

        return ranked_groups, progress

    def write_to_workspace(self, parent_group, workspace_node, outcome_groups,
                           workspace_writer: WorkspaceConfigurationWriter):

        group_node = workspace_writer.write_new_node(parent_group.name, parent=workspace_node)
        for group_id, group in enumerate(outcome_groups):
            condition_node = workspace_writer.write_new_node(group.name, parent=group_node)
            info = workspace_writer.get_outcome_determination_info(group.name).description
            condition_node["condition"] = workspace_writer.chroot(info["logic_condition"], "entities")
            group.write_to_workspace(condition_node, workspace_writer)

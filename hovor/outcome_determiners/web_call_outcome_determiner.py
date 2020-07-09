from hovor.outcome_determiners.outcome_determiner_base import OutcomeDeterminerBase
from hovor.outcome_determiners.random_outcome_determiner import RandomOutcomeDeterminer


class WebCallOutcomeDeterminer(OutcomeDeterminerBase):
    def rank_groups(self, outcome_groups, determination_progress):
        progress = determination_progress.create_child()

        # report values that were discovered by the action
        for field_name in determination_progress.action_result.field_names:
            value = determination_progress.action_result.get_field(field_name)
            progress.add_detected_entity(field_name, value)

        outcome_chosen = progress.action_result.get_field("outcome_chosen")
        ranked_groups = []
        for group in outcome_groups:
            description = progress.get_description(group.name)
            confidence = 1.0 if str(description["outcome_index"]) == str(outcome_chosen) else 0.0

            ranked_groups.append((group, confidence))

        return ranked_groups, progress

    def write_to_workspace(self, parent_group, workspace_node, outcome_groups, workspace_writer):
        group_node = workspace_writer.write_new_node(parent_group.name, parent=workspace_node)
        for group in outcome_groups:
            condition_node = workspace_writer.write_new_node(group.name, parent=group_node)
            group_description = workspace_writer.get_outcome_determination_info(group.name).description
            outcome_index = group_description["outcome_index"]

            condition_node["condition"] = f"$action_result.outcome_chosen == \"{outcome_index}\""
            group.write_to_workspace(condition_node, workspace_writer)

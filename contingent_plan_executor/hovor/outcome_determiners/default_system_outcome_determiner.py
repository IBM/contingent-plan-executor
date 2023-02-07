from hovor.outcome_determiners.outcome_determiner_base import OutcomeDeterminerBase


class DefaultSystemOutcomeDeterminer(OutcomeDeterminerBase):
    def rank_groups(self, outcome_groups, progress):
        ranked_groups = []

        for group in outcome_groups:
            outcome_description = progress.get_description(group.name)
            for update_var, update_config in outcome_description["updates"].items():
                if "value" in update_config:
                    if progress.get_entity_type(update_var) == "enum":
                        progress.add_detected_entity(update_var, update_config["value"])
            ranked_groups.append((group, 1.0/len(outcome_groups)))
        return ranked_groups, progress
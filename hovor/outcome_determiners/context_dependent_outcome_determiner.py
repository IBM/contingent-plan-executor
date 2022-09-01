from hovor.outcome_determiners.outcome_determiner_base import OutcomeDeterminerBase


class ContextDependentOutcomeDeterminer(OutcomeDeterminerBase):
    def rank_groups(self, outcome_groups, progress):
        ranked_groups = []
        for group in outcome_groups:
            outcome_description = progress.get_description(group.name)
            entity_requirements = group.entity_requirements
            conditions = outcome_description["context"]
            evaluated_condition = True
            for ctx_var, ctx_var_cfg in conditions.items():
                if "value" in ctx_var_cfg:
                    if progress.actual_context._fields[ctx_var] != ctx_var_cfg["value"]:
                        evaluated_condition = False
                        break
                elif "known" in ctx_var_cfg:
                    pass
            confidence = 1.0 if evaluated_condition else 0.0
            ranked_groups.append((group, confidence))
        return ranked_groups, progress
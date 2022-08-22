from hovor.outcome_determiners.outcome_determiner_base import OutcomeDeterminerBase


class ContextDependentOutcomeDeterminer(OutcomeDeterminerBase):
    def rank_groups(self, outcome_groups, progress):
        ranked_groups = []

        for group in outcome_groups:
            outcome_description = progress.get_description(group.name)
            conditions = outcome_description["context"]
            evaluated_condition = True
            for ctx_var, val in conditions.items():
                if progress.actual_context._fields[ctx_var] != val:
                    evaluated_condition = False
                    break
            confidence = 1.0 if evaluated_condition else 0.0
            ranked_groups.append((group, confidence))
        return ranked_groups, progress
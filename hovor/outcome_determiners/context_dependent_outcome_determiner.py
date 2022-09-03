from hovor.outcome_determiners.outcome_determiner_base import OutcomeDeterminerBase


class ContextDependentOutcomeDeterminer(OutcomeDeterminerBase):
    def __init__(self, context_variables):
        self.context_variables = context_variables

# TODO: FIX
    def check_known_status(self, ctx_var, known, current_state):
        is_fflag = self.context_variables[ctx_var]["known"]["type"] == "fflag"
        if known == True:
            return (f"NegatedAtom have_{ctx_var}()" not in current_state and f"Atom maybe-have_{ctx_var}()" not in current_state) if is_fflag else (f"NegatedAtom have_{ctx_var}()" not in current_state)
        elif known == False:
            return (f"Atom have_{ctx_var}()" not in current_state and f"Atom maybe-have_{ctx_var}()" not in current_state) if is_fflag else (f"Atom have_{ctx_var}()" not in current_state)
        elif known == "maybe":
            return (f"Atom maybe-have_{ctx_var}()" not in current_state or f"NegatedAtom have_{ctx_var}()" not in current_state)

    def rank_groups(self, outcome_groups, progress):
        ranked_groups = []
        for group in outcome_groups:
            outcome_description = progress.get_description(group.name)
            conditions = outcome_description["context"]
            evaluated_condition = True
            for ctx_var, ctx_var_cfg in conditions.items():
                if "value" in ctx_var_cfg:
                    if progress.actual_context._fields[ctx_var] != ctx_var_cfg["value"]:
                        evaluated_condition = False
                        break
                if "known" in ctx_var_cfg:
                    positive = progress.actual_state.get_positive_fluents()
                    evaluated_condition = self.check_known_status(ctx_var, ctx_var_cfg["known"], progress.actual_state.fluents)
                    if not evaluated_condition:
                        break                
            confidence = 1.0 if evaluated_condition else 0.0
            if confidence == 1.0:
                for update_var, update_config in outcome_description["updates"].items():
                    if "value" in update_config:
                        if progress.get_entity_type(update_var) == "enum":
                            progress.add_detected_entity(update_var, update_config["value"])
            ranked_groups.append((group, confidence))
        return ranked_groups, progress
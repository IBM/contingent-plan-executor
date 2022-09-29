from hovor.outcome_determiners.outcome_determiner_base import OutcomeDeterminerBase


class ContextDependentOutcomeDeterminer(OutcomeDeterminerBase):
    def __init__(self, context_variables):
        self.context_variables = context_variables

    @staticmethod
    def known_to_certainty(known):
        return ("Known" if known else "Unknown") if type(known) == bool else "Uncertain"

    def rank_groups(self, outcome_groups, progress):
        ranked_groups = []
        for group in outcome_groups:
            outcome_description = progress.get_description(group.name)
            conditions = outcome_description["context"]
            evaluated_condition = True
            for ctx_var, ctx_var_cfg in conditions.items():
                if "value" in ctx_var_cfg:
                    # break + indicate failure if the condition fails
                    if not progress.actual_context._fields[ctx_var] == ctx_var_cfg["value"]:
                        evaluated_condition = False
                        break
                if "known" in ctx_var_cfg:
                    # iterate through the outcomes executed so far
                    # the last "certainty" setting will indicate the current certainty of the variable
                    certainty = None
                    for outcome in progress._session.delta_history:
                        if outcome._edge:
                            if ctx_var in outcome._edge.info["updates"]:
                                if "certainty" in outcome._edge.info["updates"][ctx_var]:
                                    certainty = outcome._edge.info["updates"][ctx_var]["certainty"]
                    # break + indicate failure if the condition fails
                    if not certainty == ContextDependentOutcomeDeterminer.known_to_certainty(ctx_var_cfg["known"]):
                        evaluated_condition = False
                        break   
            confidence = 1.0 if evaluated_condition else 0.0
            if confidence == 1.0:
                for update_var, update_config in outcome_description["updates"].items():
                    if "value" in update_config:
                        if progress.get_entity_type(update_var) == "enum":
                            progress.add_detected_entity(update_var, update_config["value"])
            ranked_groups.append((group, confidence))
        return ranked_groups, progress
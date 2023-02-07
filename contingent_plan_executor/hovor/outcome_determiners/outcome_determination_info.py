class OutcomeDeterminationInfo(object):
    def __init__(self, description=None, outcome_determiner=None, context_effects=[]):
        self.description = description
        self.outcome_determiner = outcome_determiner
        self.context_effects = list(context_effects)

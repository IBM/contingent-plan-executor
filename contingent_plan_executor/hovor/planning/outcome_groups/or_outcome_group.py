from hovor.runtime.outcome_determination_progress import OutcomeDeterminationProgress
from hovor.planning.outcome_groups.outcome_group_base import OutcomeGroupBase
from hovor import DEBUG


class OrOutcomeGroup(OutcomeGroupBase):
    def __init__(self, name, outcome_groups):
        super().__init__(name)

        self._outcome_groups = list(outcome_groups)

    def update_progress(self, initial_progress: OutcomeDeterminationProgress):
        # run the determiner and update progress accordingly
        determiner = initial_progress.get_determiner(self.name)
        ranked_groups, updated_progress = determiner.rank_groups(self._outcome_groups, initial_progress)

        # every group can have some effect defined (e.g. assign determination result to context)
        updated_progress.apply_effect(self.name)

        # find valid group with top confidence
        for group, confidence in sorted(ranked_groups, key=lambda r: -r[1]):
            final_progress, conf = group.update_progress(updated_progress.create_child())
            if final_progress is None or not final_progress.is_valid():
                continue

            #DEBUG("\t OR group '%s' chooses child '%s' with confidence '%.2f'" % (self.name, group.name, confidence))
            return final_progress, confidence

        raise AssertionError("No outcome group has valid outcome.")

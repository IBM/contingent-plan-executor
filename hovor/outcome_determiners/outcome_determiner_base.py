from hovor.planning.outcome_groups.deterministic_outcome_group import DeterministicOutcomeGroup
from hovor.planning.outcome_groups.or_outcome_group import OrOutcomeGroup


class OutcomeDeterminerBase(object):
    def rank_groups(self, outcome_groups, determination_progress):
        """

        Ranks outcome groups according to the current determination progress.
        The execution and determination results can be found in the progress.

        :param outcome_groups: Outcome groups to be ranked.
        :param determination_progress: The available determination progress.
        :return: enumeration of tuples (outcome group, score), updated_determination_progress
        """
        raise NotImplementedError("must be overriden")

    @classmethod
    def find_required_present_entities(cls, outcome_groups):
        collected_entities = set()
        outcomes = cls._find_deterministic_groups(outcome_groups)
        for outcome in outcomes:
            collected_entities.update(outcome.required_present_entities)

        return collected_entities

    @classmethod
    def _find_deterministic_groups(cls, groups):
        result = []
        for group in groups:
            if isinstance(group, DeterministicOutcomeGroup):
                result.append(group)
            elif isinstance(group, OrOutcomeGroup):
                result.extend(cls._find_deterministic_groups(group._outcome_groups))
            else:
                raise NotImplementedError("Outcome listing for group %s is not implemented yet." % group)

        return result

    def write_to_workspace(self, parent_group, workspace_node, outcome_groups, workspace_writer):
        raise NotImplementedError("OutcomeDeterminer implemented by " + str(
            type(self)) + " does not support workspace deployment yet.")

import collections
import datetime
import random

from hovor.outcome_determiners.outcome_determiner_base import OutcomeDeterminerBase
from hovor.planning.outcome_groups.deterministic_outcome_group import DeterministicOutcomeGroup
from hovor.planning.outcome_groups.or_outcome_group import OrOutcomeGroup
from hovor import DEBUG
from hovor.wa_deployment.workspace_configuration_writer import WorkspaceConfigurationWriter


class RandomOutcomeDeterminer(OutcomeDeterminerBase):
    """Determiner"""

    random_samples = {
        "sys-location": ["New York", "Prague", "Boston", "Yorktown", "Paris", "Melbourne"],
    }

    def rank_groups(self, outcome_groups, progress):
        top_group = None
        top_rank = float("-inf")
        ranked_groups = []
        for outcome_group in outcome_groups:
            rank = random.uniform(0.0, 1.0)
            ranked_groups.append((outcome_group, rank))

            if rank > top_rank:
                top_rank = rank
                top_group = outcome_group

        DEBUG("\t top random ranking for group '%s'" % (top_group.name,))

        self._report_sampled_entities(outcome_groups, progress)
        return ranked_groups, progress

    @classmethod
    def _make_entity_sample(cls, entity, progress):
        entity_type = progress.get_entity_type(entity)
        entity_config = progress.get_entity_config(entity)
        return cls._make_entity_type_sample(entity_type, entity_config)

    @classmethod
    def _make_entity_type_sample(cls, entity_type, entity_config):
        if entity_type == "location" or entity_type == "sys-location":
            return random.choice(RandomOutcomeDeterminer.random_samples["sys-location"])

        if entity_type == "travel_dates" or entity_type == "sys-date_range":
            format = "%Y-%m-%d"
            start = cls._sample_date(datetime.datetime.now().date())
            end = cls._sample_date(start)
            return (start.strftime(format), end.strftime(format))
        elif entity_type == "json":
            # todo what can we do here?
            return {}
        elif entity_type == "enum":
            return random.choice(entity_config)
        elif entity_type == "sys-currency":
            return random.choice(["1$", "10$", "100 USD", "500 CZK"])
        else:
            raise NotImplementedError("Cant sample from type: " + entity_type)

    @classmethod
    def _sample_date(cls, mindate):
        daycount = random.choice([0, 1, 7, 14, 31])
        return mindate + datetime.timedelta(days=daycount)

    def _report_sampled_entities(self, outcome_groups, progress):
        collected_entities = self.find_required_present_entities(outcome_groups)

        # add the entities like they were really detected during the determination
        for entity in collected_entities:
            entity_sample = RandomOutcomeDeterminer._make_entity_sample(entity, progress)
            progress.add_detected_entity(entity, entity_sample)

    def write_to_workspace(self, parent_group, workspace_node, outcome_groups, workspace_writer):
        self.write_random_selection_to_workspace(parent_group, workspace_node, outcome_groups, workspace_writer)

    @classmethod
    def write_random_selection_to_workspace(cls, parent_group, workspace_node, outcome_groups, workspace_writer):
        group_node = workspace_writer.write_new_node(parent_group.name, parent=workspace_node)
        # fill in random samples for all entities
        group_node["context"]["action_result"] = action_result = {}
        all_entities = cls.find_required_present_entities([parent_group])
        for entity in all_entities:
            entity_type = workspace_writer.get_entity_type(entity)
            entity_config = workspace_writer.get_entity_config(entity)
            action_result[entity] = cls._create_workspace_sample(entity_type, entity_config)
        action_result["group_id"] = f"<? new Random().nextInt({len(outcome_groups)}) ?>"
        for group_id, group in enumerate(outcome_groups):
            condition_node = workspace_writer.write_new_node(group.name, parent=group_node)
            condition_node["condition"] = f"$action_result.group_id == {group_id}"
            group.write_to_workspace(condition_node, workspace_writer)

    @classmethod
    def _create_workspace_sample(cls, entity_type, entity_config):
        sample_batch = set()
        unhashable_batch = list()
        for i in range(20):
            sample = cls._make_entity_type_sample(entity_type, entity_config)
            if isinstance(sample, collections.Hashable):
                sample_batch.add(sample)
            else:
                unhashable_batch.append(sample)

        spel_samples = WorkspaceConfigurationWriter.to_spel(sample_batch)
        if unhashable_batch:
            spel_samples = WorkspaceConfigurationWriter.to_spel(unhashable_batch)

        sample_code = f"<? {spel_samples}.getRandomItem() ?>"
        return sample_code

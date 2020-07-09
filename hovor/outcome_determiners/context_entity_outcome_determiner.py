import itertools
import re
from collections import defaultdict

from watson_developer_cloud.assistant_v1 import CreateIntent, CreateExample, Mentions, CreateEntity

from hovor.outcome_determiners.unified_workspace_outcome_determiner import UnifiedWorkspaceOutcomeDeterminer
from hovor.runtime.outcome_determination_progress import OutcomeDeterminationProgress
# from hovor.outcome_determiners.workspace_outcome_determiner import WorkspaceOutcomeDeterminer


class ContextEntityOutcomeDeterminer(UnifiedWorkspaceOutcomeDeterminer):
    def __init__(self, action_name, name, entity_mapping, entity_definitions, force_replace_existing_ws=False):
        self._entity_definitions = dict(entity_definitions)

        intents = {"global_intent": list(entity_mapping)}
        super().__init__(action_name, name, intents, [])

    def rank_groups(self, outcome_groups, progress: OutcomeDeterminationProgress):
        """
        Identifies recognized entities, and finds best matching outcomes.

        """

        response = self._message_wa(progress._session.current_action.name, progress.action_result.get_field('input'))
        self._report_entities(response, progress)
        entity_confidences = self._parse_entity_confidences(response)

        ranked_groups = []
        for group in outcome_groups:
            required_entities = self.find_required_present_entities([group])

            confidence_score = 0.0
            for entity in required_entities:
                # detect target confidence level (maybe-have vs have)
                target_level = self._get_target_confidence_level(group, entity)

                # increase confidence for every recognized entity
                actual_confidence = entity_confidences.get(entity, 0)
                score = 1.0 - abs(target_level - actual_confidence)
                confidence_score += score

            ranked_groups.append((group, confidence_score))

        self._monitor_entities(response, progress)
        return self._normalize_scores(ranked_groups), progress

    def configuration(self, action_name, name, intent_definitions, entities):
        """Overrides WA workspace configuration - intents are used as examples for context entities."""

        if entities:
            raise ValueError("entities are expected empty")

        intents = []

        # collect all the examples
        for intent_name, examples in intent_definitions.items():
            intent_examples = []
            for example in examples:
                for instantiated_example, spans in self.instantiate_example(example):
                    entity_mentions = []
                    for entity, start_char, end_char in spans:
                        mention = Mentions(entity, [start_char, end_char])
                        entity_mentions.append(mention)

                    # note, mentions are not supported in older versions of the API
                    intent_example = CreateExample(instantiated_example, mentions=entity_mentions)
                    intent_examples.append(intent_example)

            intents.append(CreateIntent(action_name+'-'+intent_name, examples=intent_examples))

        # define all entities
        entities = []
        for entity_name, entity_type in self._entity_definitions.items():
            if entity_type == 'sys-date_range':
                # contextual system entities are not available in WA - workaround by standard sys-date entity
                entities.append(CreateEntity("sys-date"))
            else:
                entities.append(CreateEntity(entity_name))

        self._wa_definitions = {
            'name': name,
            'intents': intents,
            'entities': entities
        }

        return self._wa_definitions

    def instantiate_example(self, example):
        """
        Example is of form: I want to go from $src to $dst.
        We need to replace $vars by examples of the entities.
        """

        tokens = self.tokenize_variables(example)

        value_examples = []
        for i in range(len(tokens)):
            token = tokens[i]
            # todo watson assistant does not have yet support for contextual sys entities - using value examples is a workaround
            value_examples.append(self.get_examples(token))

        # cross product across all example values
        instances = []
        substitutions = itertools.product(*value_examples)
        # create example for every combination of example substitutions
        for substitution in substitutions:
            example_str = ""
            ranges = []
            for i in range(len(substitution)):
                token = substitution[i]
                if example_str:
                    # ensures proper words separation
                    example_str += " "

                if isinstance(token, tuple):
                    # entity value - remember its position
                    entity_name, value = token
                    value_start = len(example_str)
                    value_end = value_start + len(value)
                    entity_range = (entity_name, value_start, value_end)
                    ranges.append(entity_range)
                    token = value

                example_str += token

            instance = (example_str, ranges)
            instances.append(instance)

        return instances

    def get_examples(self, token):
        var_token = token[1:]
        if var_token not in self._entity_definitions:
            # no known entity example detected
            return [token]

        type = self._entity_definitions[var_token]

        def add_entity_info(values):
            return [(var_token, value) for value in values]

        if type == "sys-location":
            return add_entity_info(["Prague", "Paris", "New York"])

        if type == "sys-date_range":
            # date entities are workarounded by sys-date
            return var_token

        if isinstance(type, list):
            return add_entity_info(type)

        # we don't know anything about the type - treat it as a general object
        return add_entity_info([var_token, "color", "object", "weather", "Peter", "Yorktown", "dog"])

    def tokenize_variables(self, example):
        matches = re.findall(r'(([^ .?,]+)|([,?.]+))', example)
        return [match[0] for match in matches]

    def _get_target_confidence_level(self, group, entity):
        for requirement in group.entity_requirements:
            if requirement.entity != entity:
                continue

            if requirement.maybe_have:
                return 0.6  # todo (principial solution) this depends on context entity model - this number was empirically fitted on initial action

        return 1.0

    def _report_entities(self, response, progress):
        name_to_values = defaultdict(list)

        # collect values according to their types
        for entity in response['entities']:
            entity_name = entity['entity']
            name_to_values[entity_name].append(entity['value'])

        # report the entities to the progress
        for name, entity_type in self._entity_definitions.items():
            if entity_type == "sys-date_range":
                dates = name_to_values.get("sys-date", [])
                if len(dates) == 2:
                    progress.add_detected_entity(name, tuple(dates))
            else:
                if name in name_to_values:
                    progress.add_detected_entity(name, name_to_values[name][0])

    def _monitor_entities(self, response, progress):
        entities = {}
        for entity in response['entities']:
            entity_name = entity['entity']
            entities[entity_name] = (entity['value'], entity['confidence'])

        progress.add_monitor_field(self.workspace_id, "recognized_entities", entities)

    def _normalize_scores(self, ranked_groups):
        score_sum = sum(group[1] for group in ranked_groups)
        if score_sum <= 0:
            return ranked_groups

        normalized_ranked_groups = []
        for group, score in ranked_groups:
            normalized_ranked_groups.append((group, score / score_sum))

        return normalized_ranked_groups

    def _parse_entity_confidences(self, response):
        confidences = {}

        for entity in response['entities']:
            entity_name = entity['entity']
            confidences[entity_name] = entity['confidence']

        return confidences

    def write_to_workspace(self, parent_group, workspace_node, outcome_groups, workspace_writer):
        # prepare global intent/entity definitions
        workspace_writer.write_workspace_entities(self._wa_definitions["entities"])
        workspace_writer.write_workspace_intents(self._wa_definitions["intents"])

        # outcome determination nodes
        read_node = workspace_writer.write_new_node(parent_group.name, parent=workspace_node, skip_user_input=False)
        group_node = workspace_writer.write_new_node(parent_group.name + "-parse", parent=read_node)
        group_node["context"]["action_result"] = action_result = {}

        # parse all available entities
        entities = self._find_required_delta_entities(parent_group)
        for entity in entities:
            entity_value = workspace_writer.get_recognized_context_entity(entity)
            entity_reference = f"<? {entity_value} ?>"
            action_result[entity] = entity_reference

        # create condition node for each outcome
        sorted_groups = sorted(outcome_groups, key=lambda g: len(self._find_required_delta_entities(g)),
                               reverse=True)
        for group in sorted_groups:
            condition_node = workspace_writer.write_new_node(group.name, parent=group_node)

            condition_parts = ["true"]
            entities = self._find_required_delta_entities(group)
            for entity in entities:
                condition_parts.append(f"$action_result.{entity}")

            condition_node["condition"] = " && ".join(condition_parts)
            group.write_to_workspace(condition_node, workspace_writer)

    def _find_required_delta_entities(self, group):
        all_entities = self.find_required_present_entities([group])

        delta = set(self._entity_definitions.keys()).intersection(set(all_entities))
        return list(delta)

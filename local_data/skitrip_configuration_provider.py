from collections import OrderedDict

from hovor.actions.action_base import ActionBase
from hovor.configuration.configuration_provider_base import ConfigurationProviderBase
from hovor.effects.assign_entity_effect import AssignEntityEffect
from hovor.outcome_determiners.context_entity_outcome_determiner import ContextEntityOutcomeDeterminer
from hovor.outcome_determiners.random_outcome_determiner import RandomOutcomeDeterminer
from hovor.outcome_determiners.workspace_outcome_determiner import WorkspaceOutcomeDeterminer
from hovor.planning import controller
from hovor.planning.controller.node import ControllerNode
from hovor.planning.controller.edge import ControllerEdge
from hovor.planning.entity_requirement import EntityRequirement
from hovor.planning.outcome_groups.deterministic_outcome_group import DeterministicOutcomeGroup
from hovor.planning.outcome_groups.or_outcome_group import OrOutcomeGroup
from hovor.outcome_determiners.outcome_determination_info import OutcomeDeterminationInfo
from hovor.planning.partial_state import PartialState
from local_data.ski_gen import psgraph, action_mapping, intent_info_mapping, get_domain, context_entity_info_mapping


class SkitripConfigurationProvider(ConfigurationProviderBase):
    """
    Specific configuration provider that loads mockup skitrip data.
    For real use cases, new configuration providers should be implemented.
    """

    def __init__(self, use_wa_determiners=True):
        # load some indexes for faster lookup
        self._intent_mapping = self._sanitize_intents(intent_info_mapping)

        self._outcome_group_name_to_info = {}

        self._node_id_to_node = self._load_nodes()
        self._set_nodes_action_names()
        self._set_nodes_children()
        self._edge_to_condition = self._load_condition_edges()
        self._use_wa_determiners = use_wa_determiners

        # populate nodes with extra information required by the controller based plan execution
        self._set_nodes_outcome_groups()

        # use the existing data structures to compute the edge objects
        self._edge_id_to_edge = self._load_edges()

        # create a plan
        plan = controller.Plan(self._node_id_to_node.values(),
                               self._edge_id_to_edge.values(),
                               get_domain())

        super(SkitripConfigurationProvider, self).__init__('plan-ski', plan)

    def get_node_info(self, node):
        action_config = self._get_action_config(node)
        return action_config['definition']

    def get_node_type(self, node):
        action_config = self._get_action_config(node)
        return action_config['type']

    def create_action(self, node, state, context):
        """Creates action for the given state"""
        action_config = self._get_action_config(node)
        action = ActionBase.create_action(action_config, state, context, node.outcome_group)
        return action

    def create_initial_effects(self):
        return []

    def get_outcome_determination_info(self, outcome_group_name):
        return self._outcome_group_name_to_info[outcome_group_name]

    def _load_nodes(self):
        """Loads nodes from the generated plan"""

        node_id_to_node = {}
        for node_id, node_definition in psgraph["nodes"].items():
            # read definition
            state_id = node_definition["state"]
            state_fluents = psgraph["states"][state_id]

            # build a node with its partial state
            is_initial_state = node_id == psgraph["init"]
            is_goal_state = node_id == psgraph["goal"]

            partial_state = PartialState(state_fluents)
            node = ControllerNode(node_id, partial_state, is_initial_state, is_goal_state)

            node_id_to_node[node_id] = node

        return node_id_to_node

    def _load_edges(self):
        """Loads the edges from the existing data structures"""
        edge_id_to_edge = {}
        eid = 0
        for src_node in self._node_id_to_node.values():
            intent_names = list(self._intent_mapping.get(src_node.action_name, []))
            oid = 0
            for outcome_name, dst_node in src_node.named_children:
                intent_name = intent_names[oid]
                eid += 1
                oid += 1
                edge = ControllerEdge(eid,
                                      src_node,
                                      dst_node,
                                      outcome_name,
                                      self._intent_mapping[src_node.action_name][intent_name])
                edge_id_to_edge[eid] = edge
        return edge_id_to_edge

    def _set_nodes_children(self):
        for node in self._node_id_to_node.values():
            node.named_children = self._get_named_children(node)
            for child_name, child in node.named_children:
                child.parent = node

    def _set_nodes_action_names(self):
        for node in self._node_id_to_node.values():
            node.action_name = psgraph["nodes"][node.node_id]["action"]

    def _set_nodes_outcome_groups(self):
        for node in self._node_id_to_node.values():
            node.outcome_group = self._create_outcome_group(node)

    def _load_condition_edges(self):
        edge_to_condition = {}

        for node in self._node_id_to_node.values():
            for condition, child in node.named_children:
                edge = (node, child)
                edge_to_condition[edge] = condition

        return edge_to_condition

    def _create_outcome_group(self, node):
        group_name = str(node.node_id) + "-group"

        # create all nested deterministic groups
        nested_groups = []
        for child_name, outcome_node in node.named_children:
            branch_name = group_name + "." + str(str(outcome_node.node_id) + "-outcome")

            description = {"intent": child_name}
            nested_groups.append(self._new_deterministic_group(branch_name, node, outcome_node, description))

        if len(nested_groups) == 1:
            return nested_groups[0]

        return self._new_or_group(group_name, node, nested_groups)

    def _get_named_children(self, node):
        group_name = str(node.node_id) + "-group"

        # create all nested deterministic groups

        children = []
        outcome_node_ids = psgraph["nodes"][node.node_id]["successors"]
        for outcome_node_id in outcome_node_ids:
            outcome_name = group_name + "." + str(str(outcome_node_id) + "-outcome")

            outcome_node = self._get_node(outcome_node_id)
            children.append((outcome_name, outcome_node))

        return children

    def _get_node(self, node_id):
        return self._node_id_to_node[node_id]

    def _new_deterministic_group(self, group_name, source_node, target_node, description):
        present_entities, missing_entities = self._parse_entities(target_node.partial_state.fluents)
        requirements = []
        for e in present_entities:
            requirements.append(EntityRequirement(e, "found"))

        for e in missing_entities:
            requirements.append(EntityRequirement(e, "didnt-find"))

        group = DeterministicOutcomeGroup(group_name, requirements)

        initial_entities, _ = self._parse_entities(source_node.partial_state.fluents)
        effect_entities = present_entities - initial_entities

        effects = self._create_effects(effect_entities)
        self._outcome_group_name_to_info[group_name] = OutcomeDeterminationInfo(description=description,
                                                                                context_effects=effects)

        return group

    def _new_or_group(self, group_name, node, nested_groups):
        group = OrOutcomeGroup(group_name, nested_groups)
        outcome_determiner = self._create_outcome_determiner(node)
        self._outcome_group_name_to_info[group_name] = OutcomeDeterminationInfo(outcome_determiner=outcome_determiner)

        return group

    def _create_outcome_determiner(self, node):
        if node.action_name.startswith("dialogue-") and self._use_wa_determiners:
            # convert conditions to intent training examples

            entity_definitions = self._get_entity_definitions(node)
            intent_definitions = self._get_intent_definitions(node)
            if len(entity_definitions) == 0 and len(intent_definitions) <= 1:
                # there is no point for triggering sophisticated determination
                raise NotImplementedError(
                    "Outcome determiner for a single outcome is incorrect (use DeterministicOutcomeGroup)")

            return WorkspaceOutcomeDeterminer(node.action_name, intent_definitions, entity_definitions,
                                              force_replace_existing_ws=False)

        if node.action_name in context_entity_info_mapping and self._use_wa_determiners:
            entity_definitions = self._get_entity_definitions(node)
            mapping = context_entity_info_mapping[node.action_name]
            return ContextEntityOutcomeDeterminer(node.action_name, mapping, entity_definitions)

        else:
            return RandomOutcomeDeterminer()

    def _get_action_config(self, node):
        action_name = node.action_name
        action_type = action_name.split("-")[0]

        if action_type == "":
            action_type = "goal_achieved"

        if node.action_name in context_entity_info_mapping and self._use_wa_determiners:
            action_type = "dialogue"

        is_message_action = len(self._intent_mapping.get(action_name, [])) <= 1 and action_type == "dialogue"
        if is_message_action:
            # some actions only reports to user - without expecting input
            action_type = "message"

        action_definition = action_mapping[action_name]
        action_config = {
            "name": action_name,
            "type": action_type,
            "definition": action_definition,
            "message_variants": [action_definition.split(":", maxsplit=1)[-1].strip()]
        }

        return action_config

    def _get_entity_definitions(self, node):
        entities = self._get_requested_entities(node)
        entity_definitions = {}
        for entity in entities:
            entity_definitions[entity] = self._get_entity_type_definition(entity)

        return entity_definitions

    def _get_intent_definitions(self, node):
        intent_definitions = {}
        for intent_name, intent_example in self._intent_mapping[node.action_name].items():
            clean_intent_example = intent_example.split(':')[-1]
            intent_definitions[intent_name] = [clean_intent_example]

        return intent_definitions

    def _get_requested_entities(self, node):
        # for mock purposes we assume on entities from fluents parsing
        existing_entities, _ = self._parse_entities(node.partial_state.fluents)

        requested_entities = set()
        for _, outcome_node in node.named_children:
            outcome_entities, _ = self._parse_entities(outcome_node.partial_state.fluents)
            requested_entities.update(outcome_entities)

        requested_entities.difference_update(existing_entities)
        return requested_entities

    def _create_effects(self, required_entities):
        effects = []
        for entity in required_entities:
            effect = AssignEntityEffect(entity, {
                "interpretation": "spel",
                "value": "$" + entity,
            })
            effects.append(effect)

        return effects

    def _get_entity_type_definition(self, entity):
        domain = get_domain()
        entity_type = domain["entities"][entity]

        return domain["types"][entity_type]

    def _parse_entities(self, fluents):
        required_present_entities = set()
        required_missing_entities = set()

        for entity, type in get_domain()["entities"].items():
            entity_predicate = "have-" + type + "(" + entity + ")"
            maybe_entity_predicate = "maybe-" + entity_predicate

            present_maybe_entity_atom = "Atom " + maybe_entity_predicate
            present_entity_atom = "Atom " + entity_predicate
            negated_maybe_entity_atom = "NegatedAtom " + maybe_entity_predicate
            negated_entity_atom = "NegatedAtom " + entity_predicate

            is_entity_required_present = present_entity_atom in fluents or present_maybe_entity_atom in fluents
            is_entity_required_missing = negated_entity_atom in fluents

            if is_entity_required_present:
                required_present_entities.add(entity)
            elif is_entity_required_missing:
                required_missing_entities.add(entity)

        return required_present_entities, required_missing_entities

    def _sanitize_intents(self, intent_info_mapping):
        result = {}
        for action_name, intents in intent_info_mapping.items():
            result[action_name] = new_intent_dict = OrderedDict()
            for intent_name, intent_value in intents.items():
                new_intent_name = action_name + "_" + intent_name
                new_intent_name = new_intent_name.replace(" ", "_")
                new_intent_dict[new_intent_name] = intent_value

        return result

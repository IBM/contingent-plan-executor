import json

from hovor.actions.action_base import ActionBase
from hovor.configuration.configuration_provider_base import ConfigurationProviderBase
from hovor.configuration.json_configuration_postprocessing import hovor_config_postprocess
from hovor.effects.assign_entity_effect import AssignEntityEffect
from hovor.outcome_determiners.context_dependent_outcome_determiner import ContextDependentOutcomeDeterminer
from hovor.outcome_determiners.default_system_outcome_determiner import DefaultSystemOutcomeDeterminer
from hovor.outcome_determiners.outcome_determination_info import OutcomeDeterminationInfo
from hovor.outcome_determiners.random_outcome_determiner import RandomOutcomeDeterminer
from hovor.outcome_determiners.nlu_outcome_determiner import NLUOutcomeDeterminer
from hovor.outcome_determiners.web_call_outcome_determiner import WebCallOutcomeDeterminer
from hovor.planning import controller
from hovor.planning.controller.edge import ControllerEdge
from hovor.planning.controller.node import ControllerNode
from hovor.planning.entity_requirement import EntityRequirement
from hovor.planning.outcome_groups.and_outcome_group import AndOutcomeGroup
from hovor.planning.outcome_groups.deterministic_outcome_group import DeterministicOutcomeGroup
from hovor.planning.outcome_groups.or_outcome_group import OrOutcomeGroup
from hovor.planning.partial_state import PartialState


class JsonConfigurationProvider(ConfigurationProviderBase):
    def __init__(self, path):
        with open(path + ".json") as f:
            configuration_data = json.load(f)

        with open(path + ".prp.json") as f:
            plan_data = json.load(f)["plan"]

        self._run_initialization(id, configuration_data, plan_data)

    def check_all_action_builders(self):
        self._force_build_of_all_action_builders()

    def _run_initialization(self, id, configuration_data, plan_data):
        self._outcome_group_name_to_info = {}
        self._configuration_data = hovor_config_postprocess(configuration_data)
        self._plan_data = plan_data
        plan = self._create_plan()
        self._initial_effect_list = []
        super(JsonConfigurationProvider, self).__init__(id, plan)

    def _get_nested_outcome_description(self, src_node, outcome_name, dst_node):
        outcome_config = self._get_nested_outcome_config(src_node, outcome_name)
        return outcome_config

    def get_outcome_determination_info(self, outcome_group_name):
        if len(self._outcome_group_name_to_info) == 0:
            # lazy create the info if needed
            # todo think about lazy creation of just a single action builder
            self._force_build_of_all_action_builders()

        return self._outcome_group_name_to_info[outcome_group_name]

    def _force_build_of_all_action_builders(self):
        for action_name, action_config in self._configuration_data["actions"].items():
            self._create_action_builder(action_name, action_config)
        # UnifiedWorkspaceOutcomeDeterminer.setup_workspace()

    def get_node_info(self, node):
        return self._get_action_config(node)

    def get_node_type(self, node):
        action_config = self._get_action_config(node)
        return action_config['type']

    def create_action(self, node, state, context):
        action_name = node.action_name
        action_config = self._configuration_data["actions"][action_name]
        # adding a full copy of the data.json data to be used for simulation
        action_config.update({"data_for_sim": self._configuration_data})
        builder = self._create_action_builder(action_name, action_config)

        return builder(state, context)

    def create_initial_effects(self):
        if not self._initial_effect_list:
            for entity, assignment in self._collect_domain()["entity_initial_assignments"].items():
                self._initial_effect_list.append(
                    AssignEntityEffect(entity, {'interpretation': 'json', 'value': assignment}))
        return self._initial_effect_list

    def _create_plan(self):
        node_id_to_node = self._load_nodes()
        edge_id_to_edge = self._load_edges(node_id_to_node)

        domain = self._collect_domain()

        # create a plan
        plan = controller.Plan(node_id_to_node.values(),
                               edge_id_to_edge.values(),
                               domain)

        return plan

    def _load_nodes(self):
        """Loads nodes from the generated plan"""
        plan_data = self._plan_data
        node_id_to_node = {}
        for node_id, node_definition in plan_data["nodes"].items():
            node_id = self._sanitize_node_id(node_id)
            # read definition
            state_id = node_definition["state"]
            state_fluents = plan_data["states"][state_id]
            action_name = plan_data["nodes"][node_id]["action"]

            # build a node with its partial state
            is_initial_state = node_id == self._sanitize_node_id(plan_data["init"])
            is_goal_state = node_id == self._sanitize_node_id(plan_data["goal"])

            partial_state = PartialState(state_fluents)
            node = ControllerNode(node_id, partial_state, is_initial_state, is_goal_state)

            # set action name performed at the node
            node.action_name = action_name

            node_id_to_node[node_id] = node

        # after all nodes are load we can define parentship between them
        for node in node_id_to_node.values():
            node.named_children = self._get_named_children(node, node_id_to_node)
            for name, child in node.named_children:
                child.parent = node

        return node_id_to_node

    def _load_edges(self, node_id_to_node):
        edge_id_to_edge = {}
        eid = 0
        for src_node in node_id_to_node.values():
            for outcome_name, dst_node in src_node.named_children:
                outcome_description = self._get_nested_outcome_description(src_node, outcome_name, dst_node)

                eid += 1
                edge = ControllerEdge(eid,
                                      src_node,
                                      dst_node,
                                      outcome_name,
                                      outcome_description)
                edge_id_to_edge[eid] = edge
        return edge_id_to_edge

    def _get_named_children(self, node, node_id_to_node):
        named_children = []
        successors = self._plan_data["nodes"][node.node_id]["successors"]
        used_names = set()
        for successor in successors:
            successor_id = self._sanitize_node_id(successor["successor_id"])
            outcome_node = node_id_to_node[successor_id]
            outcome_name = successor["outcome_label"]

            if outcome_name in used_names:
                raise ValueError(f'Duplicit outcome name {outcome_name} was registered')

            used_names.add(outcome_name)
            named_children.append((outcome_name, outcome_node))

        return named_children

    def _create_action_builder(self, action_name, action_config):
        outcome_group = self._create_outcome_group(action_name, action_config["effect"])
        action_config = dict(action_config)
        action_config["name"] = action_name

        # creating action builders here allows checking all the necessary fields
        # during configuration file parsing (no surprising errors at runtime)
        return ActionBase.create_builder(action_config, outcome_group)

    def _parse_group_name(self, outcome_config):
        return outcome_config.get("name", outcome_config.get("global-outcome-name", None))

    def _create_outcome_group(self, action_name, effect_config):
        outcome_group, determination_info = self._create_outcome_group_with_determination_info(action_name,
                                                                                               effect_config)
        self._outcome_group_name_to_info[outcome_group.name] = determination_info
        return outcome_group

    def _create_outcome_group_with_determination_info(self, action_name, effect_config):
        group_name = self._parse_group_name(effect_config)
        outcome_type = effect_config.get("type", None)
        if outcome_type == "or" or outcome_type == "oneof":
            children = self._create_outcome_children(action_name, effect_config["outcomes"])
            outcome_determiner = self._create_outcome_determiner(action_name, effect_config)

            return OrOutcomeGroup(group_name, children), OutcomeDeterminationInfo(
                outcome_determiner=outcome_determiner)

        elif outcome_type == "and":
            children = self._create_outcome_children(action_name, effect_config["outcomes"])
            return AndOutcomeGroup(group_name, children), OutcomeDeterminationInfo()

        elif outcome_type is None:
            effects = self._create_effects(effect_config)
            requirements = self._create_requirements(effect_config)

            return DeterministicOutcomeGroup(group_name, requirements), OutcomeDeterminationInfo(
                description=effect_config,
                context_effects=effects)

        else:
            raise NotImplementedError("Unknown outcome group " + outcome_type)

    def _create_effects(self, effect_config):
        effects = []
        for entity, value in effect_config["updates"].items():
            effect = AssignEntityEffect(entity, value)
            effects.append(effect)

        return effects

    def _create_requirements(self, effect_config):
        requirements = []
        for entity, requirement_type in effect_config["entity_requirements"].items():
            requirements.append(EntityRequirement(entity, requirement_type))

        return requirements

    def _create_outcome_determiner(self, action_name, outcome_config):
        outcome_determiner_name = outcome_config["outcome_determiner"]
        if outcome_determiner_name == "random_outcome_determiner":
            return RandomOutcomeDeterminer()

        if outcome_determiner_name == "context_dependent_outcome_determiner":
            return ContextDependentOutcomeDeterminer()

        if outcome_determiner_name == "default_system_outcome_determiner":
            return DefaultSystemOutcomeDeterminer()

        if outcome_determiner_name == "disambiguation_outcome_determiner":
            return NLUOutcomeDeterminer(action_name, outcome_config["outcomes"], self._configuration_data["context_variables"], self._configuration_data["intents"])

        if outcome_determiner_name == "web_call_outcome_determiner":
            return WebCallOutcomeDeterminer()

        print(f"WARNING: {outcome_determiner_name} fallbacked to random outcome determination")
        return RandomOutcomeDeterminer()

    def _get_entity_type_specification(self, entity):
        domain = self._collect_domain()
        type = domain["entities"][entity]

        if type == "enum":
            return domain["entity_configs"][entity]

        if type == "json":
            return entity

        return type

    def _create_outcome_children(self, action_name, outcomes):
        result = []
        for outcome_config in outcomes:
            outcome = self._create_outcome_group(action_name, outcome_config)
            result.append(outcome)

        return result

    def _get_action_config(self, node):
        return self._configuration_data["actions"][node.action_name]

    def _get_nested_outcome_config(self, node, outcome_name):
        action_config = self._get_action_config(node)

        outcomes = action_config["effect"].get("outcomes", [])
        for outcome in outcomes:
            if outcome["name"] == outcome_name:
                return outcome

        raise ValueError(f"Outcome config for {outcome_name} is missing")

    def _collect_domain(self):
        domain_types = {}
        domain_entities = {}
        entity_configs = {}
        entity_initial_assignments = {}
        domain = {
            "types": domain_types,
            "entities": domain_entities,
            "entity_configs": entity_configs,
            "entity_initial_assignments": entity_initial_assignments
        }
        variables = self._configuration_data["context_variables"]
        for variable, variable_configuration in variables.items():
            type = variable_configuration["type"]
            domain_types[type] = type
            entity_configs[variable] = variable_configuration.get("config", {})
            entity_initial_assignments[variable] = variable_configuration.get("init", None)
            domain_entities[variable] = type

        return domain

    def _sanitize_node_id(self, node_id):
        if isinstance(node_id, str):
            return node_id

        if isinstance(node_id, int):
            return str(node_id)

        raise ValueError("Invalid format of node_id %s" % node_id)

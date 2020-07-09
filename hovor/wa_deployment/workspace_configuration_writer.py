from typing import Dict

from watson_developer_cloud import AssistantV1
from watson_developer_cloud.assistant_v1 import CreateIntent, CreateExample, CreateDialogNode, DialogNodeNextStep, \
    DialogNodeOutput, CreateEntity, CreateValue, DialogNodeAction

from hovor.configuration.configuration_provider_base import ConfigurationProviderBase
from hovor.outcome_determiners.workspace_outcome_determiner import MAX_WS_PAGINATION
from hovor.planning.node import Node


class WorkspaceConfigurationWriter(object):
    def __init__(self, configuration_provider: ConfigurationProviderBase, debug_logging):
        self._wa_nodes_ordered = []
        self._wa_node_config: Dict[object, Dict] = {}
        self._plan_nodes = []
        self._wa_intent_definitions: Dict[str, str] = {}
        self._wa_entities = []
        self._wa_intents = []
        self._declared_sys_entities = set()
        self._entity_types = {}
        self._entity_configs = {}
        self._configuration_provider = configuration_provider

        self._execution_root = self._write_execution_root()

        self.is_debug_logging_enabled = debug_logging

        self.current_plan_node = None

    def write_initial_node(self, node):
        """Writes an initial plan node to the workspace (it does not mean it will be workspace root node)"""

        node_config = self._node_config(node)
        node_config["condition"] = "true"  # no condition for entering initial node

        self.write_direct_child(self._execution_root, node)

    def write_execution_step(self, node, node_action, outcome_group):
        """Writes a single step of execution (action + outcome resolution)"""
        from hovor.actions.goal_achieved_action import GoalAchievedAction

        self.current_plan_node = node

        action_node = self._write_action_node(node, node_action)
        action_node["context"][
            "action_result_eraser"] = "<? $action_result.clear() ?>"  # remove action results from previous actions

        if isinstance(node_action, GoalAchievedAction):
            action_node["skip_user_input"] = False
            return

        outcome_group.write_to_workspace(action_node, self)

    def write_new_node(self, node_name, parent=None, skip_user_input=True):
        node_name = f"{self.current_plan_node.node_id} {node_name}"
        if node_name in self._wa_node_config:
            raise ValueError("Requested new node name is already registered")

        config = self._node_config(id=node_name)
        config["parent"] = parent
        config["skip_user_input"] = skip_user_input
        config["condition"] = "true"
        return config

    def write_node(self, node):
        if node in self._wa_nodes_ordered:
            raise ValueError("Duplicit write")

        return self._wa_nodes_ordered.append(node)

    def write_entity(self, entity_name, entity_type, entity_config):
        if entity_type.startswith("sys-"):
            if entity_type == "sys-date_range":
                self._declared_sys_entities.add("sys-date")
            else:
                self._declared_sys_entities.add(entity_type)

        elif entity_type == "enum":
            self._wa_entities.append(CreateEntity(entity_name, values=[CreateValue(v) for v in entity_config]))

        elif entity_type in ["flag", "json"]:
            # such entity does not need special treatment
            pass

        else:
            raise NotImplementedError()

        self._entity_types[entity_name] = entity_type
        self._entity_configs[entity_name] = entity_config

    def get_recognized_context_entity(self, entity):
        type = self._entity_types[entity]
        if type == "sys-date_range":
            return self.get_recognized_entity(type)

        return "@" + entity

    def get_recognized_entity(self, type):
        if not type.startswith("sys-"):
            raise NotImplementedError("Custom entities not supported yet")

        if type == "sys-date_range":
            return "@sys-date[0] && @sys-date[1] ? @sys-date[0] > @sys-date[1] ? new JsonArray().append(@sys-date[1]).append(@sys-date[0]) :  new JsonArray().append(@sys-date[0]).append(@sys-date[1]) : null"

        return "@" + type

    def get_recognized_entity_condition(self, entity, type):
        if not type.startswith("sys-"):
            return "@" + entity

        if type == "sys-date_range":
            return "@sys-date.size()==2"

        return "@" + type

    def get_entity_type(self, entity_name):
        return self._entity_types[entity_name]

    def get_entity_config(self, entity_name):
        return self._entity_configs[entity_name]

    def get_outcome_determination_info(self, outcome_group_name):
        return self._configuration_provider.get_outcome_determination_info(outcome_group_name)

    @classmethod
    def chroot(cls, expression, new_root):
        """
        Changes "root" of all variable accesses to the new_root
        """

        indexes_to_chroot = cls._find_variable_starts(expression)
        expression_list = list(expression)

        for i in reversed(indexes_to_chroot):
            # traverse in reverse order so we don't need to offset unprocessed indexes
            expression_list[i:i + 1] = "$" + new_root + "."

        return "".join(expression_list)

    @classmethod
    def _find_variable_starts(cls, expression):
        indexes_to_chroot = []
        is_escaped_char = False
        is_in_double_quotes = False
        is_in_single_quotes = False
        for i in range(len(expression)):
            c = expression[i]

            # ==== special case recognition
            if is_escaped_char:
                is_escaped_char = False
                continue  # the character was escaped so we don't need to look at it

            if c == "\\":
                is_escaped_char = True
                continue

            if is_in_single_quotes:
                if c == "\'":
                    is_in_single_quotes = False

                continue  # skip everything which is within single quotes

            if is_in_double_quotes:
                if c == "\"":
                    is_in_double_quotes = False

                continue  # skip everything which is within double quotes

            # ==== standard character recognition
            if c == "\"":
                is_in_double_quotes = True
            elif c == "\'":
                is_in_single_quotes = True
            elif c == "$":
                indexes_to_chroot.append(i)

        return indexes_to_chroot

    def _write_execution_root(self):
        root = self._node_config(id="__EXECUTION_ROOT__")
        root["condition"] = "true"
        root["context"]["action_result"] = {}
        root["context"]["entities"] = {}

        for initial_effect in self._configuration_provider.create_initial_effects():
            initial_effect.write_to_workspace_node(root)

        return root

    def _write_action_node(self, node, node_action):
        action_node = self._node_config(node)
        action_node["skip_user_input"] = True
        new_action_node = node_action.write_to_workspace(action_node, self)

        return new_action_node

    def write_jump(self, node1, node2):
        config = self._node_config(node1)
        if config["next_step_node"] is not None:
            raise ValueError("Can't set next node multiple times")

        config["next_step_behavior"] = "jump_to"
        config["next_step_node"] = node2

    def write_direct_child(self, parent, child, skip_user_input=True):
        config = self._node_config(child)
        if config["parent"] is not None:
            raise ValueError("Can't set parent multiple times")

        config["parent"] = parent
        config["condition"] = "true"

        parent_config = self._node_config(parent)
        parent_config["skip_user_input"] = skip_user_input

    def get_child(self, parent_node):
        children = []
        for node in self._wa_nodes_ordered:
            if node["parent"] == parent_node or parent_node["next_step_node"] == node:
                children.append(node)

        if len(children) != 1:
            raise ValueError(f"Child could not been determined exactly among {len(children)} children")

        return children[0]

    def get_target_nodes(self, parent_node):
        targets = []

        if parent_node["next_step_node"]:
            targets.append(self._node_config(parent_node["next_step_node"]))
        else:
            for node in self._wa_nodes_ordered:
                if node["parent"] == parent_node:
                    targets.append(node)

        return targets

    def write_workspace_entities(self, entities):
        self._wa_entities.extend(entities)

    def write_workspace_intents(self, intents):
        self._wa_intents.extend(intents)

    def has_parent(self, node):
        return self._node_config(node)["parent"] is not None

    def _node_config(self, node=None, id: str = None):
        """
        node can be either planning node or auxiliary WA node
        """

        if id is not None:
            if node is not None:
                raise ValueError("Cannot accept node and id at the same time.")

            node = id

        if isinstance(node, dict):
            # auxiliary WA node
            return node

        if node not in self._wa_node_config:
            node_config = {
                "id": id if id else str(node.node_id) + " " + node.action_name,
                "condition": None,
                "parent": None,
                "next_step_node": None,
                "next_step_behavior": None,
                "skip_user_input": True,
                "output": None,
                "actions": [],
                "context": {}
            }

            if isinstance(node, Node):
                self._plan_nodes.append(node)

            self._wa_node_config[node] = node_config
            self._wa_nodes_ordered.append(node_config)
        return self._wa_node_config[node]

    @classmethod
    def to_spel(cls, obj):
        if isinstance(obj, str):
            obj = f"'{obj}'"

        if isinstance(obj, tuple) or isinstance(obj, list) or isinstance(obj, set):
            buffer = []
            for item in obj:
                item_as_spel = cls.to_spel(item)
                buffer.append(f".append({item_as_spel})")

            obj = "new JsonArray()" + "".join(buffer)

        return obj

    def deploy_to(self, assistant: AssistantV1, name: str):
        """
        Deploys written configuration via given assistant connector.
        If a workspace with same name exists already, it will be overwritten.
        """

        intents = []
        for intent_name, examples in self._wa_intent_definitions.items():
            intent = CreateIntent(intent_name, examples=[CreateExample(ex) for ex in examples])
            intents.append(intent)

        intents.extend(self._wa_intents)
        intents = self._make_unique_intents(intents)

        entities = []
        for sys_entity in self._declared_sys_entities:
            entities.append(CreateEntity(sys_entity))

        entities.extend(self._wa_entities)
        entities = self._make_unique_entities(entities)

        wa_nodes = self._create_wa_nodes()

        workspace_id = None
        for workspace in assistant.list_workspaces(page_limit=MAX_WS_PAGINATION).result["workspaces"]:
            if workspace["name"] == name:
                workspace_id = workspace["workspace_id"]
                break

        if workspace_id is None:
            result = assistant.create_workspace(
                name=name,
                intents=intents,
                entities=entities,
                dialog_nodes=wa_nodes
            )
        else:
            result = assistant.update_workspace(
                name=name,
                intents=intents,
                entities=entities,
                dialog_nodes=wa_nodes,
                workspace_id=workspace_id
            )

        unreachable_nodes = self._find_unreachable_nodes()
        print("DEPLOY STATISTICS")
        print(f"\t intents: {len(intents)}")
        print(f"\t entities: {len(entities)}")
        print(f"\t wa nodes: {len(wa_nodes)}")
        print(f"\t planning nodes: {len(self._plan_nodes)}")
        print(f"\t unreachable nodes: {len(unreachable_nodes)}")

        print()
        print(f"Status: {result.status_code}")
        print(f"WA API result: {result.result}")

    def _find_unreachable_nodes(self):
        reachable_nodes = set()
        worklist = [self._execution_root]
        reachable_nodes.add(worklist[0]["id"])
        while worklist:
            current_node = worklist.pop()
            conditions = set()
            for child in self.get_target_nodes(current_node):
                id = child["id"]
                if id in reachable_nodes:
                    # node was already visited
                    continue

                condition = child["condition"]
                if condition in conditions:
                    # the previous condition guards this node to be reached
                    continue

                # add the node for further processing
                conditions.add(condition)
                reachable_nodes.add(id)
                worklist.append(child)

                if condition in ["true", "1", "anything_else"]:
                    # other nodes won't be evaluated
                    break

        unreachable_nodes = []
        for node in self._wa_nodes_ordered:
            if node["id"] not in reachable_nodes:
                unreachable_nodes.append(node)

        return unreachable_nodes

    def _create_wa_nodes(self):
        parent_slot_fill_table = {}
        wa_nodes = []

        node_id_to_node = dict((node["id"], node) for node in self._wa_nodes_ordered)

        unreachable_nodes = self._find_unreachable_nodes()
        node_ids_to_export = [node["id"] for node in self._wa_nodes_ordered if node not in unreachable_nodes]
        exported_node_ids = set()

        while node_ids_to_export:
            node_id = node_ids_to_export.pop()
            if node_id is None or node_id in exported_node_ids:
                continue  # node was exported already

            exported_node_ids.add(node_id)
            node = node_id_to_node[node_id]

            parent_id = None
            previous_sibling_id = None
            next_step = None
            output = None
            node_actions = None

            if node["parent"]:
                # node can have only one child connected via parent - others are connected as siblings
                parent_id = str(self._node_config(node["parent"])["id"])
                if parent_id in parent_slot_fill_table:
                    previous_sibling_id = parent_slot_fill_table[parent_id]

                parent_slot_fill_table[parent_id] = node["id"]

                if previous_sibling_id is not None:
                    parent_id = None

                # ensure all dependencies are also exported
                node_ids_to_export.append(parent_id)
                node_ids_to_export.append(previous_sibling_id)

            if node["output"]:

                values = []
                node_output = node["output"]
                if isinstance(node_output, list):
                    values.extend(node_output)
                else:
                    values.append(node_output)

                output = DialogNodeOutput(
                    text={
                        "values": values,
                        "selection_policy": "sequential"
                    }
                )

            if node["actions"]:
                node_actions = []
                for action in node["actions"]:
                    node_action = DialogNodeAction(
                        name=action["name"],
                        action_type="server",
                        parameters=action["parameters"],
                        result_variable="context.action_result"
                    )
                    node_actions.append(node_action)

            if node["skip_user_input"]:
                next_step = DialogNodeNextStep(behavior="skip_user_input")

            if node["next_step_node"]:
                next_step_id = self._node_config(node["next_step_node"])["id"]
                behavior = node["next_step_behavior"]
                next_step = DialogNodeNextStep(behavior=behavior, dialog_node=str(next_step_id), selector="condition")

            wa_node = CreateDialogNode(
                dialog_node=str(node["id"]),
                next_step=next_step,
                parent=parent_id,
                context=node["context"],
                actions=node_actions,
                output=output,
                previous_sibling=previous_sibling_id,
                conditions=node["condition"],
            )

            wa_nodes.append(wa_node)
        return wa_nodes

    def _make_unique_intents(self, intents):
        result = []
        processed = set()

        for intent in intents:
            name = intent.intent
            if name in processed:
                continue

            processed.add(name)
            result.append(intent)

        return result

    def _make_unique_entities(self, entities):
        result = []
        processed = set()
        for entity in entities:
            name = entity.entity
            if name in processed:
                if entity.values:
                    raise ValueError("Cannot remove duplicities with examples")
                continue

            processed.add(name)
            result.append(entity)

        return result

import copy
import json
import os.path
import pickle
import random
import re
import string
from collections import defaultdict
from time import sleep

from watson_developer_cloud import AssistantV1
from watson_developer_cloud.assistant_v1 import CreateIntent, CreateExample, CreateEntity, CreateValue, InputData

from hovor.runtime.outcome_determination_progress import OutcomeDeterminationProgress
from hovor.outcome_determiners.outcome_determiner_base import OutcomeDeterminerBase

from hovor import DEBUG

# Cutoff for the fallback
FALLBACK_THRESHOLD = 0.2


class WorkspaceOutcomeDeterminer(OutcomeDeterminerBase):
    _workspace_cache_file = "./odws_cache.p"
    _workspace_cache = None
    _local_id = None

    def __init__(self, name, intents, entities, force_replace_existing_ws=False):
        """
        Upon initialization, finds a workspace with name id or creates it and adds the given intents and entities.
        :param name: str, name of the determiner and associated WA workspace
        :param intents: dict {"intent_name1": ["Intent example 1", "intent example 2"], ...}
        :param entities: dict e.g. {"ski_location": ["Whistler", "Mont Tremblant", ...], "sport": ["skiing", "cycling"]}
        """

        WorkspaceOutcomeDeterminer.ensure_cache_loaded()

        name = WorkspaceOutcomeDeterminer.sanitize_id(name)
        data_hash = WorkspaceOutcomeDeterminer.get_data_hash(intents, entities)

        self._real_entity_targets = {}  # same as entity targets but without type translation

        self._entity_targets = {}
        ws_config = self.configuration(name, intents, entities)

        if name in WorkspaceOutcomeDeterminer._workspace_cache:
            # Find the workspace_id of workspace with name name
            workspace_info = WorkspaceOutcomeDeterminer._workspace_cache[name]
            self.workspace_id = workspace_info["id"]

            replace_existing_ws = force_replace_existing_ws or data_hash != workspace_info["hash"]
            if replace_existing_ws:
                # Replace workspace if forced or training data changed







                # TODO: This is just a shim until we can replace the WA backend
                #assistant.update_workspace(self.workspace_id, append=False, **ws_config)






                workspace_info["hash"] = data_hash
                WorkspaceOutcomeDeterminer.save_cache()
        else:
            # Create new workspace








            # TODO: This is just a shim until we can replace the WA backend
            #ws = assistant.create_workspace(**ws_config)
            #self.workspace_id = ws.result['workspace_id']
            self.workspace_id = str(random.randint(0,123456787654321))







            WorkspaceOutcomeDeterminer._workspace_cache[name] = {
                "id": self.workspace_id,
                "hash": data_hash
            }
            WorkspaceOutcomeDeterminer.save_cache()

    @classmethod
    def get_workspace_ids(cls, cache_only=True):
        """
        Gets specified workspace ids
        :param cache_only: Determines whether only cached ids will be returned or
                all workspace ids existing in the instance.
                It is useful for e.g. removal operations where only
                workspace created by certain team member can be selected (cache_only=True).
        :return: The specified workspace ids.
        """

        if cache_only:
            # search ids in the cache
            cls.ensure_cache_loaded()
            for key, workspace_entry in dict(cls._workspace_cache).items():
                if key == "root":
                    continue  # this entry contains only cache related meta information

                yield workspace_entry["id"]

        else:
            available_workspaces_response = assistant.list_workspaces(page_limit=MAX_WS_PAGINATION).result
            for ws in available_workspaces_response['workspaces']:
                yield ws['workspace_id']

    @classmethod
    def delete_workspace(cls, workspace_id):
        WorkspaceOutcomeDeterminer.ensure_cache_loaded()

        response = assistant.delete_workspace(workspace_id)
        print("DELETING WORKSPACE " + workspace_id)
        print("\t " + str(response).replace("\n", " "))

        for key, workspace_entry in dict(cls._workspace_cache).items():
            if key == "root":
                continue

            if workspace_entry.get("id", None) == workspace_id:
                print("\t cache entry removed")
                del cls._workspace_cache[key]  # remove the deleted workspace from cache
                cls.save_cache()

    @classmethod
    def check_training_finished(cls, workspace_id):
        response = assistant.request("GET", f"/v1/workspaces/{workspace_id}/status", params={
            "version": "2017-04-21"
        })
        data = json.loads(response.result.text)
        return not data["training"]

    @classmethod
    def wait_for_training_finished(cls, workspace_id):

        first_waiting = True
        while True:

            if cls.check_training_finished(workspace_id):
                break

            if first_waiting:
                print(f"\t Watson Assistant is training on `{workspace_id}`, please wait.")
                print("\t\t", end='')
                first_waiting = False
            else:
                print(".", end='', flush=True)
                sleep(1)

        if not first_waiting:
            print()

    def rank_groups(self, outcome_groups, progress: OutcomeDeterminationProgress):
        """
        Identifies intents in the user utterance execution_result['input'] and returns scored outcome groups with
        with respect to their intent centered conditions

        """

        response = self._message_wa(progress.action_result.get_field('input'))
        self._report_entities(response, progress)

        ranked_groups = []
        for group in outcome_groups:
            outcome_description = progress.get_description(group.name)
            confidence = self._get_confidence(outcome_description, response)

            # Make sure that the fallback has /some/ signal
            if '-fallback' in group.name and (0 == len(response.get('entities', []))):
                confidence = max(confidence, FALLBACK_THRESHOLD)

            ranked_groups.append((group, confidence))

            DEBUG("group / conf: %s / %s" % (group.name, str(confidence)))

        self._monitor_entities(response, progress)
        self._monitor_intents(response, progress)

        return ranked_groups, progress

    @staticmethod
    def ensure_cache_loaded():
        """
        Ensures that workspace cache exists, is loaded and synchronized with real workspaces
        :return:
        """

        if WorkspaceOutcomeDeterminer._workspace_cache is not None:
            # cache was loaded already
            return

        if not os.path.exists(WorkspaceOutcomeDeterminer._workspace_cache_file):
            # first run - generate unique id which will be used as a workspace prefix
            uid = ''.join(random.choice(string.ascii_lowercase) for _ in range(10))
            WorkspaceOutcomeDeterminer._workspace_cache = {"root": uid}
            WorkspaceOutcomeDeterminer.save_cache()

        WorkspaceOutcomeDeterminer._workspace_cache = pickle.load(
            open(WorkspaceOutcomeDeterminer._workspace_cache_file, 'rb'))







        # TODO: This is just a shim until we can replace the WA backend
        #available_workspaces_response = assistant.list_workspaces(page_limit=MAX_WS_PAGINATION).result
        #existing_workspace_names = {ws['name'] for ws in available_workspaces_response['workspaces']}
        existing_workspace_names = []







        for key in list(WorkspaceOutcomeDeterminer._workspace_cache.keys()):
            if key == "root":
                # keep local information
                continue

            if key not in existing_workspace_names:
                del WorkspaceOutcomeDeterminer._workspace_cache[key]

        print("\t workspace name prefix: " + str(WorkspaceOutcomeDeterminer._workspace_cache["root"]))

    @staticmethod
    def save_cache():
        pickle.dump(WorkspaceOutcomeDeterminer._workspace_cache,
                    open(WorkspaceOutcomeDeterminer._workspace_cache_file, 'wb'))

    def configuration(self, name, intents, entities):

        # Process entities
        entities_conf = []
        for entity_name, vals in entities.items():
            self._real_entity_targets[entity_name] = vals

            if isinstance(vals, list):
                entities_conf.append(CreateEntity(entity_name, values=[CreateValue(v) for v in vals]))
                self._entity_targets[entity_name] = entity_name
            elif vals == "sys-date_range":
                # watson assistant date range bypass
                wa_type = "sys-date"
                self._entity_targets[wa_type] = (entity_name, entity_name)
                entities_conf.append(CreateEntity(wa_type, values=[]))
            elif isinstance(vals, str) and re.match('sys-', vals):
                if vals in self._entity_targets:
                    raise ValueError("Multiple targets specified for entity {}. So far unsupported.".format(vals))
                self._entity_targets[vals] = entity_name
                entities_conf.append(CreateEntity(vals, values=[]))
            else:
                raise ValueError("Invalid configuration for entity {}".format(entity_name))

        self._wa_definitions = {
            'name': name,
            'intents': [CreateIntent(intent_name,
                                     examples=[self._create_intent_example(ex) for ex in examples])
                        for intent_name, examples in intents.items()],
            'entities': entities_conf
        }
        return self._wa_definitions

    def _create_intent_example(self, example):
        return CreateExample(example.replace("$", "@"))

    @staticmethod
    def sanitize_id(id):
        uid = WorkspaceOutcomeDeterminer._workspace_cache["root"]
        return uid + " - " + id.strip().replace(" ", "_")

    @staticmethod
    def get_data_hash(intents, entities):
        intents_str = str(intents)
        entities_str = str(entities)
        data_str = str((intents_str, entities_str))

        # this hashing is intents/entities order independent, because the sum is character position independent
        return sum(bytearray(data_str, 'ascii'))

    def _message_wa(self, text):
        """
        Submit text as a user utterance to Watson Assistant
        :param text:
        :return:
        """

        WorkspaceOutcomeDeterminer.wait_for_training_finished(self.workspace_id)
        response = assistant.message(self.workspace_id, InputData(text), alternate_intents=True).result
        return response

    def _report_entities(self, response, progress):

        name_to_values = defaultdict(list)

        # collect values according to their types
        for entity in response['entities']:
            entity_name = self._entity_targets[entity['entity']]
            name_to_values[entity_name].append(entity['value'])

        # report the entities to the progress
        for name, values in name_to_values.items():
            if isinstance(name, tuple):
                # some entities can be composed (e.g. sys-date_range)
                if len(name) == len(values):
                    # all parts were recognized
                    progress.add_detected_entity(name[0], tuple(values))
            else:
                progress.add_detected_entity(name, values[0])

    def _get_confidence(self, outcome_description, response):
        intent_confidences = {intent['intent']: intent['confidence'] for intent in response['intents']}
        return intent_confidences.get(outcome_description["intent"], 0)

    def _monitor_entities(self, response, progress):
        entities = {}
        for entity in response['entities']:
            entity_name = self._entity_targets[entity['entity']]
            entity_value = entity['value']
            entities[entity_name] = entity_value

        progress.add_monitor_field(self.workspace_id, "recognized_entities", entities)

    def _monitor_intents(self, response, progress):
        intent_confidences = {intent['intent']: intent['confidence'] for intent in response['intents']}
        progress.add_monitor_field(self.workspace_id, "intent_confidences", intent_confidences)

    def write_to_workspace(self, parent_group, workspace_node, outcome_groups, workspace_writer):
        # prepare global intent/entity definitions
        workspace_writer.write_workspace_intents(self._wa_definitions["intents"])

        # create node for this group
        group_node = workspace_writer.write_new_node(parent_group.name, parent=workspace_node, skip_user_input=False)

        condition_nodes = self._write_condition_nodes(group_node, outcome_groups, workspace_writer)
        self._write_nointent_fallback_nodes(condition_nodes, workspace_writer)

    def _write_nointent_fallback_nodes(self, condition_nodes, workspace_writer):
        # duplicate nodes to fallback nodes - nodes without intents
        for condition_node in condition_nodes:
            fallback_node = copy.copy(condition_node)  # shallow copy
            fallback_node["id"] += "-fallback"

            # replace intents by true
            condition = fallback_node["condition"]
            condition = re.sub(r'[$]scoped_intent==\'[^\']*\'', 'true', condition)
            fallback_node["condition"] = condition
            workspace_writer.write_node(fallback_node)

            # connect to node
            target = workspace_writer.get_child(condition_node)
            workspace_writer.write_jump(fallback_node, target)

    def _write_condition_nodes(self, group_node, outcome_groups, workspace_writer):
        sorted_groups = sorted(outcome_groups, key=lambda g: len(self._find_required_delta_entities(g)),
                               reverse=True)

        group_node = workspace_writer.write_new_node("intent_proxy", parent=group_node)

        intents = set()
        condition_nodes = []
        for group in sorted_groups:
            condition_node = workspace_writer.write_new_node(group.name, parent=group_node)
            condition_node["context"]["action_result"] = {}
            info = workspace_writer.get_outcome_determination_info(group.name)

            intent = info.description["intent"]
            condition_parts = [f"$scoped_intent=='{intent}'"]
            delta_entities = self._find_required_delta_entities(group)
            for entity in delta_entities:
                type = workspace_writer.get_entity_type(entity)
                entity_value = workspace_writer.get_recognized_entity_condition(entity, type)
                condition_parts.append(entity_value)
                condition_node["context"]["action_result"][entity] = entity_value

            condition_node["condition"] = " && ".join(condition_parts)
            condition_nodes.append(condition_node)
            group.write_to_workspace(condition_node, workspace_writer)

            intents.add(f"'{intent}'")

        group_node["context"]["_eval"] = [
            f"$intent_scope = new JsonArray().append({','.join(intents)})",
            "$scoped_intent = intents.filter('i', '$intent_scope.contains(i.intent)').![intent]",
            "$scoped_intent = $scoped_intent.append('%no_intent%')",
            "$scoped_intent = $scoped_intent.get(0)"]

        return condition_nodes

    def _find_required_delta_entities(self, group):
        all_entities = self.find_required_present_entities([group])

        delta = set(self._real_entity_targets.keys()).intersection(set(all_entities))
        return list(delta)

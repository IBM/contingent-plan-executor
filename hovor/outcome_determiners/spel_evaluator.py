import os
import pickle
import random
import string
import time

from watson_developer_cloud.assistant_v1 import InputData, DialogNodeOutput
from ibm_watson.assistant_v1 import MessageInput

from hovor.outcome_determiners.unified_workspace_outcome_determiner import UnifiedWorkspaceOutcomeDeterminer
from hovor.outcome_determiners.workspace_outcome_determiner import MAX_WS_PAGINATION


class SpelEvaluator(object):
    _existing_nodes = None
    _id_cache = None
    _id_cache_file = "./sews_cache.p"

    _workspace_id = None

    @classmethod
    def evaluate(cls, spel, context={}):
        # cls.ensure_cache_loaded()
        cls.setup_workspace(UnifiedWorkspaceOutcomeDeterminer.workspace_id)

        node_name = cls._create_node_name(spel)
        if node_name not in cls._existing_nodes:
            # ensure the evaluation node is in place.
            UnifiedWorkspaceOutcomeDeterminer.assistant.create_dialog_node(cls.get_workspace_id(),
                                                                           dialog_node=node_name,
                                                                           conditions=f"input[\"text\"]==\"{node_name}\"",
                                                                           context={
                                                                               "_eval": [
                                                                                   "$result = " + spel
                                                                               ]
                                                                           },
                                                                           output=DialogNodeOutput(text={
                                                                               "values": [f"<?$result?>"],
                                                                               "selection_policy": "sequential"
                                                                           }))

            cls._existing_nodes.add(node_name)

        # TODO: The node creation is likely async, and the code below fails to
        #       get anything that matches because the node doesn't exist yet.
        #       Going to sleep for a bit to handle it.
        #
        # NOTE: This has actually been confirmed. Seems as though ~35sec is the
        #       limit we'd face, but that would be a horrible experience. Going
        #       to instead leave it at 15sec, and throw an error otherwise.
        #
        # - https://github.ibm.com/watson-engagement-advisor/wea-backlog/issues/32779
        #
        response = cls._send_evaluation_request(node_name, context)
        count = 0
        RETRY_LIMIT = 30
        while (count < RETRY_LIMIT) and (0 == len(response["output"]["text"])):
            count += 1
            time.sleep(0.5)
            response = cls._send_evaluation_request(node_name, context)

        assert count < RETRY_LIMIT, "Node creation for SPEL evaluation timed out."

        return response["output"]["text"][0]

    @classmethod
    def _send_evaluation_request(cls, spel, context):
        return UnifiedWorkspaceOutcomeDeterminer.assistant.message(cls.get_workspace_id(),
                                                                   input=MessageInput(text=spel),
                                                                   context=context).result

    @classmethod
    def _create_node_name(cls, spel):
        name = spel
        for pattern, replacement in {",": "comma", "$": "context", "+": "plus", "-": "minus", "*": "multiply",
                                     "/": "div", "%": "mod", "\"": "quote", "'": "singlequote", "<": "le", ">": "ge",
                                     "=": "eq"}.items():
            name = name.replace(pattern, "_" + replacement + "_")
        return name

    @classmethod
    def _send_evaluation(cls, spel, context):
        UnifiedWorkspaceOutcomeDeterminer.assistant.message(
            cls.get_workspace_id(), spel, context=context
        )
        raise NotImplementedError()

    @classmethod
    def setup_workspace(cls, workspace_id):
        """
        loads the workspace
        :return:
        """
        available_workspaces_response = UnifiedWorkspaceOutcomeDeterminer.assistant.list_workspaces().get_result()
        assert workspace_id in [ws['workspace_id'] for ws in available_workspaces_response[
            'workspaces']], "Workspace id %s does not exist" % workspace_id
        cls._workspace_id = workspace_id

        nodes = \
            UnifiedWorkspaceOutcomeDeterminer.assistant.list_dialog_nodes(workspace_id=cls.get_workspace_id()).result[
                "dialog_nodes"]
        cls._existing_nodes = set(node['dialog_node'] for node in nodes)

    @classmethod
    def ensure_cache_loaded(cls):
        """
        Ensures that workspace cache exists, is loaded and synchronized with real workspaces
        :return:
        """

        if SpelEvaluator._existing_nodes is not None:
            # cache was loaded already
            return

        if not os.path.exists(SpelEvaluator._id_cache_file):
            # first run - generate unique id which will be used as a workspace prefix
            uid = ''.join(random.choice(string.ascii_lowercase) for _ in range(10))
            SpelEvaluator._id_cache = {"root": uid}
            SpelEvaluator.save_cache()

        SpelEvaluator._id_cache = pickle.load(
            open(SpelEvaluator._id_cache_file, 'rb'))

        available_workspaces_response = UnifiedWorkspaceOutcomeDeterminer.assistant.list_workspaces(
            page_limit=MAX_WS_PAGINATION).result
        for workspace in available_workspaces_response["workspaces"]:
            if workspace["name"] == cls.get_workspace_name():
                cls._workspace_id = workspace["workspace_id"]

        if cls._workspace_id is None:
            # create the workspace for the first time
            workspace = UnifiedWorkspaceOutcomeDeterminer.assistant.create_workspace(cls.get_workspace_name()).result
            cls._workspace_id = workspace["workspace_id"]

        workspace = UnifiedWorkspaceOutcomeDeterminer.assistant.get_workspace(cls.get_workspace_id(),
                                                                              export=True).result
        nodes = workspace["dialog_nodes"]
        cls._existing_nodes = set(node['dialog_node'] for node in nodes)

        print("\t workspace name prefix: " + str(SpelEvaluator._id_cache["root"]))

    @classmethod
    def save_cache(cls):
        pickle.dump(SpelEvaluator._id_cache,
                    open(SpelEvaluator._id_cache_file, 'wb'))

    @classmethod
    def get_workspace_name(cls):
        return SpelEvaluator._id_cache["root"] + "-WA_expr_eval"

    @classmethod
    def get_workspace_id(cls):
        return cls._workspace_id

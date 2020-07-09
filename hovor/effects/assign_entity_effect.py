import re

from hovor.outcome_determiners.spel_evaluator import SpelEvaluator
from hovor.runtime.fields_container import FieldsContainer


class AssignEntityEffect(object):
    def __init__(self, entity, value_config):
        if entity.startswith("$"):
            raise ValueError("entity should not be an expression")

        self.entity = entity
        self.interpretation = value_config["interpretation"]
        if self.interpretation not in ["json", "spel", "noop"]:
            raise ValueError(f"Unknown interpretation '{self.interpretation}'.")

        self.use_spel = self.interpretation == "spel"
        self.skip_evaluation = self.interpretation == "noop"
        self.value = value_config["value"]

        if self.use_spel and not isinstance(self.value, str):
            raise ValueError(f"Spel expression must be string but '{self.value}' was given.")

    def __call__(self, context, determination_result):
        if self.skip_evaluation:
            return True

        if self.use_spel:
            value, is_success = self._evaluate_spel(self.value, context, determination_result)
            if not is_success:
                # spel evaluation may fail for some reasons
                return False
        else:
            value = self.value

        context.set_field(self.entity, value)
        return True

    def _evaluate_spel(self, spel, context, determination_result):

        # TODO: Address the chrooting fully and properly instead of this workaround
        spel = spel.replace('$action_result.', '$')
        spel = spel.replace('$entities.', '$')

        joined_fields = FieldsContainer(context, determination_result)

        if spel == "null":
            return None, True

        is_simple_reference = re.match("^[$][.a-zA-Z01-9_-]+$", spel) is not None
        if is_simple_reference:
            # field access will be evaluted faster locally
            reference = spel[1:]
            if not joined_fields.has_field(reference):
                return None, False

            return joined_fields.get_field(reference), True

        fields_dump = joined_fields.dump()
        return SpelEvaluator.evaluate(spel, fields_dump), True

    def write_to_workspace_node(self, workspace_node):
        context = workspace_node["context"]
        if "entities" not in context:
            context["entities"] = {}

        v = self.value

        if isinstance(v, str):
            # Make sure everything is chroot'd properly
            for root in v.split('$')[1:]:
                assert (root[:len('entities.')] == 'entities.') or \
                        (root[:len('action_result.')] == 'action_result.'), \
                        "Error: Missing a valid chroot for variable in %s" % v
            chrooted_spel = self.value
        elif self.value is None or isinstance(v, (int, bool, float)):
            # keep the value unchanged
            chrooted_spel = self.value
        else:
            chrooted_spel = str(self.value)

        context["entities"][self.entity] = chrooted_spel

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
            if self.value in [True, False, None]:
                value = self.value
            else:
                if self.entity in determination_result._fields: 
                    value = determination_result._fields[self.entity]
                else:
                    return False
        context.set_field(self.entity, value)
        return True

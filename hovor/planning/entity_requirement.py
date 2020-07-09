class EntityRequirement(object):
    def __init__(self, entity, type):
        self._entity = entity
        self._must_have = type == "found"
        self._maybe_have = type == "maybe-found"
        self._dont_have = type == "didnt-find"

        is_valid = self._must_have or self._maybe_have or self._dont_have
        if not is_valid:
            raise ValueError(f"Target confidence {type} was not recognized.")

    @property
    def entity(self):
        return self._entity

    @property
    def must_have(self):
        return self._must_have

    @property
    def maybe_have(self):
        return self._maybe_have

    @property
    def dont_have(self):
        return self._dont_have

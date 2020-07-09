from copy import deepcopy


class FieldsContainer(object):
    def __init__(self, *field_containers):
        self._fields = {}

        for container in field_containers:
            self._fields.update(container.dump())

    @property
    def field_names(self):
        return list(self._fields.keys())

    def dump(self):
        return deepcopy(self._fields)

    def has_field(self, complex_field):
        value = self.get_field(complex_field)
        return value is not None

    def get_field(self, complex_field, unresolved_depth=0, create_levels=False, unresolved_path=[]):
        self._require_field_name(complex_field)

        path = complex_field.split(".")
        for i in range(unresolved_depth):
            unresolved_path.insert(0, path.pop(-1))

        current_level = self._fields
        while path and current_level is not None:
            current_level_name = path.pop(0)
            if create_levels and current_level_name not in current_level:
                current_level[current_level_name] = {}

            current_level = current_level.get(current_level_name, None)

        return current_level

    def set_field(self, complex_field, value):
        self._require_field_name(complex_field)

        path = []
        level = self.get_field(complex_field, unresolved_depth=1, create_levels=True, unresolved_path=path)
        level[path[-1]] = value

    def remove_field(self, complex_field):
        # fields can be removed only in a flat manner
        self._require_field_name(complex_field)
        if complex_field in self._fields:
            del self._fields[complex_field]

    def _require_field_name(self, complex_field):
        if complex_field.startswith("$"):
            raise ValueError(f"Invalid field name `{complex_field}`.")

    def __repr__(self):
        return str(self._fields)

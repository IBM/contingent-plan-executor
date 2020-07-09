class PartialState(object):
    """Representation of a planning state (i.e., set of predicates)
    """

    def __init__(self, fluents):
        self.fluents = set(fluents)

    def get_positive_fluents(self):
        result = []

        for fluent, is_positive in self._parse_fluents(self.fluents):
            if is_positive:
                result.append(fluent)

        return result

    def contains(self, fluent):
        return fluent in self.fluents

    def update_by(self, partial_state):
        """
        Creates a state that is updated by the given partial_state.
        """

        # create a new fluents copy so old fluents are not corrupted
        new_fluents = set(self.fluents)

        # merge fluents based on their polarity
        for fluent, is_fluent_positive in self._parse_fluents(partial_state.fluents):
            positive_fluent = self._as_positive_fluent(fluent)
            negative_fluent = self._as_negative_fluent(fluent)
            if is_fluent_positive:
                new_fluents.discard(negative_fluent)
                new_fluents.add(positive_fluent)
            else:
                new_fluents.discard(positive_fluent)
                new_fluents.add(negative_fluent)

        return PartialState(new_fluents)

    def entails(self, partial_state):
        """
        Determine whether the current complete state entails the given partial state.

        Unspecified fluents in the complete state are treated as false.
        Unspecified fluents in partial_state are treated as undefined (we don't care of their value)

        """
        for fluent, is_positive in self._parse_fluents(partial_state.fluents):
            # try to find the entailment contradiction

            if is_positive and fluent not in self.fluents:
                return False

            positive_fluent = self._as_positive_fluent(fluent)
            if not is_positive and positive_fluent in self.fluents:
                return False

        # no contradiction found
        return True

    def _parse_fluents(self, fluents):
        result = []
        for fluent in fluents:
            positive_fluent = self._as_positive_fluent(fluent)
            negative_fluent = self._as_negative_fluent(fluent)

            if fluent == positive_fluent:
                result.append((fluent, True))
            elif fluent == negative_fluent:
                result.append((fluent, False))
            else:
                raise AssertionError("Fluent parsing.")

        return result

    def _as_positive_fluent(self, fluent):
        return "Atom " + fluent.split(' ', 1)[1]

    def _as_negative_fluent(self, fluent):
        return "NegatedAtom " + fluent.split(' ', 1)[1]

    def __repr__(self):
        return str(self.fluents)

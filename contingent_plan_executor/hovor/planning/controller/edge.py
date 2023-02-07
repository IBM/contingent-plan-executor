
class ControllerEdge(object):
    """
    Edge API specific to a plan represented as a controller.
    """

    def __init__(self, id, src, dst, outcome_id, info):
        self._id = id
        self._src = src
        self._dst = dst
        self._outcome_id = outcome_id
        self._info = info

    @property
    def edge_id(self):
        return self._id

    @property
    def src(self):
        """Source node of the edge."""
        return self._src

    @property
    def dst(self):
        """Destination node of the edge."""
        return self._dst

    @property
    def outcome_id(self):
        """The id for the full realized outcome corresponding to this edge."""
        return self._outcome_id

    @property
    def info(self):
        """Any pertinent info about this edge."""
        return self._info

    def __eq__(self, other):
        return self.edge_id == other.edge_id

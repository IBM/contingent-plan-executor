from abc import abstractmethod

from hovor.runtime.outcome_determination_progress import OutcomeDeterminationProgress


class OutcomeGroupBase(object):
    def __init__(self, name):
        self._name = name

    @property
    def name(self):
        return self._name

    @abstractmethod
    def update_progress(self, initial_progress: OutcomeDeterminationProgress):
        """
        Returns an updated determination progress.
        IT IS CALLER RESPONSIBILITY to create copy if they need initial progress unchanged
            ==> It is safe to update the initial_progress

        Determination considers nesting logic of outcomes.

        NOTE: Determination progress can be copied and modified multiple times within the call
            - as a result of outcome group nesting
        """

        raise NotImplementedError("has to be overriden")

    def write_to_workspace(self, workspace_node, workspace_writer):
        raise NotImplementedError("Outcome group " + self.name + ", implemented by " + str(
            type(self)) + " does not support workspace deployment yet.")

from abc import ABC, abstractmethod, abstractproperty


class RolloutStub(ABC):
    @abstractproperty
    def current_state(self):
        pass

    @abstractproperty
    def applicable_actions(self):
        pass    

    @abstractmethod
    def get_reached_goal(self):
        pass

    @abstractmethod
    def get_highest_intents(self, *args, **kwargs):
        pass

    @abstractmethod
    def _update_applicable_actions(self, *args, **kwargs):
        pass

    @abstractmethod
    def update_state(self, *args, **kwargs):
        pass

    @abstractmethod
    def get_action_confidences(self, *args, **kwargs):
        pass

from dataclasses import dataclass
from typing import List, Union
from abc import ABC, abstractmethod


class RolloutBase(ABC):
    @abstractmethod
    def get_reached_goal(self, *args, **kwargs):
        pass

    @abstractmethod
    def get_highest_intents(self, *args, **kwargs):
        pass

    @abstractmethod
    def get_action_confidences(self, *args, **kwargs):
        pass

    @abstractmethod
    def _update_applicable_actions(self, *args, **kwargs):
        pass

    @abstractmethod
    def update_state(self, *args, **kwargs):
        pass

    @abstractmethod
    def update_if_message_action(self, *args, **kwargs):
        pass


class Output:
    """Describes an output, which is either an action or intent. Sorts based on
    cumulative score.
    Args:
        name (str): The name of the output.
        probability (float): The confidence this output occurred.
        beam (int): The beam that the output initially belonged to, which does 
            not change if the beam order/id becomes shifted. This is because 
            the beam attribute is only important at the point where the output
            is chosen so we can add the output to that beam's rankings.

            For example, if an Output from beam 0 is chosen, but this output is
            the second best option, the reconstructed beam will be beam 1, but 
            the Output's beam id will still be 0, indicating which beam the 
            output originated from at that point.
        score (float): The cumulative score of the beam up to and including the
            output.
    """
    def __init__(self, name: str, probability: float, beam: int, score: float):
        self.name = name
        self.probability = probability
        self.beam = beam
        self.score = score

    def __lt__(self, other):
        return self.score > other.score

class Action(Output):
    """Describes an Action."""
    def __init__(self, name: str, probability: float, beam: int, score: float):
        super().__init__(name, probability, beam, score)

class Intent(Output, ABC):
    """Describes an Intent.
    Args:
        outcome (str): The outcome chosen from the intent."""

    def __init__(self, name: str, probability: float, beam: int, score: float, outcome: str):
        super().__init__(name, probability, beam, score)
        self.outcome = outcome

    @abstractmethod
    def is_fallback(self, *args, **kwargs) -> bool:
        """Determines if the provided intent is a fallback.

        Returns:
            bool: True if the intent is a fallback, False otherwise.
        """
        pass

@dataclass
class Beam:
    """Describes a beam.

    Args:
        last_action (Union[Action, None]): The last action that occurred. 
            Can be None upon initiation.
        last_intent (Union[Intent, None]): The last intent that occurred.
            Can be None upon initiation.
        rankings (List[Output]): The list of actions or intents in the beam.
        rollout (RolloutBase): Handles retrieving action and intent 
            confidences, updating the state/applicable actions, etc. This
            stub class should be implemented with functions that reflect your
            particular chatbot.
        scores (List[float]): The list of scores in the beam.
        fallbacks (int): The number of fallbacks that have occurred in the beam
            so far.
    """
    last_action: Union[Action, None]
    last_intent: Union[Intent, None]
    rankings: List[Output]
    rollout: RolloutBase
    scores: List[float]
    fallbacks: int
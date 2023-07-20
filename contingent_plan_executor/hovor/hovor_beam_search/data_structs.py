from dataclasses import dataclass
from typing import List, Optional, Dict
from abc import ABC, abstractmethod


class RolloutBase(ABC):
    """Abstract "rollout" class to be inherited. Houses all the functions that
    calculate action and intent confidences and keep track of + update the
    current state.

    Args:
        ABC (class): Used to create an abstract class.
    """

    @abstractmethod
    def get_reached_goal(self, *args, **kwargs) -> bool:
        """Returns if the beam reached the goal.

        Returns:
            bool: True if the corresponding beam reached the goal, False
            otherwise.
        """
        pass

    @abstractmethod
    def call_outcome_determiner(self, *args, **kwargs) -> List:
        """Calls the outcome determiner of an action.

        Returns:
            List: A list of outcomes ranked by confidence.
        """
        pass

    @abstractmethod
    def get_intent_confidences(self, *args, **kwargs) -> List[Dict]:
        """Returns: (all) the intent confidences that match a user utterance.
        NOTE: Do not just return the k highest intents, because the top k are
        selected based on overall score, not just the singular confidence.

        Returns:
            List[Dict]: The intent/confidence map. Return in the format:

                .. code-block:: python

                    [
                        {
                            "intent": INTENT_NAME (str),
                            "outcome": OUTCOME_NAME (str),
                            "confidence": CONFIDENCE (float)
                        },
                        # continue for each intent
                        {
                            ...
                        }
                    ]
        """
        pass

    @abstractmethod
    def get_action_confidences(self, *args, **kwargs) -> Dict:
        """Returns: (all) the action confidences that match an agent utterance.
        NOTE: Do not just return the k highest actions, because the top k are
        selected based on overall score, not just the singular confidence.

        Returns:
            Dict: The action confidence map. Return in the format:

                .. code-block:: python

                    {
                        ACTION_NAME (str): CONFIDENCE (float),
                        # continue for each action
                        ...
                    }

                NOTE: Insertion order of dictionary values is maintained as of
                Python 3.7.
        """
        pass

    @abstractmethod
    def _update_applicable_actions(self, *args, **kwargs):
        """Updates which actions are applicable in the current state."""
        pass

    @abstractmethod
    def update_state(self, *args, **kwargs):
        """Update the state (including applicable actions, so
        :py:func:`_update_applicable_actions
        <beam_search.beam_srch_data_structs.RolloutBase._update_applicable_actions>`
        should be called here).
        """
        pass

    @abstractmethod
    def update_if_message_action(self, *args, **kwargs) -> Optional[Dict]:
        """Checks if the provided action is a "message" action, meaning it only
        has one outcome. If that's the case, the outcome must be automatically
        executed as it won't take (or need) user input to be determined.
        This execution is already handled within the beam search algorithm; this
        function just needs to return the associated intent. So:

        * Check if the action is a "message" action

           * | If it is, update the state with the single outcome and return a
               single intent in the form

             .. code-block:: python

                {
                    "intent": INTENT_NAME (str),
                    "outcome": OUTCOME_NAME (str),
                    "confidence": CONFIDENCE (float)
                }

        * Otherwise, just return None.

        Returns:
            Optional[Dict]: The associated intent if the action is a "message"
            action; None otherwise.
        """
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
        return self.score.real > other.score.real


class Action(Output):
    """Describes an Action."""

    def __init__(self, name: str, probability: float, beam: int, score: float):
        super().__init__(name, probability, beam, score)


class Intent(Output, ABC):
    """Describes an Intent.

    Args:
        outcome (str): The outcome chosen from the intent.
    """

    def __init__(
        self, name: str, probability: float, beam: int, score: float, outcome: str
    ):
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
        last_action (Optional[Action]): The last action that occurred.
            Can be None upon initiation.
        last_intent (Optional[Intent]): The last intent that occurred.
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

    last_action: Optional[Action]
    last_intent: Optional[Intent]
    rankings: List[Output]
    rollout: RolloutBase
    scores: List[float]
    fallbacks: int

    def __lt__(self, other):
        return sum(self.scores).real > sum(other.scores).real

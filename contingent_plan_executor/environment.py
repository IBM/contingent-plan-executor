from hovor.actions.action_base import ActionBase
from hovor.actions.goal_achieved_action import GoalAchievedAction
from hovor.actions.local_dialogue_action import LocalDialogueAction
from hovor.actions.local_dialogue_action_simulated import LocalDialogueActionSimulated
from hovor.actions.local_info_action import LocalInfoAction
from hovor.actions.dialogue_action import DialogueAction
from hovor.actions.web_action import WebAction


def initialize_local_environment():
    ActionBase.register_action("dialogue", LocalDialogueAction)
    ActionBase.register_action("message", LocalDialogueAction)
    ActionBase.register_action("system", LocalInfoAction)
    ActionBase.register_action("api", WebAction)
    ActionBase.register_action("goal_achieved", GoalAchievedAction)
    ActionBase.register_action("web", LocalInfoAction)

def initialize_local_environment_simulated():
    ActionBase.register_action("dialogue", LocalDialogueActionSimulated)
    ActionBase.register_action("message", LocalDialogueActionSimulated)
    ActionBase.register_action("system", LocalInfoAction)
    ActionBase.register_action("api", WebAction)
    ActionBase.register_action("goal_achieved", GoalAchievedAction)
    ActionBase.register_action("web", LocalInfoAction)
    
def initialize_remote_environment():
    ActionBase.register_action("dialogue", DialogueAction)
    ActionBase.register_action("message", DialogueAction)
    ActionBase.register_action("system", LocalInfoAction)
    ActionBase.register_action("api", WebAction)
    ActionBase.register_action("goal_achieved", GoalAchievedAction)
    ActionBase.register_action("web", LocalInfoAction)

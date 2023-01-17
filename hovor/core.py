from hovor.execution_monitor import EM
from hovor.execution_monitor_simulator import EM_S
from hovor.runtime.action_result import ActionResult
from hovor.runtime.outcome_determination_progress import OutcomeDeterminationProgress
from hovor.session.in_memory_session import InMemorySession
import datetime
import json

def run_interaction(configuration_provider):
    print("RUNNING INTERACTION")
    print("-" * 20 + "\n")

    session = initialize_session(configuration_provider)
    last_execution_result = session.current_action.execute()  # initial action execution

    while True:
        EM(session, last_execution_result)
        # the previous line will loop until there is a system action
        action = session.current_action
        if action is None:
            break

        # external call simulation
        last_execution_result = action.start_execution()
        action.end_execution(last_execution_result)
        if action.action_type == "goal_achieved":
            break

    print("\n" + "-" * 20)
    print("INTERACTION END")

class ConversationLogInterface:
    def write_message(self, entity, message):
        pass
    def write_diologue_pair(self, agent_message=None, user_message=None):
        pass
    def save_conversation_to_file(self, file_path):
        pass

class SimpleTextConversationLog(ConversationLogInterface):
    def __init__(self):
        self.messages = []
    
    def write_message(self, entity, message):
        self.messages.append(f'{entity}: ' + message)

    def write_diologue_pair(self, agent_message=None, user_message=None):
        if agent_message:
            self.messages.append('AGENT: ' + agent_message.replace('HOVOR: ', '', 1)) 
        if user_message:
            self.messages.append('USER: ' + user_message) 

    def save_conversation_to_file(self, file_path):
        if file_path.split('.')[-1]!='txt':
            file_path = file_path + '.txt'

        with open(file_path, "w") as fout:
            fout.writelines([m + '\n' for m in self.messages])

class JsonConversationLog(ConversationLogInterface):
    def __init__(self):
        self.messages = []
    
    def write_message(self, entity, message):
        self.messages.append({
            'entity': entity,
            'message': message
        })

    def write_diologue_pair(self, agent_message=None, user_message=None):
        if agent_message:
            agent_message = agent_message.replace('HOVOR: ', '', 1)
        self.messages.append({
            'agent_message': agent_message,
            'user_message': user_message
        })

    def save_conversation_to_file(self, file_path):
        if file_path.split('.')[-1]!='json':
            file_path = file_path + '.json'

        with open(file_path, "w") as fout:
            json.dump(self.messages, fout)

def simulate_interaction(configuration_provider):
    print("SIMULATING INTERACTION")
    print("-" * 20 + "\n")

    timestamp = datetime.datetime.now()
    str_date_time = timestamp.strftime(r"%d-%m-%Y-%H-%M-%S-%f")
    print("Current timestamp", str_date_time)

    convo_logs = [JsonConversationLog(), SimpleTextConversationLog()]

    session = initialize_session(configuration_provider)
    last_execution_result = session.current_action.execute()  # initial action execution

    if hasattr(session.current_action, '_utterance'):
        agent_message = session.current_action._utterance
    else:
        agent_message = None

    try:
        user_message = last_execution_result._fields['input']
    except KeyError:
        # No user input for this action result. 
        user_message=None
    
    # write the diologue pair to each conversation log
    for convo_log in convo_logs:
        convo_log.write_diologue_pair(agent_message=agent_message, user_message=user_message)

    while True:
        accumulated_messages, _, _, _ = EM_S(session, last_execution_result, convo_logs=convo_logs)
        action = session.current_action
        if action is None:
            break

        # external call simulation
        last_execution_result = action.start_execution()
        action.end_execution(last_execution_result)
        if action.action_type == "goal_achieved":
            break

    print("\n" + "-" * 20)
    print("INTERACTION END")
    for convo_log in convo_logs:
        convo_log.save_conversation_to_file(f'simulated_conversation_{str_date_time}')


def initialize_session(configuration_provider):
    session = InMemorySession(configuration_provider)
    session.load_initial_plan_data()

    initial_result = ActionResult()
    initial_progress = OutcomeDeterminationProgress(session, initial_result)

    for initial_effect in configuration_provider.create_initial_effects():
        # initialization is done via context effects
        initial_progress.run_effect(initial_effect)

    if not initial_progress.is_valid():
        raise AssertionError("Initialization failed.")

    session.update_context_by(initial_progress)

    session.create_initial_action()  # create initial action after the session is fully initialized
    return session

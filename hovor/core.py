from hovor.execution_monitor import EM
from hovor.execution_monitor_simulator import EM_S
from hovor.runtime.action_result import ActionResult
from hovor.runtime.outcome_determination_progress import OutcomeDeterminationProgress
from hovor.session.in_memory_session import InMemorySession
import time
import datetime

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

def simulate_interaction(configuration_provider):
    print("SIMULATING INTERACTION")
    print("-" * 20 + "\n")

    

    timestamp = datetime.datetime.now()
 
    str_date_time = timestamp.strftime(r"%d-%m-%Y-%H-%M-%S-%f")
    print("Current timestamp", str_date_time)

    with open(f'simulated_conversation_{str_date_time}.txt', 'w') as log_out:
        log_out.writelines(['SIMULATING INTERACTION', "-" * 20 + "\n"])

        session = initialize_session(configuration_provider)
        last_execution_result = session.current_action.execute()  # initial action execution

        if hasattr(session.current_action, '_utterance'):
            log_out.write(session.current_action._utterance + '\n')
        try:
            log_out.write(last_execution_result._fields['input'] + '\n')
        except KeyError:
            # No user input for this action result. 
            pass

        while True:
            accumulated_messages, _, _, _ = EM_S(session, last_execution_result, log_out=log_out)
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

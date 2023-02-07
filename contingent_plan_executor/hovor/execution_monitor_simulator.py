from copy import deepcopy

from hovor.runtime.outcome_determination_progress import OutcomeDeterminationProgress
from hovor import DEBUG


def EM_S(session, action_execution_result, convo_logs=[]):
    """
    Top-level execution monitor code that will loop until we have an external
    action execution call to make. We assume that this is entered when a new
    event triggers hovor corresponding to the completion of an action. The
    last action being executed should already have been fetched, and the EM
    can continue from there.

    This version of this function will actually simulate and provide both sides
    of the conversation. 
    """

    is_external_call = False
    accumulated_messages = None

    diagnostics = []

    while not is_external_call:
        # incorporates state/context changes that happend after action execution
        final_progress, confidence = run_outcome_determination(session, action_execution_result)

        # Add the diagnostics required
        diagnostics.append(compute_diagnostic(final_progress, session.current_action, action_execution_result))

        # next we change state accordingly
        action = progress_with_outcome(session, final_progress)

        # We will execute the action and keep going if it does not correspond to
        #  an external call.
        is_external_call = action.is_external

        # if the outcome is foreordained, execute locally and proceed to the next action
        if action.is_deterministic() and action.action_type != "goal_achieved":
            is_external_call = False

        if is_external_call:
            return accumulated_messages, diagnostics, final_progress.final_outcome_name, confidence
        else:
            # here it sends a message back to the user
            action_execution_result = action.execute()

            # Here it should write the utterance from the bot and the response from the simulator
            # using the action._utterance and the action_execution_result.input
            if convo_logs != []:
                if hasattr(action, '_utterance'):
                    agent_message = action._utterance
                else:
                    agent_message = None
                try:
                    user_message = action_execution_result._fields['input']
                except KeyError:
                    # No user input for this action result. 
                    user_message = None
                # write the pair to the log
                for convo_log in convo_logs:
                    convo_log.write_diologue_pair(agent_message=agent_message, user_message=user_message)

            

            # now if it was an action that asked the user for something, the action_execution_result will have the user's response
            # so the code that actually got the user response must be in action.execute()
            if action_execution_result.get_field('type') == 'message':
                if accumulated_messages is None:
                    accumulated_messages = action_execution_result.get_field('msg')
                else:
                    accumulated_messages = accumulated_messages + '\n' + action_execution_result.get_field('msg')



        # If we exit the loop, then we have an external action to execute next (e.g.,
        #  a dialogue message to send back to the user). We assume that the calling
        #  code will handle storing the state and context in the appropriate fashion.


def progress_with_outcome(session, final_progress):
    """
    Updates the state and context given the outcome, and returns the next action
    that should be executed from the plan.
    """

    if not final_progress.is_valid():
        raise ValueError("Invalid progress detected.")

    session.update_by(final_progress)

    #DEBUG("\t session context: %s" % session.get_context_copy())
    return session.current_action


def run_outcome_determination(session, action_execution_result):
    action = session.current_action

    initial_progress = OutcomeDeterminationProgress(session, action_execution_result)
    final_progress, confidence = action.outcome_group.update_progress(initial_progress)

    return final_progress, confidence

def compute_diagnostic(progress, action, action_result):
    import pprint
    monitored_values = progress.collect_monitored_values()
    if monitored_values:
        assert len(monitored_values) == 1, "Need to rethink multiple monitors (see the execution_monitor.py file)"
        diagnostic = deepcopy(monitored_values[0][1])
    else:
        diagnostic = {}
    diagnostic['outcome_name'] = progress.final_outcome_name
    diagnostic['determination_info'] = progress.get_description(progress.final_outcome_name)
    diagnostic['action_result'] = action_result.json
    diagnostic['action'] = action.name

    return diagnostic

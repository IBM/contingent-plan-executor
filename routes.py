# Used just for seeding the initial database
import json
import jsonpickle
import traceback
from json2html import *

from requests.exceptions import HTTPError

from flask import request, jsonify

from werkzeug.routing import RequestRedirect
from werkzeug.exceptions import MethodNotAllowed, NotFound

from hovor.configuration.direct_json_configuration_provider import DirectJsonConfigurationProvider
from hovor.outcome_determiners import ws_action_outcome_determiner_config
from hovor.outcome_determiners.unified_workspace_outcome_determiner import UnifiedWorkspaceOutcomeDeterminer
from hovor.outcome_determiners.workspace_outcome_determiner import WorkspaceOutcomeDeterminer
from remote_main import app
from ibm_cloud_sdk_core.authenticators import IAMAuthenticator
from ibm_watson import AssistantV1

from hovor.wa_deployment.workspace_builder import WorkspaceBuilder

from hovor.execution_monitor import EM

from environment import initialize_remote_environment
from hovor.core import initialize_session
from hovor.session.database_session import DatabaseSession

initialize_remote_environment()

DEFAULT_PLAN = 'plan-Bob'


###################################################################
#
#   WARNING: Do /not/ leave this endpoint uncommented and exposed
#
# @app.route('/setup-database')
def setup_database():
    assert app.db_client

    # Wipe everything. Note that we may have dangling things if there are plans
    #  or traces with no users.
    plans = set()
    if check_db(app.db, 'user-2-plan'):

        user2plan = app.db['user-2-plan']['data']

        for user in user2plan:
            plans.add("plan-%s" % user2plan[user])

            if check_db(app.db, "trace-%s" % user):
                print("Found and purging trace-%s" % user)
                app.db["trace-%s" % user].delete()

        print("Found and purging user-2-plan")
        app.db['user-2-plan'].delete()

    if check_db(app.db, 'plans'):
        for pid in app.db['plans']['data']:
            plans.add("plan-" + pid)

    for pid in plans:
        if check_db(app.db, pid):
            print("Found and purging %s" % pid)
            app.db[pid].delete()

    # Create the user table again
    app.db.create_document({'_id': 'user-2-plan', 'data': {}})

    # Create the default plans to insert
    if check_db(app.db, 'plan-ski'):
        print("Found and purging plan-ski")
        app.db['plan-ski'].delete()

    # Create the plans entry
    if check_db(app.db, 'plans'):
        app.db['plans'].delete()
    app.db.create_document({'_id': 'plans', 'data': []})

    # Delete all workspaces created with the local prefix
    # If ALL workspaces need to be deleted, change cache_only to False
    cache_only = True
    print("Deleting workspaces in mode: cache_only=" + str(cache_only))
    for id in WorkspaceOutcomeDeterminer.get_workspace_ids(cache_only):
        WorkspaceOutcomeDeterminer.delete_workspace(id)

    return "Database configured."


@app.route('/deploy-to-wa/<pid>', methods=['POST'])
def deploy_to_wa(pid):
    if app.db_client:

        configuration = request.get_json()

        full_plan_id = configuration['bot_name']

        if check_db(app.db, 'plan-' + full_plan_id):
            try:

                app.db['plan-' + full_plan_id].fetch()
                plan_json_config = app.db['plan-' + full_plan_id]['data']
                plan_config = DirectJsonConfigurationProvider(full_plan_id,
                                                              plan_json_config['hovor_config'],
                                                              plan_json_config['plan_config'])
                plan_config.check_all_action_builders()

                api = configuration['api']
                key = configuration['key']

                builder = WorkspaceBuilder('MAI_Workspace ' + pid, api, key)
                builder.deploy(plan_config)

            except Exception as e:
                debug_str = ''.join(traceback.format_exception(etype=type(e), value=e, tb=e.__traceback__))
                print(debug_str)
                return jsonify({'status': 'error', 'msg': "Delpoy failed: %s" % str(e), 'debug': debug_str})

            return jsonify({'status': 'success', 'msg': 'Some magic just happened.'})
        else:
            return jsonify({'status': 'error', 'msg': "Plan %s does not exist" % pid})
    else:
        return jsonify({'status': 'error', 'msg': 'No database client!'})


@app.route('/assign-plan', methods=['POST'])
def assign_plan():
    if app.db_client:

        configuration = request.get_json()
        if 'user' not in configuration or 'plan' not in configuration:
            return jsonify({'status': 'error', 'msg': "Must specify both 'user' and 'plan'."})

        uid = configuration['user']
        pid = configuration['plan']

        if check_db(app.db, 'plan-' + pid):
            user2plan = app.db['user-2-plan']
            user2plan['data'][uid] = 'plan-' + pid
            user2plan.save()

            return jsonify({'status': 'success', 'msg': "User %s assigned to use plan %s." % (uid, pid)})

        else:
            return jsonify({'status': 'error', 'msg': "Plan %s does not exist." % pid})


# allow for the remote chat to initialize the message
@app.route('/new-conversation', methods=['POST'])
def new_conversation():
    if app.db_client:
        UnifiedWorkspaceOutcomeDeterminer.train_wa_flag = False
        try:

            # We assume that we only have one trace per user
            input_data = request.get_json()
            user_id = input_data['user']
            trace_id = "trace-%s" % user_id

            # Check what plan should be used, and assign one by default if not specified already
            user2plan = app.db['user-2-plan']
            if user_id not in user2plan['data']:
                print("Adding %s to user2plan table" % user_id)
                user2plan['data'][user_id] = DEFAULT_PLAN
                user2plan.save()
            plan_id = user2plan['data'][user_id]
            plan_json_config = app.db[plan_id]['data']
            plan_config = DirectJsonConfigurationProvider(plan_id,
                                                          plan_json_config['hovor_config'],
                                                          plan_json_config['plan_config'])

            # assign WA workspace credentials to system
            assign_wa_credentials(plan_json_config)

            plan_config.check_all_action_builders()

            print("Plan fetched.")

            # If the trace already exists, we delete it first
            if check_db(app.db, trace_id):
                app.db[trace_id].delete()

            print("Creating a new trace.")
            temp_session = initialize_session(plan_config)
            action = temp_session.current_action

            need_to_execute = (not action.is_external) or (
                    action.is_deterministic() and action.action_type != "goal_achieved")
            action_result = action.start_execution()  # initial action execution

            trace_data = {
                '_id': trace_id,
                'plan': plan_id,
                'state': jsonpickle.encode(temp_session.current_state),
                'action': jsonpickle.encode(temp_session.current_action),
                'action_result': jsonpickle.encode(action_result),
                'context': jsonpickle.encode(temp_session.get_context_copy()),
                'node_id': plan_config.plan.get_initial_node().node_id,
                'history': [prog.json for prog in temp_session.delta_history]
            }
            app.db.create_document(trace_data)

            original_message = action_result.get_field('msg')

            # Something that is blocking and internal (like a web api call)
            new_accumulated_messages = None
            diagnostics = []
            if need_to_execute:
                action.end_execution(action_result)
                # Need to run the EM here until we are ready for external input
                session = DatabaseSession(app.db, trace_id, plan_config)
                new_accumulated_messages, diagnostics, outcome_name, confidence = EM(session, action_result)
                action = session.current_action

            # Need to jump through some hoops to keep things consistent
            accumulated_messages = ''
            if original_message is not None:
                accumulated_messages += original_message
            if new_accumulated_messages is not None:
                accumulated_messages += '\n' + new_accumulated_messages
            if accumulated_messages == '':
                accumulated_messages = None

            if (action is None) or (action.action_type == "goal_achieved"):
                # If the goal is achieved, then we kill the session (so a new one can begin)
                app.db[trace_id].delete()
                if accumulated_messages is None:
                    return jsonify({'status': "Plan complete!"})
                else:
                    return jsonify(
                        {'status': "Plan complete!", 'msg': accumulated_messages, 'diagnostics': diagnostics})

            if need_to_execute:
                action_result = action.start_execution()

                if accumulated_messages is not None:
                    msg = action_result.get_field('msg')
                    if msg is None:
                        action_result.set_field('msg', accumulated_messages)
                    else:
                        action_result.set_field('msg', accumulated_messages + '\n' + msg)

                session.update_action_result(action_result)

                # Update the trace state in the database
                session.save(app.db, trace_id)

            if action_result is None:
                print("No execution result to return.")
                return jsonify({'status': 'success', 'msg': 'All set!'})
            if action_result.get_field('type') == 'message':
                print("Returning message: %s" % action_result.get_field('msg'))
                return jsonify({'status': 'success',
                                'msg': action_result.get_field('msg'),
                                'diagnostics': diagnostics})
            else:
                print("Not sure what to do with action of type %s\n%s" % (action_result.get_field('type'),
                                                                          str(action_result)))
                return jsonify({'status': 'error',
                                'msg': "Received unknown action type of %s" % action_result.get_field('type'),
                                'debug': action_result.json})

        except Exception as e:
            debug_str = ''.join(traceback.format_exception(etype=type(e), value=e, tb=e.__traceback__))
            print(debug_str)
            return jsonify({'status': 'error', 'msg': "New conversation failed: %s" % str(e), 'debug': debug_str})

    else:
        return jsonify({'status': 'error', 'msg': 'No database client!'})


# check on the training
@app.route('/training-complete', methods=['GET', 'POST'])
def check_training():
    if app.db_client:
        UnifiedWorkspaceOutcomeDeterminer.train_wa_flag = False

        try:
            # We assume that we only have one trace per user
            input_data = request.get_json()
            plan_id = 'plan-' + input_data['plan']
            plan_json_config = app.db[plan_id]['data']
            plan_config = DirectJsonConfigurationProvider(plan_id,
                                                          plan_json_config['hovor_config'],
                                                          plan_json_config['plan_config'])

            # assign WA workspace credentials to system
            assign_wa_credentials(plan_json_config)

            plan_config.check_all_action_builders()

            trained, total_workspaces, status = plan_config.training_done()

            return jsonify({'status': 'success',
                            'training_complete': status,
                            'trained': trained,
                            'total_workspaces': total_workspaces})

        except Exception as e:
            debug_str = ''.join(traceback.format_exception(etype=type(e), value=e, tb=e.__traceback__))
            print(debug_str)
            return jsonify(
                {'status': 'error', 'msg': "Checking training failed for plan: %s" % str(e), 'debug': debug_str})

    else:
        return jsonify({'status': 'error', 'msg': 'No database client!'})


# entrypoint to execution monitor.
@app.route('/new-message', methods=['POST'])
def new_message():
    if app.db_client:
        UnifiedWorkspaceOutcomeDeterminer.train_wa_flag = False
        try:
            # We assume that we only have one trace per user
            input_data = request.get_json()
            user_id = input_data['user']
            trace_id = "trace-%s" % user_id

            # Check what plan should be used, and assign one by default if not specified already
            user2plan = app.db['user-2-plan']
            if user_id not in user2plan['data']:
                print("Adding %s to user2plan table" % user_id)
                user2plan['data'][user_id] = DEFAULT_PLAN
                user2plan.save()
            plan_id = user2plan['data'][user_id]
            plan_json_config = app.db[plan_id]['data']
            plan_config = DirectJsonConfigurationProvider(plan_id,
                                                          plan_json_config['hovor_config'],
                                                          plan_json_config['plan_config'])

            # assign WA workspace credentials to system
            assign_wa_credentials(plan_json_config)

            plan_config.check_all_action_builders()

            print("Plan fetched.")

            # If the trace doesn't already exist, we create it with an empty session
            if not check_db(app.db, trace_id):
                print("Creating a new trace.")
                print("WARNING: This probably shouldn't be happening anymore.")
                print("         New messages should come after new conversations.")
                temp_session = initialize_session(plan_config)
                temp_result = temp_session.current_action.start_execution()  # initial action execution
                trace_data = {
                    '_id': trace_id,
                    'plan': plan_id,
                    'state': jsonpickle.encode(temp_session.current_state),
                    'action': jsonpickle.encode(temp_session.current_action),
                    'action_result': jsonpickle.encode(temp_result),
                    'context': jsonpickle.encode(temp_session.get_context_copy()),
                    'node_id': plan_config.plan.get_initial_node().node_id,
                    'history': [prog.json for prog in temp_session.delta_history]
                }
                app.db.create_document(trace_data)

            # Load up the existing session
            session = DatabaseSession(app.db, trace_id, plan_config)
            action = session.current_action
            result = session.current_action_result
            action.end_execution(result, input_data['msg'])

            # used for d3ba blackbox integration
            previous_action = action.name

            # Execute!
            accumulated_messages, diagnostics, final_outcome_name, confidence = EM(session, result)
            action = session.current_action

            if (action is None) or (action.action_type == "goal_achieved"):
                # If the goal is achieved, then we kill the session (so a new one can begin)
                app.db[trace_id].delete()
                if accumulated_messages is None:
                    return jsonify({'status': 'Plan Complete',
                                    'action_name': previous_action,
                                    'outcome_name': final_outcome_name,
                                    'confidence': confidence,
                                    'stickiness': 0})
                    # return jsonify({'status': "Plan complete!"})
                else:
                    return jsonify({'status': "Plan complete!",
                                    'action_name': previous_action,
                                    'outcome_name': final_outcome_name,
                                    'confidence': confidence,
                                    'stickiness': 0,
                                    'msg': accumulated_messages,
                                    'diagnostics': diagnostics})

            last_execution_result = action.start_execution()

            if accumulated_messages is not None:
                msg = last_execution_result.get_field('msg')
                if msg is None:
                    last_execution_result.set_field('msg', accumulated_messages)
                else:
                    last_execution_result.set_field('msg', accumulated_messages + '\n' + msg)

            session.update_action_result(last_execution_result)

            # Update the trace state in the database
            session.save(app.db, trace_id)

        except Exception as e:
            debug_str = ''.join(traceback.format_exception(etype=type(e), value=e, tb=e.__traceback__))
            print(debug_str)
            return jsonify({'status': 'error', 'msg': "New message failed: %s" % str(e), 'debug': debug_str})

        if last_execution_result is None:
            print("No execution result to return.")
            return jsonify({'status': 'success',
                            'action_name': previous_action,
                            'outcome_name': final_outcome_name,
                            'confidence': confidence,
                            'stickiness': 1, 'msg': 'All set!'})
        if last_execution_result.get_field('type') == 'message':
            print("Returning message: %s" % last_execution_result.get_field('msg'))
            return jsonify({'status': 'success',
                            'action_name': previous_action,
                            'outcome_name': final_outcome_name,
                            'confidence': confidence,
                            'stickiness': 1,
                            'msg': last_execution_result.get_field('msg'),
                            'diagnostics': diagnostics})
        else:
            print("Not sure what to do with action of type %s\n%s" % (last_execution_result.get_field('type'),
                                                                      str(last_execution_result)))
            return jsonify({'status': 'error',
                            'msg': "Received unknown action type of %s" % last_execution_result.get_field('type'),
                            'debug': last_execution_result.json})

    else:
        return jsonify({'status': 'error', 'msg': 'No database client!'})


@app.route('/preview', methods=['POST'])
def preview():
    if app.db_client:
        UnifiedWorkspaceOutcomeDeterminer.train_wa_flag = False
        try:
            # We assume that we only have one trace per user
            input_data = request.get_json()
            user_id = input_data['user']
            trace_id = "trace-%s" % user_id

            # Check what plan should be used, and assign one by default if not specified already
            user2plan = app.db['user-2-plan']
            if user_id not in user2plan['data']:
                print("Adding %s to user2plan table" % user_id)
                user2plan['data'][user_id] = DEFAULT_PLAN
                user2plan.save()
            plan_id = user2plan['data'][user_id]
            plan_json_config = app.db[plan_id]['data']
            plan_config = DirectJsonConfigurationProvider(plan_id,
                                                          plan_json_config['hovor_config'],
                                                          plan_json_config['plan_config'])
            plan_config.check_all_action_builders()

            print("Plan fetched.")

            # If the trace doesn't already exist, we create it with an empty session
            if not check_db(app.db, trace_id):
                print("Creating a new trace.")
                print("WARNING: This probably shouldn't be happening anymore.")
                print("         New messages should come after new conversations.")
                temp_session = initialize_session(plan_config)
                temp_result = temp_session.current_action.start_execution()  # initial action execution
                trace_data = {
                    '_id': trace_id,
                    'plan': plan_id,
                    'state': jsonpickle.encode(temp_session.current_state),
                    'action': jsonpickle.encode(temp_session.current_action),
                    'action_result': jsonpickle.encode(temp_result),
                    'context': jsonpickle.encode(temp_session.get_context_copy()),
                    'node_id': plan_config.plan.get_initial_node().node_id,
                    'history': [prog.json for prog in temp_session.delta_history]
                }
                app.db.create_document(trace_data)

            # Load up the existing session
            session = DatabaseSession(app.db, trace_id, plan_config)
            action = session.current_action
            result = session.current_action_result
            action.end_execution(result, input_data['msg'])

            # used for d3ba blackbox integration
            previous_action = action.name

            # Execute!
            accumulated_messages, diagnostics, final_outcome_name, confidence = EM(session, result)
            action = session.current_action

            # TODO: simplify this if-else statement.
            if (action is None) or (action.action_type == "goal_achieved"):
                # If the goal is achieved, then we return
                if accumulated_messages is None:
                    return jsonify({'status': 'Plan Complete',
                                    'action_name': previous_action,
                                    'outcome_name': final_outcome_name,
                                    'confidence': confidence,
                                    'stickiness': 0})
                    # return jsonify({'status': "Plan complete!"})
                else:
                    return jsonify({'status': "Plan complete!",
                                    'action_name': previous_action,
                                    'outcome_name': final_outcome_name,
                                    'confidence': confidence,
                                    'stickiness': 0,
                                    'msg': accumulated_messages,
                                    'diagnostics': diagnostics})

            last_execution_result = action.start_execution()

            if accumulated_messages is not None:
                msg = last_execution_result.get_field('msg')
                if msg is None:
                    last_execution_result.set_field('msg', accumulated_messages)
                else:
                    last_execution_result.set_field('msg', accumulated_messages + '\n' + msg)

            session.update_action_result(last_execution_result)

        except Exception as e:
            debug_str = ''.join(traceback.format_exception(etype=type(e), value=e, tb=e.__traceback__))
            print(debug_str)
            return jsonify({'status': 'error', 'msg': "Preview failed: %s" % str(e), 'debug': debug_str})

        if last_execution_result is None:
            print("No execution result to return.")
            return jsonify({'status': 'success',
                            'action_name': previous_action,
                            'outcome_name': final_outcome_name,
                            'confidence': confidence,
                            'stickiness': 1, 'msg': 'All set!'})
        if last_execution_result.get_field('type') == 'message':
            print("Returning message: %s" % last_execution_result.get_field('msg'))
            return jsonify({'status': 'success',
                            'action_name': previous_action,
                            'outcome_name': final_outcome_name,
                            'confidence': confidence,
                            'stickiness': 1,
                            'msg': last_execution_result.get_field('msg'),
                            'diagnostics': diagnostics})
        else:
            print("Not sure what to do with action of type %s\n%s" % (last_execution_result.get_field('type'),
                                                                      str(last_execution_result)))
            return jsonify({'status': 'error',
                            'msg': "Received unknown action type of %s" % last_execution_result.get_field('type'),
                            'debug': last_execution_result.json})

    else:
        return jsonify({'status': 'error', 'msg': 'No database client!'})


#############################################################
########       DBA Stuff
#############################################################

# allow for the remote chat to initialize the message
@app.route('/new-conversation-dba', methods=['POST'])
def new_conversation_dba():
    if app.db_client:
        UnifiedWorkspaceOutcomeDeterminer.train_wa_flag = False
        try:

            input_data = request.get_json()
            plan_id = 'plan-' + input_data['plan_id']
            user_id = input_data['user'] + '-' + plan_id
            trace_id = "trace-%s" % user_id

            # plan needs to exist in db
            if not check_db(app.db, plan_id):
                return jsonify({'status': 'error', 'msg': 'plan %s doesnt exist' % plan_id, 'confidence': 0})

            # Check what plan should be used
            user2plan = app.db['user-2-plan']
            if user_id not in user2plan['data']:
                print("Adding %s to user2plan table" % user_id)
                user2plan['data'][user_id] = plan_id
                user2plan.save()
            plan_id = user2plan['data'][user_id]
            plan_json_config = app.db[plan_id]['data']
            plan_config = DirectJsonConfigurationProvider(plan_id,
                                                          plan_json_config['hovor_config'],
                                                          plan_json_config['plan_config'])

            # assign WA workspace credentials to system
            assign_wa_credentials(plan_json_config)

            plan_config.check_all_action_builders()

            print("Plan fetched.")

            # If the trace already exists, we delete it first
            if check_db(app.db, trace_id):
                app.db[trace_id].delete()

            print("Creating a new trace.")
            temp_session = initialize_session(plan_config)
            action = temp_session.current_action

            need_to_execute = (not action.is_external) or (
                    action.is_deterministic() and action.action_type != "goal_achieved")
            action_result = action.start_execution()  # initial action execution

            trace_data = {
                '_id': trace_id,
                'plan': plan_id,
                'state': jsonpickle.encode(temp_session.current_state),
                'action': jsonpickle.encode(temp_session.current_action),
                'action_result': jsonpickle.encode(action_result),
                'context': jsonpickle.encode(temp_session.get_context_copy()),
                'node_id': plan_config.plan.get_initial_node().node_id,
                'history': [prog.json for prog in temp_session.delta_history]
            }
            app.db.create_document(trace_data)

            original_message = action_result.get_field('msg')

            # Something that is blocking and internal (like a web api call)
            new_accumulated_messages = None
            diagnostics = []
            if need_to_execute:
                action.end_execution(action_result)
                # Need to run the EM here until we are ready for external input
                session = DatabaseSession(app.db, trace_id, plan_config)
                new_accumulated_messages, diagnostics = EM(session, action_result)
                action = session.current_action

            # Need to jump through some hoops to keep things consistent
            accumulated_messages = ''
            if original_message is not None:
                accumulated_messages += original_message
            if new_accumulated_messages is not None:
                accumulated_messages += '\n' + new_accumulated_messages
            if accumulated_messages == '':
                accumulated_messages = None

            if (action is None) or (action.action_type == "goal_achieved"):
                # If the goal is achieved, then we kill the session (so a new one can begin)
                app.db[trace_id].delete()
                if accumulated_messages is None:
                    return jsonify({'status': "Plan complete!"})
                else:
                    return jsonify(
                        {'status': "Plan complete!", 'msg': accumulated_messages, 'diagnostics': diagnostics})

            if need_to_execute:
                action_result = action.start_execution()

                if accumulated_messages is not None:
                    msg = action_result.get_field('msg')
                    if msg is None:
                        action_result.set_field('msg', accumulated_messages)
                    else:
                        action_result.set_field('msg', accumulated_messages + '\n' + msg)

                session.update_action_result(action_result)

                # Update the trace state in the database
                session.save(app.db, trace_id)

            if action_result is None:
                print("No execution result to return.")
                return jsonify({'status': 'success', 'msg': 'All set!'})
            if action_result.get_field('type') == 'message':
                print("Returning message: %s" % action_result.get_field('msg'))
                return jsonify({'status': 'success',
                                'msg': action_result.get_field('msg'),
                                'diagnostics': diagnostics})
            else:
                print("Not sure what to do with action of type %s\n%s" % (action_result.get_field('type'),
                                                                          str(action_result)))
                return jsonify({'status': 'error',
                                'msg': "Received unknown action type of %s" % action_result.get_field('type'),
                                'debug': action_result.json})

        except Exception as e:
            debug_str = ''.join(traceback.format_exception(etype=type(e), value=e, tb=e.__traceback__))
            print(debug_str)
            return jsonify({'status': 'error', 'msg': "New conversation failed: %s" % str(e), 'debug': debug_str})

    else:
        return jsonify({'status': 'error', 'msg': 'No database client!'})


@app.route('/preview-dba', methods=['POST'])
def preview_dba():
    if app.db_client:
        UnifiedWorkspaceOutcomeDeterminer.train_wa_flag = False
        try:
            input_data = request.get_json()
            plan_id = 'plan-' + input_data['plan_id']
            user_id = input_data['user'] + '-' + plan_id
            trace_id = "trace-%s" % user_id

            # plan needs to exist in db
            if not check_db(app.db, plan_id):
                return jsonify({'status': 'error', 'msg': 'plan %s doesnt exist' % plan_id, 'confidence': 0})

            # Check what plan should be used
            user2plan = app.db['user-2-plan']
            if user_id not in user2plan['data']:
                print("Adding %s to user2plan table" % user_id)
                user2plan['data'][user_id] = plan_id
                user2plan.save()
            plan_id = user2plan['data'][user_id]
            plan_json_config = app.db[plan_id]['data']
            plan_config = DirectJsonConfigurationProvider(plan_id,
                                                          plan_json_config['hovor_config'],
                                                          plan_json_config['plan_config'])
            plan_config.check_all_action_builders()

            print("Plan fetched.")

            # If the trace doesn't already exist, we create it with an empty session
            if not check_db(app.db, trace_id):
                print("Creating a new trace.")
                print("WARNING: This probably shouldn't be happening anymore.")
                print("         New messages should come after new conversations.")
                temp_session = initialize_session(plan_config)
                temp_result = temp_session.current_action.start_execution()  # initial action execution
                trace_data = {
                    '_id': trace_id,
                    'plan': plan_id,
                    'state': jsonpickle.encode(temp_session.current_state),
                    'action': jsonpickle.encode(temp_session.current_action),
                    'action_result': jsonpickle.encode(temp_result),
                    'context': jsonpickle.encode(temp_session.get_context_copy()),
                    'node_id': plan_config.plan.get_initial_node().node_id,
                    'history': [prog.json for prog in temp_session.delta_history]
                }
                app.db.create_document(trace_data)

            # Load up the existing session
            session = DatabaseSession(app.db, trace_id, plan_config)
            action = session.current_action
            result = session.current_action_result
            action.end_execution(result, input_data['msg'])

            # used for d3ba blackbox integration
            previous_action = action.name

            # Execute!
            accumulated_messages, diagnostics, final_outcome_name, confidence = EM(session, result)
            action = session.current_action

            # TODO: simplify this if-else statement.
            if (action is None) or (action.action_type == "goal_achieved"):
                # If the goal is achieved, then we return
                if accumulated_messages is None:
                    return jsonify({'status': 'Plan Complete',
                                    'action_name': previous_action,
                                    'outcome_name': final_outcome_name,
                                    'confidence': confidence,
                                    'stickiness': 0})
                    # return jsonify({'status': "Plan complete!"})
                else:
                    return jsonify({'status': "Plan complete!",
                                    'action_name': previous_action,
                                    'outcome_name': final_outcome_name,
                                    'confidence': confidence,
                                    'stickiness': 0,
                                    'msg': accumulated_messages,
                                    'diagnostics': diagnostics})

            last_execution_result = action.start_execution()

            if accumulated_messages is not None:
                msg = last_execution_result.get_field('msg')
                if msg is None:
                    last_execution_result.set_field('msg', accumulated_messages)
                else:
                    last_execution_result.set_field('msg', accumulated_messages + '\n' + msg)

            session.update_action_result(last_execution_result)

        except Exception as e:
            debug_str = ''.join(traceback.format_exception(etype=type(e), value=e, tb=e.__traceback__))
            print(debug_str)
            return jsonify({'status': 'error', 'msg': "Preview failed: %s" % str(e), 'debug': debug_str})

        if last_execution_result is None:
            print("No execution result to return.")
            return jsonify({'status': 'success',
                            'action_name': previous_action,
                            'outcome_name': final_outcome_name,
                            'confidence': confidence,
                            'stickiness': 1, 'msg': 'All set!'})
        if last_execution_result.get_field('type') == 'message':
            print("Returning message: %s" % last_execution_result.get_field('msg'))
            return jsonify({'status': 'success',
                            'action_name': previous_action,
                            'outcome_name': final_outcome_name,
                            'confidence': confidence,
                            'stickiness': 1,
                            'msg': last_execution_result.get_field('msg'),
                            'diagnostics': diagnostics})
        else:
            print("Not sure what to do with action of type %s\n%s" % (last_execution_result.get_field('type'),
                                                                      str(last_execution_result)))
            return jsonify({'status': 'error',
                            'msg': "Received unknown action type of %s" % last_execution_result.get_field('type'),
                            'debug': last_execution_result.json})

    else:
        return jsonify({'status': 'error', 'msg': 'No database client!'})


# entrypoint to execution monitor.
@app.route('/new-message-dba', methods=['POST'])
def new_message_dba():
    if app.db_client:
        UnifiedWorkspaceOutcomeDeterminer.train_wa_flag = False
        try:
            input_data = request.get_json()
            plan_id = 'plan-' + input_data['plan_id']
            user_id = input_data['user'] + '-' + plan_id
            trace_id = "trace-%s" % user_id

            # plan needs to exist in db
            if not check_db(app.db, plan_id):
                return jsonify({'status': 'error', 'msg': 'plan %s doesnt exist' % plan_id, 'confidence': 0})

            # Check what plan should be used
            user2plan = app.db['user-2-plan']
            if user_id not in user2plan['data']:
                print("Adding %s to user2plan table" % user_id)
                user2plan['data'][user_id] = plan_id
                user2plan.save()
            plan_id = user2plan['data'][user_id]
            plan_json_config = app.db[plan_id]['data']
            plan_config = DirectJsonConfigurationProvider(plan_id,
                                                          plan_json_config['hovor_config'],
                                                          plan_json_config['plan_config'])

            # assign WA workspace credentials to system
            assign_wa_credentials(plan_json_config)

            plan_config.check_all_action_builders()

            print("Plan fetched.")

            # If the trace doesn't already exist, we create it with an empty session
            if not check_db(app.db, trace_id):
                print("Creating a new trace.")
                print("WARNING: This probably shouldn't be happening anymore.")
                print("         New messages should come after new conversations.")
                temp_session = initialize_session(plan_config)
                temp_result = temp_session.current_action.start_execution()  # initial action execution
                trace_data = {
                    '_id': trace_id,
                    'plan': plan_id,
                    'state': jsonpickle.encode(temp_session.current_state),
                    'action': jsonpickle.encode(temp_session.current_action),
                    'action_result': jsonpickle.encode(temp_result),
                    'context': jsonpickle.encode(temp_session.get_context_copy()),
                    'node_id': plan_config.plan.get_initial_node().node_id,
                    'history': [prog.json for prog in temp_session.delta_history]
                }
                app.db.create_document(trace_data)

            # Load up the existing session
            session = DatabaseSession(app.db, trace_id, plan_config)
            action = session.current_action
            result = session.current_action_result
            action.end_execution(result, input_data['msg'])

            # used for d3ba blackbox integration
            previous_action = action.name

            # Execute!
            accumulated_messages, diagnostics, final_outcome_name, confidence = EM(session, result)
            action = session.current_action

            if (action is None) or (action.action_type == "goal_achieved"):
                # If the goal is achieved, then we kill the session (so a new one can begin)
                app.db[trace_id].delete()
                if accumulated_messages is None:
                    return jsonify({'status': 'Plan Complete',
                                    'action_name': previous_action,
                                    'outcome_name': final_outcome_name,
                                    'confidence': confidence,
                                    'stickiness': 0})
                    # return jsonify({'status': "Plan complete!"})
                else:
                    return jsonify({'status': "Plan complete!",
                                    'action_name': previous_action,
                                    'outcome_name': final_outcome_name,
                                    'confidence': confidence,
                                    'stickiness': 0,
                                    'msg': accumulated_messages,
                                    'diagnostics': diagnostics})

            last_execution_result = action.start_execution()

            if accumulated_messages is not None:
                msg = last_execution_result.get_field('msg')
                if msg is None:
                    last_execution_result.set_field('msg', accumulated_messages)
                else:
                    last_execution_result.set_field('msg', accumulated_messages + '\n' + msg)

            session.update_action_result(last_execution_result)

            # Update the trace state in the database
            session.save(app.db, trace_id)

        except Exception as e:
            debug_str = ''.join(traceback.format_exception(etype=type(e), value=e, tb=e.__traceback__))
            print(debug_str)
            return jsonify({'status': 'error', 'msg': "New message failed: %s" % str(e), 'debug': debug_str})

        if last_execution_result is None:
            print("No execution result to return.")
            return jsonify({'status': 'success',
                            'action_name': previous_action,
                            'outcome_name': final_outcome_name,
                            'confidence': confidence,
                            'stickiness': 1, 'msg': 'All set!'})
        if last_execution_result.get_field('type') == 'message':
            print("Returning message: %s" % last_execution_result.get_field('msg'))
            return jsonify({'status': 'success',
                            'action_name': previous_action,
                            'outcome_name': final_outcome_name,
                            'confidence': confidence,
                            'stickiness': 1,
                            'msg': last_execution_result.get_field('msg'),
                            'diagnostics': diagnostics})
        else:
            print("Not sure what to do with action of type %s\n%s" % (last_execution_result.get_field('type'),
                                                                      str(last_execution_result)))
            return jsonify({'status': 'error',
                            'msg': "Received unknown action type of %s" % last_execution_result.get_field('type'),
                            'debug': last_execution_result.json})

    else:
        return jsonify({'status': 'error', 'msg': 'No database client!'})


@app.route('/plan/<pid>', methods=['PUT'])
def add_plan(pid):
    if app.db_client:
        UnifiedWorkspaceOutcomeDeterminer.train_wa_flag = True
        ws_action_outcome_determiner_config.clear()
        try:
            data = request.get_json()
            wa_credentials = data['wa_credentials']
            hovor_config = data["config"]
            plan = data["plan"]["plan"]

            configuration = {'wa_credentials': wa_credentials, 'hovor_config': hovor_config, 'plan_config': plan}

            if check_db(app.db, 'plan-' + pid):
                action = 'replaced'
                plan = app.db['plan-' + pid]
                plan['data'] = configuration
                plan.save()
            else:
                action = 'added'
                app.db.create_document({'_id': 'plan-' + pid, 'data': configuration})
                plans = app.db['plans']
                plans['data'].append(pid)
                plans.save()

        except Exception as e:
            debug_str = ''.join(traceback.format_exception(etype=type(e), value=e, tb=e.__traceback__))
            print(debug_str)
            return jsonify({'status': 'error', 'msg': "Plan creation failed: %s" % str(e), 'debug': debug_str})

        try:
            plan_id = 'plan-' + pid
            plan_json_config = app.db['plan-' + pid]['data']
            plan_config = DirectJsonConfigurationProvider(plan_id,
                                                          plan_json_config['hovor_config'],
                                                          plan_json_config['plan_config'])

            # assign WA workspace credentials to system
            assign_wa_credentials(plan_json_config)

            plan_config.check_all_action_builders()
        except Exception as e:
            debug_str = ''.join(traceback.format_exception(etype=type(e), value=e, tb=e.__traceback__))
            return jsonify(
                {'status': 'error', 'msg': "Start of training failed for plan: %s" % str(e), 'debug': debug_str})

        return jsonify({'status': 'success', 'msg': "Plan %s and Training started" % action})

    else:
        return jsonify({'status': 'error', 'msg': 'No database client!'})


@app.route('/plans')
def get_plans():
    if app.db_client:
        plans = set()
        missing = set()
        if check_db(app.db, 'plans'):
            plans = set(app.db['plans']['data'])
            print("Found plans: %s" % plans)

        # for pid in plans:
        #     if not check_db(app.db, "plan-"+pid):
        #         print("Missing db entry for %s" % pid)
        #         missing.add(pid)

        plan_json = {'plans': [pid for pid in (plans - missing)]}
        return jsonify({'status': 'success', 'status_desc': 'plans returned successfully', 'data': plan_json})
    else:
        return jsonify({'status': 'error', 'status_desc': 'No database client!'})


######################################################################
#                                                                    #
#    OUTPUT: plan json expected by hovor-frontend                    #
#                                                                    #
#    DESCRIPTION: This endpoint uses the pickeled                    #
#                 plan stored in db and creates a json               #
#                 which will be used by hovor-frontend to display it #
#                                                                    #
######################################################################
@app.route('/plan/<pid>')
def get_plan(pid):
    if app.db_client:

        app.db['plan-' + pid].fetch()
        configuration = app.db['plan-' + pid]['data']
        plan_config = DirectJsonConfigurationProvider(pid, configuration['hovor_config'], configuration['plan_config'])
        print('plan fetched!')

        nodes_json_array = []
        for node in plan_config.plan.nodes:
            node_json = {'id': node.node_id,
                         'info': plan_config.get_node_info(node),
                         'scope': plan_config.get_node_type(node)}

            # Hack to handle negative node id's, which signify a failed node.
            if isinstance(node.node_id, str) and '-' == node.node_id[0]:
                node_json['scope'] = 'fail'

            if node.is_initial:
                node_json['type'] = 'root'
            elif node.is_goal:
                node_json['type'] = 'goal'
            else:
                node_json['type'] = 'regular'
            nodes_json_array.append(node_json)

        edge_json_array = []
        for edge in plan_config.plan.edges:
            edge_json = {'id': edge.edge_id,
                         'from': edge.src.node_id,
                         'to': edge.dst.node_id,
                         'intent': edge.outcome_id,
                         'info': edge.info}
            edge_json_array.append(edge_json)

        plan_json = {'plan': {'globalNodes': nodes_json_array, 'globalEdges': edge_json_array, 'id': pid}}
        return jsonify({'status': 'success', 'status_desc': 'plan returned successfully', 'data': plan_json})
    else:
        return jsonify({'status': 'error', 'status_desc': 'No database client!'})


@app.route('/trace/<user_id>')
def get_trace(user_id):
    if app.db_client:

        if check_db(app.db, 'trace-' + user_id):
            trace = app.db['trace-' + user_id]
            trace.fetch()
            data = {'trace': trace['history'],
                    'id': user_id,
                    'version': trace['_rev']}
            print("Trace fetched.")
            return jsonify({'status': 'success', 'status_desc': 'trace returned successfully', 'data': data})
        else:
            return jsonify({'status': 'error', 'status_desc': 'trace does not exist'})

    else:
        return jsonify({'status': 'error', 'status_desc': 'No database client!'})


################################################################################
################################################################################


@app.route('/html-debug/<path:endpoint>')
def html_debug(endpoint):
    ''' Pretty prints json to HTML'''

    (endpoint_func, args) = get_view_function('/' + endpoint)

    if not endpoint_func:
        return "Error: The endpoint /%s doesn't seem to exist." % endpoint
    elif len(args) != 0:
        return json2html.convert(json=json.loads(endpoint_func(**args).get_data()))
    else:
        return json2html.convert(json=json.loads(endpoint_func().get_data()))


def check_db(db, key):
    try:
        return (db[key] is not []) and (len(db[key].keys()) > 1)
    except (KeyError, HTTPError):
        return False


# https://stackoverflow.com/a/38488506
def get_view_function(url, method='GET'):
    """Match a url and return the view and arguments
    it will be called with, or None if there is no view.
    """

    adapter = app.url_map.bind('localhost')

    try:
        match = adapter.match(url, method=method)
    except RequestRedirect as e:
        # recursively match redirects
        return get_view_function(e.new_url, method)
    except (MethodNotAllowed, NotFound):
        # no match
        return (None, None)

    try:
        # return the view function and arguments
        return app.view_functions[match[0]], match[1]
    except KeyError:
        # no view is associated with the endpoint
        return (None, None)


def assign_wa_credentials(plan_json_config):
    # assign WA workspace credentials to system
    UnifiedWorkspaceOutcomeDeterminer.WORKSPACE_NAME = plan_json_config['hovor_config']['short_name']
    UnifiedWorkspaceOutcomeDeterminer.authenticator = IAMAuthenticator(plan_json_config['wa_credentials']['key'])
    UnifiedWorkspaceOutcomeDeterminer.assistant = AssistantV1(
        version='2019-02-28',
        authenticator=UnifiedWorkspaceOutcomeDeterminer.authenticator
    )
    UnifiedWorkspaceOutcomeDeterminer.assistant.set_service_url(plan_json_config['wa_credentials']['api'])

    # In case it is needed in the future, below defaults to EJ's account
    # UnifiedWorkspaceOutcomeDeterminer.WORKSPACE_NAME = plan_json_config['hovor_config']['short_name']
    # if 'key' in plan_json_config['wa_credentials'] and 'api' in plan_json_config['wa_credentials'] and \
    #         plan_json_config['wa_credentials']['key'] != '' and plan_json_config['wa_credentials']['api'] != '':
    #     creds = plan_json_config['wa_credentials']
    #     UnifiedWorkspaceOutcomeDeterminer.authenticator = IAMAuthenticator(creds['key'])
    #     UnifiedWorkspaceOutcomeDeterminer.assistant = AssistantV1(
    #         version='2019-02-28',
    #         authenticator=UnifiedWorkspaceOutcomeDeterminer.authenticator
    #     )
    #     UnifiedWorkspaceOutcomeDeterminer.assistant.set_service_url(creds['api'])
    # else:
    #     UnifiedWorkspaceOutcomeDeterminer.authenticator = IAMAuthenticator(
    #         '4QymnfEtdAo4oRse2gHWmqV9JRTEZOHtWyGZJo5baSmr')
    #     UnifiedWorkspaceOutcomeDeterminer.assistant = AssistantV1(
    #         version='2019-02-28',
    #         authenticator=UnifiedWorkspaceOutcomeDeterminer.authenticator
    #     )
    #     UnifiedWorkspaceOutcomeDeterminer.assistant.set_service_url(
    #         'https://gateway.watsonplatform.net/assistant/api')

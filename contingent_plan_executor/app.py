from hovor import setupapp
from hovor.session.database_session import DatabaseSession
from hovor.core import initialize_session
from hovor.configuration.direct_json_configuration_provider import DirectJsonConfigurationProvider
from hovor.execution_monitor import EM
from environment import initialize_remote_environment
from local_run_utils import run_model_server
from flask import request, jsonify
import json, jsonpickle
import traceback
import os
import sqlalchemy
import random

initialize_remote_environment()
app, db = setupapp()


class ConversationDatabase(db.Model):
    user_id = db.Column(db.String, unique=True, nullable=False, primary_key=True)
    state = db.Column(db.PickleType, nullable=True)
    action = db.Column(db.PickleType, nullable=True)
    action_result = db.Column(db.PickleType, nullable=True)
    context = db.Column(db.PickleType, nullable=True)
    node_id = db.Column(db.PickleType, nullable=True)
    history = db.Column(db.PickleType, nullable=True)

with app.app_context():
    from app import ConversationDatabase
    db.create_all()

def check_db(user_id):
    try:
        return db.session.execute(db.select(ConversationDatabase).filter_by(user_id=user_id)).scalar_one()
    except sqlalchemy.exc.NoResultFound:
        return
    
def accuHovorMsgs(raw_msg, accumulated_f = None):
    if not accumulated_f:
        accumulated_f = []
    # need to split up multiple messages (and remove any resulting empty strings)
    raw_msgs = list(filter(lambda x: x != '', raw_msg.replace("\n", "").split("HOVOR: ")))
    for msg in raw_msgs:
        # duplicates can occur due to accumulated messages resulting in overlap;
        # want to eliminate these when returning a conversation recap
        if len(accumulated_f) > 0:
            if accumulated_f[-1] != {"HOVOR": msg}:
                accumulated_f.append({"HOVOR": msg})
        else:
            accumulated_f.append({"HOVOR": msg})
    return accumulated_f

# allow for the remote chat to initialize the message
@app.route('/new-conversation', methods=['GET', 'POST'])
def new_conversation():
    try:
        if request.method == 'POST':
            # We assume that we only have one trace per user
            input_data = request.get_json()
            user_id = input_data["user_id"]
            # Try to overwrite an existing trace
            existing = check_db(user_id)
            if existing:
                db.session.delete(existing)
                trace_id = user_id
            else:
                return jsonify({'status': 'error', 'msg': "The given user ID does not exist."})
        else:
            user_id = random.getrandbits(128)
            while check_db("trace-%s" % user_id):
                user_id = random.getrandbits(128)
            trace_id = "trace-%s" % user_id

        with open("out_path.txt", "r") as f:
            out_path = f.readlines()[0]
            plan_json_config = json.load(open(f"{out_path}/data.json", "r"))
            hovor_config = json.load(open(f"{out_path}/data.prp.json", "r"))
            plan_id = plan_json_config['name']
        plan_config = DirectJsonConfigurationProvider(plan_id,
                                                      plan_json_config,
                                                      hovor_config['plan'])
        
        plan_config.check_all_action_builders()

        print("Plan fetched.")

        run_model_server(out_path)

        print("Creating a new trace.")
        temp_session = initialize_session(plan_config)
        action = temp_session.current_action

        need_to_execute = (not action.is_external) or (
                action.is_deterministic() and action.action_type != "goal_achieved")
        action_result = action.start_execution()  # initial action execution

        db.session.add(
            ConversationDatabase(
                user_id=trace_id,
                state=jsonpickle.encode(temp_session.current_state),
                action=jsonpickle.encode(temp_session.current_action),
                action_result=jsonpickle.encode(action_result),
                context=jsonpickle.encode(temp_session.get_context_copy()),
                node_id=plan_config.plan.get_initial_node().node_id,
                history=[prog.json for prog in temp_session.delta_history]
            )
        )
        db.session.commit()

        original_message = action_result.get_field('msg')

        # Something that is blocking and internal (like a web api call)
        new_accumulated_messages = None
        diagnostics = []
        if need_to_execute:
            action.end_execution(action_result)
            # Need to run the EM here until we are ready for external input
            session = DatabaseSession(db, trace_id, plan_config)
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
            # If the trace already exists, we delete it first
            # NOTE: do we want to do this?
            db.session.delete(check_db(trace_id))
            db.session.commit()
            if accumulated_messages is None:
                return jsonify({'status': "Plan complete!", "user_id": trace_id})
            else:
                # NOTE: cannot json dumps the diagnostics because they have sets in them.
                with open("diagnostics.txt","w") as f:
                    f.write(str(diagnostics))
                return jsonify(
                    {'status': "Plan complete!", 'msg': accumulated_messages, "user_id": trace_id})

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
            session.save(db, trace_id)

        if action_result is None:
            print("No execution result to return.")
            return jsonify({'status': 'success', 'msg': 'All set!', "user_id": trace_id})
        if action_result.get_field('type') == 'message':
            print("Returning message: %s" % action_result.get_field('msg'))
            # NOTE: cannot json dumps the diagnostics because they have sets in them.
            with open("diagnostics.txt","w") as f:
                f.write(str(diagnostics))
            return jsonify({'status': 'success',
                            'msg': accuHovorMsgs(action_result.get_field('msg')),
                            "user_id": trace_id})
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


# entrypoint to execution monitor.
@app.route('/new-message', methods=['POST'])
def new_message():
    try:
        # We assume that we only have one trace per user
        input_data = request.get_json()
        trace_id = input_data["user_id"]

        with open("out_path.txt", "r") as f:
            out_path = f.readlines()[0]
            plan_json_config = json.load(open(f"{out_path}/data.json", "r"))
            hovor_config = json.load(open(f"{out_path}/data.prp.json", "r"))
            plan_id = plan_json_config['name']
        
        plan_config = DirectJsonConfigurationProvider(plan_id,
                                                      plan_json_config,
                                                      hovor_config['plan'])

        plan_config.check_all_action_builders()

        print("Plan fetched.")

        run_model_server(out_path)

        # Only proceed if the trace exists
        if not check_db(trace_id):
            return jsonify({'status': 'error', 'msg': "The given user ID does not exist."})

        # Load up the existing session
        session = DatabaseSession(db, trace_id, plan_config)
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
            # NOTE: do we want to do this?
            db.session.delete(check_db(trace_id))
            db.session.commit()
            if accumulated_messages is None:
                return jsonify({'status': 'Plan complete!',
                                'action_name': previous_action,
                                'outcome_name': final_outcome_name,
                                'confidence': confidence,
                                'stickiness': 0})
            else:
                # NOTE: cannot json dumps the diagnostics because they have sets in them.
                with open("diagnostics.txt","w") as f:
                    f.write(str(diagnostics))
                return jsonify({'status': "Plan complete!",
                                'action_name': previous_action,
                                'outcome_name': final_outcome_name,
                                'confidence': confidence,
                                'stickiness': 0,
                                'msg': accuHovorMsgs(accumulated_messages),
                                })

        last_execution_result = action.start_execution()

        if accumulated_messages is not None:
            msg = last_execution_result.get_field('msg')
            if msg is None:
                last_execution_result.set_field('msg', accumulated_messages)
            else:
                last_execution_result.set_field('msg', accumulated_messages + '\n' + msg)

        session.update_action_result(last_execution_result)

        # Update the trace state in the database
        session.save(db, trace_id)

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
        # NOTE: cannot json dumps the diagnostics because they have sets in them.
        with open("diagnostics.txt","w") as f:
            f.write(str(diagnostics))
        return jsonify({'status': 'success',
                        'action_name': previous_action,
                        'outcome_name': final_outcome_name,
                        'confidence': confidence,
                        'stickiness': 1,
                        'msg': accuHovorMsgs(last_execution_result.get_field('msg')),
                        }
                    )
    else:
        print("Not sure what to do with action of type %s\n%s" % (last_execution_result.get_field('type'),
                                                                    str(last_execution_result)))
        return jsonify({'status': 'error',
                        'msg': "Received unknown action type of %s" % last_execution_result.get_field('type'),
                        'debug': last_execution_result.json})

# entrypoint to execution monitor.
@app.route('/load-conversation', methods=['POST'])
def load_conversation():
    # We assume that we only have one trace per user
    input_data = request.get_json()
    trace_id = input_data["user_id"]

    with open("out_path.txt", "r") as f:
        out_path = f.readlines()[0]
        plan_json_config = json.load(open(f"{out_path}/data.json", "r"))
        hovor_config = json.load(open(f"{out_path}/data.prp.json", "r"))
        plan_id = plan_json_config['name']
    
    plan_config = DirectJsonConfigurationProvider(plan_id,
                                                    plan_json_config,
                                                    hovor_config['plan'])

    plan_config.check_all_action_builders()

    print("Plan fetched.")

    run_model_server(out_path)

    # Only proceed if the trace exists
    if not check_db(trace_id):
        return jsonify({'status': 'error', 'msg': "The given user ID does not exist."})

    # Load up the existing session
    session = DatabaseSession(db, trace_id, plan_config)
    previous_action = session.current_action.name

    accumulated_messages = []
    for act in session.delta_history:
        if act["action_result"]["fields"]:
            if act["action_result"]["fields"]["type"] == "message":
                accumulated_messages = accuHovorMsgs(act["action_result"]["fields"]["msg"], accumulated_messages)
                if act["action_result"]["fields"]["input"]:
                    accumulated_messages.append({"USER": act["action_result"]["fields"]["input"]})
    # # need to add last action explicitly
    if session.current_action_result.get_field('type') == 'message':
        accumulated_messages = accuHovorMsgs(session.current_action_result.get_field("msg"), accumulated_messages)
        if session.current_action_result.get_field("input"):
            accumulated_messages.append({"USER": session.current_action_result.get_field("input")})
    
    if not accumulated_messages:
        print("No execution result to return.")
        return jsonify({'status': 'success',
                        'action_name': previous_action,
                        'msg': 'No execution result to return. All set!'})
    else:
        print("Returning messages: %s" % accumulated_messages)
        return jsonify({'status': 'Plan complete!' if session.current_action.action_type == 'goal_achieved' else 'success',
                        'action_name': previous_action,
                        'msg': (accumulated_messages),
                        }
                    )

if __name__ == "__main__":
    port = int(os.environ.get('PORT', 5000))
    app.run(debug=False, host='0.0.0.0', port=port)
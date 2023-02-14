from hovor.session.database_session import DatabaseSession
from hovor.core import initialize_session_db
from hovor.execution_monitor import EM
from environment import initialize_local_environment #initialize_db_environment
from local_run_utils import run_rasa_model_server, create_validate_json_config_prov
from hovor import db, app
from flask import request, session
import random
import sys
import os

initialize_local_environment()
# initialize_db_environment()


@app.route('/', methods=['GET', 'POST'])
def set_id():
    if "output_files_path" not in session:
        if len(sys.argv) > 1:
            session["output_files_path"] = sys.argv[1]
        else:
            session["output_files_path"] = "local_data/updated_gold_standard_bot"
            # raise ValueError("Please provide the directory to your plan4dial output files as a system argument.")
    if request.method == 'POST':
        if "user_id" in request.form:
            db_session = DatabaseSession(db, request.form["user_id"], create_validate_json_config_prov(session["output_files_path"]), True)
            session["user_id"] = request.form["user_id"]
        elif "user_id" not in session:
            raise ValueError("Need to provide a conversation ID to load a conversation. If this is your first time here, use a GET request to receive your conversation ID.")  
        run_rasa_model_server(session["output_files_path"])
        action = db_session.current_action
        need_to_execute = (not action.is_external) or (
                action.is_deterministic() and action.action_type != "goal_achieved")
        action_result = action.start_execution()  # initial action execution
        if need_to_execute:
            action.end_execution(action_result)
            # Need to run the EM here until we are ready for external input
            new_accumulated_messages, diagnostics, outcome_name, confidence = EM(db_session, action_result, db, session["user_id"])
            action = session.current_action
    else:
        # just for testing
        user_id = random.getrandbits(32)
        config = create_validate_json_config_prov(session["output_files_path"])
        db_session = initialize_session_db(config, db, user_id)
        db_session.save(db, user_id)
        return f"Your ID is: {user_id}"

    return ""


if __name__ == "__main__":
    port = int(os.environ.get('PORT', 5000))
    app.run(debug=False, host='0.0.0.0', port=port)


    
    # thread = Thread(target=run_local_conversation, args=(arg,))
    # thread.start()

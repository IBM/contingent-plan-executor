from hovor.session.database_session import ConversationDatabase
from local_main import run_conversation_from
from environment import initialize_db_environment
from hovor import db, app

from flask import request, session
import random
import sys
import os


initialize_db_environment()


@app.route('/', methods=['GET', 'POST'])
def set_id():
    if request.method == 'POST':
        if "output_files_path" not in session:
            if len(sys.argv) > 1:
                session["output_files_path"] = sys.argv[1]
            else:
                raise ValueError("Please provide the directory to your plan4dial output files as a system argument.")
        if "convo_id" in request.form:
            run_conversation_from(session["output_files_path"], db, request.form["convo_id"])
        # elif "input" in request.form:
        #     # TODO: need to pass this through somehow
        #     pass
        else:
            raise ValueError("Need to provide a conversation ID to load a conversation. If this is your first time here, use a GET request to receive your conversation ID.")
    else:
        # just for testing
        convo_id = random.getrandbits(32)
        db.session.add(ConversationDatabase(convo_id=convo_id))
        db.session.commit()
        return f"Your ID is: {convo_id}"

    return ""


if __name__ == "__main__":
    port = int(os.environ.get('PORT', 5000))
    app.run(debug=False, host='0.0.0.0', port=port)


    
    # thread = Thread(target=run_local_conversation, args=(arg,))
    # thread.start()


from flask import Flask
from flask.json import JSONEncoder
import atexit
# import cf_deployment_tracker
import os
from flask_cors import CORS

from db import db_setup

# Emit Bluemix deployment event
# //deprecated//
# cf_deployment_tracker.track()

app = Flask(__name__)
CORS(app, resources={r"/*": {"origins": "*"}})
db_setup(app)

class CustomJSONEncoder(JSONEncoder):
    def default(self, obj):
        if isinstance(obj, set):
            return list(obj)
        return JSONEncoder.default(self, obj)
app.json_encoder = CustomJSONEncoder

from routes import *

# On Bluemix, get the port number from the environment variable PORT
# When running this app on the local machine, default the port to 8000
port = int(os.getenv('PORT', 9000))

@atexit.register
def shutdown():
    if app.db_client:
        app.db_client.disconnect()

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=port, debug=True)

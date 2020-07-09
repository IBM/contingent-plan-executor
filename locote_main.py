import sys

import jsonpickle
from flask import Flask
from flask_cors import CORS

from db import db_setup
from environment import initialize_local_environment
from hovor.core import run_interaction

if len(sys.argv) != 2:
    raise ValueError("Expect plan id as the only argument")

pid = sys.argv[1]

initialize_local_environment()

# load configuration provider from database
app = Flask(__name__)
CORS(app)
db_setup(app)

configuration_provider = jsonpickle.decode(app.db[pid]['data'])
configuration_provider.check_all_action_builders()

run_interaction(configuration_provider)

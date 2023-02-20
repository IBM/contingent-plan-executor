from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from flask_cors import CORS
import random
import sys


def DEBUG(s):
    #pass
    print(s)

app = Flask(__name__, template_folder='../templates')
CORS(app)
# app.config["SQLALCHEMY_DATABASE_URI"] = "sqlite:////../data/project.db" # for docker
app.config["SQLALCHEMY_DATABASE_URI"] = "sqlite:///project.db" # ONLY for local runs
app.config['SQLALCHEMY_ECHO'] = True
app.secret_key = str(random.getrandbits(128))

db = SQLAlchemy()
db.init_app(app)
with app.app_context():
    from hovor.session.database_session import DatabaseSession
    db.create_all()

# also write the plan configuration data to the volume
if len(sys.argv) > 1:
    output_files_path = sys.argv[1]
else:
    # raise ValueError("Please provide the directory to your plan4dial output files as a system argument.")
    output_files_path = "local_data/updated_gold_standard_bot" # ONLY for local debugging

# save the output files path name
with open("out_path.txt", "w") as f:
    f.write(output_files_path)
    
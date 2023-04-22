from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from flask_cors import CORS
from sqlalchemy.exc import OperationalError
import random
import sys


def DEBUG(s):
    # pass
    print(s)


def setup(sqlalchemy_db_uri):
    app = Flask(__name__, template_folder="../templates")
    CORS(app)
    app.config["SQLALCHEMY_ECHO"] = True
    app.secret_key = str(random.getrandbits(128))
    db = SQLAlchemy()
    app.config["SQLALCHEMY_DATABASE_URI"] = sqlalchemy_db_uri
    db.init_app(app)
    return app, db


def setupapp():
    # also write the plan configuration data to the volume
    if len(sys.argv) > 1:
        output_files_path = sys.argv[1]
    else:
        raise ValueError(
            "Please provide the directory to your plan4dial output files as a system argument."
        )
        # output_files_path = "local_data/updated_gold_standard_bot" # ONLY for local debugging

    # save the output files path name
    with open("out_path.txt", "w") as f:
        f.write(output_files_path)

    # mounted docker run
    try:
        app, db = setup("sqlite:////../data/project.db")
        with app.app_context():
            # don't import DatabaseSession yet; we just want to make sure we can create the
            # db in the given directory. (importing creates the tables and it seems we can
            # only do this once).
            db.create_all()
    # local or unmounted docker runs
    except OperationalError:
        app, db = setup("sqlite:///project.db")

    return app, db

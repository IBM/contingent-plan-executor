from flask import Flask
from flask_sqlalchemy import SQLAlchemy
import random

def DEBUG(s):
    #pass
    print(s)

app = Flask(__name__)
# app.config["SQLALCHEMY_DATABASE_URI"] = "sqlite:////../data/project.db"
app.config["SQLALCHEMY_DATABASE_URI"] = "sqlite:///project.db"
app.config['SQLALCHEMY_ECHO'] = True
app.secret_key = str(random.getrandbits(128))
db = SQLAlchemy()
db.init_app(app)
with app.app_context():
    from hovor.session.database_session import DatabaseSession
    db.create_all()

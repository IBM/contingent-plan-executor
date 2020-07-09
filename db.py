
from cloudant import Cloudant
import os
import json

def db_setup(app):
    db_name = os.getenv('DB_NAME')
    if db_name:
        print('db name is : ' + db_name)
    app.db_client = None
    app.db = None

    if 'CUSTOM_VCAP_SERVICES' in os.environ:
        c_vcap = json.loads(os.getenv('CUSTOM_VCAP_SERVICES'))
        creds = c_vcap['cloudantNoSQLDB'][0]['credentials']
        user = creds['username']
        password = creds['password']
        url = 'https://' + creds['host']
        app.db_client = Cloudant(user, password, url=url, connect=True)
        app.db = app.db_client.create_database(db_name, throw_on_exists=False)
    elif 'VCAP_SERVICES' in os.environ:
        vcap = json.loads(os.getenv('VCAP_SERVICES'))
        print('Found VCAP_SERVICES')
        if 'cloudantNoSQLDB' in vcap:
            creds = vcap['cloudantNoSQLDB'][0]['credentials']
            user = creds['username']
            password = creds['password']
            url = 'https://' + creds['host']
            app.db_client = Cloudant(user, password, url=url, connect=True)
            app.db = app.db_client.create_database(db_name, throw_on_exists=False)
    elif os.path.isfile('vcap-local.json'):
        with open('vcap-local.json') as f:
            vcap = json.load(f)
            print('Found local VCAP_SERVICES')
            creds = vcap['services']['cloudantNoSQLDB'][0]['credentials']
            user = creds['username']
            password = creds['password']
            db_name = vcap['services']['cloudantNoSQLDB'][0]['db_name']
            url = 'https://' + creds['host']
            app.db_client = Cloudant(user, password, url=url, connect=True)
            app.db = app.db_client.create_database(db_name, throw_on_exists=False)

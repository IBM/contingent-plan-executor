from local_main import run_local_conversation
from flask import Flask, render_template, session, app, request, redirect, url_for, render_template_string
from threading import Thread
import random
import os
import sys
from datetime import timedelta

app = Flask(__name__)
app.secret_key = str(random.getrandbits(128))


@app.before_request
def make_session_permanent():
    session.permanent = True
    app.permanent_session_lifetime = timedelta(minutes=0.12)

# @app.route('/')
# def home():
#     session['id'] = "1"
#     return render_template('index.html')

@app.route('/', methods=['GET', 'POST'])
def set_id():
    if request.method == 'POST':
        # Save the form data to the session object
        session['id'] = request.form['id']
    return render_template_string("""
            {% if session['id'] %}
                <h1>Welcome {{ session['id'] }}!</h1>
            {% else %}
                <h1>Welcome! Please enter your id         
            <form method="post">
            <label for="id">Enter your id:</label>
            <input type="id" id="id" name="id" required />
            <button type="submit">Submit</button
        </form></h1>
            {% endif %}
        """)


if __name__ == "__main__":
    port = int(os.environ.get('PORT', 5000))
    app.run(debug=True, host='0.0.0.0', port=port)
    if len(sys.argv) > 1:
        arg = sys.argv[1]
    else:
        raise ValueError("Please provide the directory to your plan4dial output files as a system argument.")
    
    thread = Thread(target=run_local_conversation, args=arg)
    thread.start()

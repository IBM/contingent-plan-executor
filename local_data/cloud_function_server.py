import random

from flask import Flask, request
import json

app = Flask(__name__)


@app.route('/test_endpoint', methods=['POST'])
def test_endpoint():
    output = {"rendered-recommendations": None}
    try:
        request_data = request.get_json()
        output["test_var"] = random.uniform(0.0, 1.0)
        output["rendered-recommendations"] = request_data
        output["outcome_chosen"] = 0
        output["summary"] = {"summaryobject": ["complex_description"]}

    finally:
        print(output)
        return json.dumps(output)


if __name__ == '__main__':
    app.run(debug=True, port=5000)  # run app in debug mode on port 5000

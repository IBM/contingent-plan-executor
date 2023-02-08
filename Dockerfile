FROM python:3.8

WORKDIR /root/app

COPY requirements.txt .

RUN pip install -r requirements.txt

RUN python -m spacy download en_core_web_md

COPY contingent_plan_executor/ ./contingent_plan_executor

COPY local_data/ ./local_data

ENTRYPOINT ["python", "./contingent_plan_executor/run_flask.py"]
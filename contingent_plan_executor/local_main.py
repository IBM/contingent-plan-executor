from hovor.core import run_interaction, run_interaction_from
from local_run_utils import *
import sys
import json


def run_local_conversation(output_files_path):
    run_interaction(initialize_local_run(output_files_path))

def run_conversation_from(output_files_path, db, convo_id):
    config = initialize_local_run(output_files_path)
    run_interaction_from(config, db, convo_id)


if __name__ == "__main__":
    # if len(sys.argv) > 1:
    #     arg = sys.argv[1]
    # else:
    #     raise ValueError("Please provide the directory to your plan4dial output files as a system argument.")
    arg = "local_data/updated_gold_standard_bot"
    with open("db.json") as f:
        run_conversation_from(arg, json.load(f), "1")
    # run_conversation_from(arg, {}, "1")
    # run_local_conversation(arg)

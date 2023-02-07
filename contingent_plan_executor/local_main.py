from hovor.core import run_interaction
from local_run_utils import *
import sys

def run_local_conversation(output_files_path):
    run_interaction(initialize_local_run(output_files_path))

def run_conversation_from(output_files_path, save_state):
    run_interaction(initialize_local_run(output_files_path), True)


if __name__ == "__main__":
    # if len(sys.argv) > 1:
    #     arg = sys.argv[1]
    # else:
    #     raise ValueError("Please provide the directory to your plan4dial output files as a system argument.")
    arg = "local_data/updated_gold_standard_bot"
    run_local_conversation(arg)

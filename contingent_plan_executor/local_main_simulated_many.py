from hovor.core import run_interaction, simulate_interaction
from local_run_utils import *
import time


def run_local_conversation(output_files_path):
    simulate_interaction(initialize_local_run(output_files_path))


def simulate_local_conversation(output_files_path):
    simulate_interaction(initialize_local_run_simulated(output_files_path), "sample_conversations")


if __name__ == "__main__":
    for i in range(10):
        print(i)
        simulate_local_conversation(
            "/home/rebecca/plan4dial/plan4dial/local_data/bank_bot/output_files"
            )
        time.sleep(1)
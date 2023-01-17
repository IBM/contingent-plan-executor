from hovor.core import run_interaction, simulate_interaction
from local_run_utils import *


def run_local_conversation(output_files_path):
    simulate_interaction(initialize_local_run(output_files_path))


def simulate_local_conversation(output_files_path):
    simulate_interaction(initialize_local_run_simulated(output_files_path))


if __name__ == "__main__":
    simulate_local_conversation(
        "/home/jacob/Dev/plan4dial/plan4dial/local_data/gold_standard_bot/output_files")

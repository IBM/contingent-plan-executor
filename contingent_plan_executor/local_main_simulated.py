from hovor.core import simulate_interaction
from local_run_utils import *


def run_local_conversation(output_files_path):
    simulate_interaction(initialize_local_run(output_files_path))


def simulate_local_conversation(output_files_path, sample_convos_out):
    simulate_interaction(initialize_local_run_simulated(output_files_path), sample_convos_out)


if __name__ == "__main__":
    simulate_local_conversation(
        "/home/rebecca/plan4dial/plan4dial/local_data/bank_bot/output_files",
        "sample_conversations/bank_bot"
        )

from hovor.core import run_interaction, simulate_interaction
from local_run_utils import *
import time


def run_local_conversation(output_files_path):
    simulate_interaction(initialize_local_run(output_files_path))


def simulate_local_conversation(output_files_path, simulated_out_path):
    simulate_interaction(initialize_local_run_simulated(output_files_path), simulated_out_path)


if __name__ == "__main__":
    for i in range(1):
        print(i)
        simulate_local_conversation(
            "\\\wsl.localhost\\Ubuntu\\root\\plan4dial\\plan4dial\\local_data\\medical_bot\\output_files", 
            "sample_conversations/medical_bot"
            )
        time.sleep(1)
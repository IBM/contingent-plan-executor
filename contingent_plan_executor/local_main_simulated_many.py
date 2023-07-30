from hovor.core import simulate_interaction
from local_run_utils import *
import time
import os
from glob import glob


def run_local_conversation(output_files_path):
    simulate_interaction(initialize_local_run(output_files_path))


def simulate_local_conversation(output_files_path, sample_convos_out):
    simulate_interaction(initialize_local_run_simulated(output_files_path), sample_convos_out)


if __name__ == "__main__":
    bot = "medical_bot"
    for i in range(20):
        print(i)
        simulate_local_conversation(
            f"/home/rebecca/plan4dial/plan4dial/local_data/{bot}/output_files",
            f"sample_conversations/{bot}"
            )
        time.sleep(1)
    for f in glob(f"sample_conversations/{bot}/*.txt"):
        os.remove(f)
    for idx, f in enumerate(glob(f"sample_conversations/{bot}/*.json")):
        os.replace(f, f"sample_conversations/{bot}/convo_{idx + 1}.json")
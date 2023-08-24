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
    # bot = "gold_standard_bot"
    out = "/home/rebecca/conversation-alignment/beam_search/eval/1/1_unmodified_run/json_convos"
    for i in range(20):
        print(i)
        simulate_local_conversation(
            "/home/rebecca/conversation-alignment/beam_search/eval/1/1_unmodified_run/output_files",
            out
            )
        time.sleep(1)
    for idx, f in enumerate(glob(os.path.join(out, "*.json"))):
        os.replace(f"{f.split('.json')[0]}.txt", os.path.join(out, f"convo_{idx + 1}.txt"))
        os.replace(f, os.path.join(out, f"convo_{idx + 1}.json"))

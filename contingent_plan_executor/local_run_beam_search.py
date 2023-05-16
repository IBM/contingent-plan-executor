from hovor.hovor_beam_search.core import BeamSearchExecutor
from local_run_utils import initialize_local_run
from glob import glob
import json
import os


if __name__ == "__main__":
    simulated_convos_path ="C:\\Users\\Rebecca\\Desktop\\work\\coding\\contingent-plan-executor\\simulated_convos"
    # read all json files in the simulated convos directory
    conversations = [
        json.loads(open(os.path.join(simulated_convos_path, out), "r").read()) for out in glob(f"{simulated_convos_path}/*.json")
    ]
    output_files_path = "C:\\Users\\Rebecca\\Desktop\\work\\coding\\plan4dial\\plan4dial\\local_data\\rollout_no_system_gold_standard_bot\\output_files"
    initialize_local_run(output_files_path, False)
    exec = BeamSearchExecutor(
        3,
        2,
        conversations,
        True,
        "output",
        output_files_path=output_files_path,
    )
    exec.beam_search()
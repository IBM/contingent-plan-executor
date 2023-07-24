from hovor.hovor_beam_search.core import ConversationAlignmentExecutor
from local_run_utils import initialize_local_run
from glob import glob
import json
import os


if __name__ == "__main__":
    simulated_convos_path = "sample_conversations"
    # read all json files in the simulated convos directory
    conversations = [
        json.loads(open(out, "r").read()) for out in glob(f"{simulated_convos_path}/*.json")
    ]
    output_files_path = "C:\\Users\\Rebecca\\Desktop\\work\\coding\\plan4dial\\plan4dial\\local_data\\gold_standard_bot\\output_files"
    initialize_local_run(output_files_path, False)
    exec = ConversationAlignmentExecutor(
        2,
        2,
        conversations,
        "contingent_plan_executor/hovor/hovor_beam_search/beam_search_output/",
        output_files_path=output_files_path,
    )
    exec.beam_search()
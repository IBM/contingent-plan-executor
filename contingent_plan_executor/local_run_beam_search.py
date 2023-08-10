from hovor.hovor_beam_search.core import ConversationAlignmentExecutor
from local_run_utils import initialize_local_run
from glob import glob


if __name__ == "__main__":
    bot = "gold_standard_bot"
    simulated_convos_path = "/home/rebecca/conversation-alignment/beam_search/eval/2/json_convos"
    # read all json files in the simulated convos directory
    conversation_paths = [
        out for out in glob(f"{simulated_convos_path}/*.json")
    ]
    output_files_path = "/home/rebecca/conversation-alignment/beam_search/eval/2/2_modified_run/output_files"
    initialize_local_run(output_files_path, False)
    out_dir = "/home/rebecca/conversation-alignment/beam_search/eval/2/2_modified_run/4_iter"
    exec = ConversationAlignmentExecutor(
        k=3,
        max_fallbacks=1,
        conversation_paths=conversation_paths,
        output_path=out_dir,
        output_files_path=output_files_path,
    )
    exec.beam_search()
    ConversationAlignmentExecutor.plot(f"{out_dir}/output_stats.json", out_dir)
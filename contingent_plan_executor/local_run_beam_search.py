from hovor.hovor_beam_search.core import ConversationAlignmentExecutor
from local_run_utils import initialize_local_run
from glob import glob


if __name__ == "__main__":
    bot = "gold_standard_bot"
    simulated_convos_path = f"sample_conversations/{bot}"
    # read all json files in the simulated convos directory
    conversation_paths = [
        out for out in glob(f"{simulated_convos_path}/*.json")
    ]
    output_files_path = f"/home/rebecca/plan4dial/plan4dial/local_data/{bot}/output_files"
    initialize_local_run(output_files_path, False)
    exec = ConversationAlignmentExecutor(
        k=2,
        max_fallbacks=1,
        conversation_paths=conversation_paths,
        graphs_path=f"contingent_plan_executor/hovor/hovor_beam_search/beam_search_output/{bot}",
        output_files_path=output_files_path,
    )
    exec.beam_search()
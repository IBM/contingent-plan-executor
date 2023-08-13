from hovor.hovor_beam_search.core import ConversationAlignmentExecutor
from local_run_utils import initialize_local_run
from glob import glob


if __name__ == "__main__":
    bot = "gold_standard_bot"
    simulated_convos_path = "C:\\Users\\rebec\\OneDrive\\Desktop\\conversation-alignment\\beam_search\\eval\\1\\json_convos"
    # read all json files in the simulated convos directory
    conversation_paths = [
        out for out in glob(f"{simulated_convos_path}/*.json")
    ]
    output_files_path = "C:\\Users\\rebec\\OneDrive\\Desktop\\conversation-alignment\\beam_search\\eval\\1\\2_modified_run\\output_files"
    initialize_local_run(output_files_path, False)
    for kval in [2, 3, 4]:
        out_dir = f"C:\\Users\\rebec\\OneDrive\\Desktop\\conversation-alignment\\beam_search\\eval\\1\\2_modified_run\\k_{kval}"
        exec = ConversationAlignmentExecutor(
            k=kval,
            max_fallbacks=1,
            conversation_paths=conversation_paths,
            output_path=out_dir,
            output_files_path=output_files_path,
        )
        exec.beam_search()
        ConversationAlignmentExecutor.plot(f"{out_dir}\\output_stats.json", out_dir)

    # simulated_convos_path = "C:\\Users\\rebec\\OneDrive\\Desktop\\conversation-alignment\\beam_search\\eval\\3\\json_convos"
    # # read all json files in the simulated convos directory
    # conversation_paths = [
    #     out for out in glob(f"{simulated_convos_path}/*.json")
    # ]
    # output_files_path = "C:\\Users\\rebec\\OneDrive\\Desktop\\conversation-alignment\\beam_search\\eval\\3\\2_modified_run\\output_files"
    # initialize_local_run(output_files_path, False)
    # for kval in [1, 2, 3, 4, 5]:
    #     for fval in [1, 2, 3, 4, 5]:
    #         out_dir = f"C:\\Users\\rebec\\OneDrive\\Desktop\\conversation-alignment\\beam_search\\eval\\1\\3_modified_run\\k_{kval}_f_{fval}"
    #         exec = ConversationAlignmentExecutor(
    #             k=kval,
    #             max_fallbacks=fval,
    #             conversation_paths=conversation_paths,
    #             output_path=out_dir,
    #             output_files_path=output_files_path,
    #         )
    #         exec.beam_search()
    #         ConversationAlignmentExecutor.plot(f"{out_dir}/output_stats.json", out_dir)
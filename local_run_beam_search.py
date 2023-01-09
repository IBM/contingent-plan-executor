from hovor.hovor_beam_search.core import BeamSearchExecutor
from local_run_utils import initialize_local_run


if __name__ == "__main__":
    output_dir = "C:\\Users\\Rebecca\\Desktop\\plan4dial\\plan4dial\\local_data\\rollout_no_system_icaps_bot_mini\\output_files"
    initialize_local_run(output_dir, False)

    icaps_conversation_entity_drop = [
        {
            "AGENT": "What invited talk do you want to see on Day 1? You can learn about Factored Transition Systems or the applications of Multi-Agent Path Finding."
        },
        {"USER": "beam want to see the talk on Factored Transition Systems."},
        {
            "AGENT": "What session do you want to see in the morning? The sessions available are on Planning Representations and Scheduling, Verification, RL, or Heuristics in Classical Planning."
        },
        {
            "USER": "beam want to learn more about classical planning and why applying heuristics is useful."
        },
        {
            "AGENT": "What session do you want to see in the afternoon? Your options are: Model-Based Reasoning, Learning for Scheduling Applications, Search, and Optimal Planning."
        },
        {"USER": "Please schedule me in to watch the talk on Model-Based Reasoning."},
        {"AGENT": "Thank you, enjoy your day!"},
    ]
    icaps_conversation_break_both = [
        {
            "AGENT": "What invited talk do you want to see on Day 1? You can learn about Factored Transition Systems or the applications of Multi-Agent Path Finding."
        },
        {"USER": "beam want to see the talk on Factored Transition Systems."},
        {"AGENT": "And then? What after the invited talk?"},
        {
            "USER": "beam want to learn more about classical planning and why applying heuristics is useful."
        },
        {
            "AGENT": "What session do you want to see in the afternoon? Your options are: Model-Based Reasoning, Learning for Scheduling Applications, Search, and Optimal Planning."
        },
        {"USER": "Please schedule me in to watch the talk on Model-Based Reasoning."},
        {"AGENT": "Thank you, enjoy your day!"},
    ]

    gen = BeamSearchExecutor(3, 1, icaps_conversation_entity_drop, True, "icaps_entity_drop_goal", output_files_path=output_dir)
    gen.beam_search()

    gen.max_fallbacks = 2
    gen.graph_file = "icaps_entity_drop_no_goal"
    gen.beam_search()

    gen.max_fallbacks = 1
    gen.conversation = icaps_conversation_break_both
    gen.graph_file = "icaps_break_both"
    gen.beam_search()

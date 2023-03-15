import numpy as np
import seaborn as sns
import pandas as pd
import matplotlib.pyplot as plt
import os

from local_run_utils import *
from local_simulate_evaluate_utils import simulate_local_conversations, load_detailed_jsons, build_score_sentence_nsp_function_bert, experiment_diologues_no_agg

import streamlit as st
import shutil


def convo_heatmap(scores, utterances):
    fig, axes = plt.subplots(1, 1, sharey=True, dpi=300, figsize=(20, 10))
    sns.heatmap(ax=axes,
                data=scores,
                annot=utterances,
                fmt='',
                # linewidths=0.25,
                cmap="mako",
                vmin=-10,
                vmax=20,
                cbar=True,
                xticklabels=False,
                yticklabels=False)
    return fig


if __name__ == "__main__":

    # redefine util methods using the streamlit cache wrapper
    simulate_local_conversations = st.cache_data(
        simulate_local_conversations, max_entries=1)
    experiment_diologues_no_agg = st.cache_data(experiment_diologues_no_agg)
    # load_detailed_jsons = st.cache_data(load_detailed_jsons) # shouldn't cache this as files could differ while path won't
    build_score_sentence_nsp_function_bert = st.cache_resource(
        build_score_sentence_nsp_function_bert)

    st.write("""
    # Chatbot Simulation and Evaluation
    Let's go!
    """)

    output_dir = st.text_input("Output Directory", value="simulated_convos")

    chatbot_output_files = st.text_input(
        "Chatbot Output Files", value="/home/jacob/Dev/plan4dial/plan4dial/local_data/gold_standard_bot/output_files")

    n_convos = st.number_input("Number of Conversations", value=5)

    # Simulate conversations
    simulate_local_conversations(chatbot_output_files,
                                 output_dir,
                                 n_convos,
                                 overwrite_output_dir=True)

    # load detailed jsons
    loaded_convos = load_detailed_jsons(output_dir)

    main_bot_name = loaded_convos[0]['bot_name']

    # build the nsp model
    score_sentence_nsp = build_score_sentence_nsp_function_bert()

    # compute scores for every sentence in every convo
    convo_sentence_scores = experiment_diologues_no_agg([c['utterances'] for c in loaded_convos],
                                                        score_sentence_nsp,
                                                        n_pretext_sentences=5)

    # make agg scores
    mean_score_per_convo = [np.mean(x) for x in convo_sentence_scores]
    median_score_per_convo = [np.median(x) for x in convo_sentence_scores]
    min_score_per_convo = [np.min(x) for x in convo_sentence_scores]

    # show distribution & agg scores
    fig = plt.figure()
    sns.kdeplot(median_score_per_convo)
    st.pyplot(fig)

    # show top n and bottom n with conversation and score
    results = pd.DataFrame({"bot_name": [c['bot_name'] for c in loaded_convos],
                            "time_created": [c['time_created'] for c in loaded_convos],
                            "median_score": median_score_per_convo,
                            "mean_score": mean_score_per_convo,
                            "min_score": min_score_per_convo, })

    st.write('Conversation Scores')
    st.write(results)

    # add_random_convos = st.checkbox('Compare with shuffled conversations')

    random_convos_expander = st.expander("Randomized Convos Comparison")
    random_convos_expander.write('## Compare with randomized bot')
    random_convos_expander.write('This section will allow you to compare your scores to your bot if its utterances were shuffled. ')
    random_convos_expander.write('It will analyze the same number of conversations as your bot did. ')
    add_random_convos = random_convos_expander.checkbox('Compare with shuffled conversations', value=False)

    if add_random_convos:
        # load detailed jsons
        loaded_convos_randomized = load_detailed_jsons(output_dir, randomize=True)

        # compute scores for every sentence in every convo
        convo_sentence_scores_randomized = experiment_diologues_no_agg([c['utterances'] for c in loaded_convos_randomized],
                                                            score_sentence_nsp,
                                                            n_pretext_sentences=5)
        
        mean_score_per_convo_randomized = [np.mean(x) for x in convo_sentence_scores_randomized]
        median_score_per_convo_randomized = [np.median(x) for x in convo_sentence_scores_randomized]
        min_score_per_convo_randomized = [np.min(x) for x in convo_sentence_scores_randomized]


        # show distribution & agg scores
        fig = plt.figure()
        sns.kdeplot(median_score_per_convo, label='normal')
        sns.kdeplot(median_score_per_convo_randomized, label='random')
        plt.legend()
        random_convos_expander.pyplot(fig)

        results_randomized = pd.DataFrame({"bot_name": [c['bot_name'] for c in loaded_convos_randomized],
                            "time_created": [c['time_created'] for c in loaded_convos_randomized],
                            "median_score": median_score_per_convo_randomized,
                            "mean_score": mean_score_per_convo_randomized,
                            "min_score": min_score_per_convo_randomized, })
        
        random_convos_expander.write('### Conversation Scores Randomized')
        random_convos_expander.write(results_randomized)

        selected_ind_random = random_convos_expander.number_input(
        'What random conversation index would you like to see?', value=0, key='random_ind_selector')
        fig = convo_heatmap(np.array(convo_sentence_scores_randomized[selected_ind_random]).reshape(-1, 1),
                        np.array(loaded_convos_randomized[selected_ind_random]['utterances']).reshape(-1, 1))
        random_convos_expander.pyplot(fig)
        

    st.write('## View the best n and worst n conversations')
    st.write('This section will contain conversations from the randomized bot if enabled. ')

    n = st.number_input("Top n, n=", value=2, key='n')
    convo_compare_method = st.selectbox(
        "comparison_metric", ['median_score', 'mean_score', 'min_score'])
    
    if add_random_convos:
        final_results = pd.concat([results, results_randomized])
    else:
        final_results = results.copy()

    worst_n = final_results.sort_values(
        by=convo_compare_method).reset_index().iloc[:n]
    best_n = final_results.sort_values(
        by=convo_compare_method, ascending=False).reset_index().iloc[:n]

    st.write(f'### Worst {n} conversations by {convo_compare_method}')
    st.write(worst_n)
    if add_random_convos:
        st.write(f'Your bot is {  sum(worst_n["bot_name"]==main_bot_name) / len(worst_n["bot_name"]) * 100  :.1f}% of worst conversations.')
    st.write(f'### Best {n} conversations by {convo_compare_method}')
    st.write(best_n)
    if add_random_convos:
        st.write(f'Your bot is {  sum(best_n["bot_name"]==main_bot_name) / len(best_n["bot_name"]) * 100  :.1f}% of best conversations.')

    # show the worst & best conversation with highlighted sentence scores

    st.write('## Examine conversations from your bot')
    st.write('This section will not contain samples from the randomized bot.')

    worst_convo_ind = results[convo_compare_method].argmin()
    best_convo_ind = results[convo_compare_method].argmax()

    st.write("### Sentence evaluations for the worst conversation")
    fig = convo_heatmap(np.array(convo_sentence_scores[worst_convo_ind]).reshape(-1, 1),
                        np.array(loaded_convos[worst_convo_ind]['utterances']).reshape(-1, 1))
    st.pyplot(fig)

    st.write("### Sentence evaluations for the best conversation")
    fig = convo_heatmap(np.array(convo_sentence_scores[best_convo_ind]).reshape(-1, 1),
                        np.array(loaded_convos[best_convo_ind]['utterances']).reshape(-1, 1))
    st.pyplot(fig)

    st.write("### Sentence evaluations for selected conversation")
    selected_ind = st.number_input(
        'What conversation index would you like to see?', value=0)

    st.write(
        f"Median score: {median_score_per_convo[selected_ind]:.2f}, percentile: {sum(median_score_per_convo < median_score_per_convo[selected_ind])/len(median_score_per_convo):.2f}")
    st.write(
        f"Mean score: {mean_score_per_convo[selected_ind]:.2f}, percentile: {sum(mean_score_per_convo < mean_score_per_convo[selected_ind])/len(mean_score_per_convo):.2f}")
    st.write(
        f"Min score: {min_score_per_convo[selected_ind]:.2f}, percentile: {sum(min_score_per_convo < min_score_per_convo[selected_ind])/len(min_score_per_convo):.2f}")

    fig = convo_heatmap(np.array(convo_sentence_scores[selected_ind]).reshape(-1, 1),
                        np.array(loaded_convos[selected_ind]['utterances']).reshape(-1, 1))
    st.pyplot(fig)

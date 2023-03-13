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

    n = st.number_input("Top n, n=", value=2)
    convo_compare_method = st.selectbox(
        "comparison_metric", ['median_score', 'mean_score', 'min_score'])

    worst_n = results.sort_values(
        by=convo_compare_method).reset_index().iloc[:n]
    best_n = results.sort_values(
        by=convo_compare_method, ascending=False).reset_index().iloc[:n]

    st.write(f'### Worst {n} conversations by {convo_compare_method}')
    st.write(worst_n)
    st.write(f'### Best {n} conversations by {convo_compare_method}')
    st.write(best_n)

    # show the worst & best conversation with highlighted sentence scores

    worst_convo_ind = results[convo_compare_method].argmin()
    best_convo_ind = results[convo_compare_method].argmax()

    st.write("Sentence evaluations for the worst conversation")
    fig = convo_heatmap(np.array(convo_sentence_scores[worst_convo_ind]).reshape(-1, 1),
                        np.array(loaded_convos[worst_convo_ind]['utterances']).reshape(-1, 1))
    st.pyplot(fig)

    st.write("Sentence evaluations for the best conversation")
    fig = convo_heatmap(np.array(convo_sentence_scores[best_convo_ind]).reshape(-1, 1),
                        np.array(loaded_convos[best_convo_ind]['utterances']).reshape(-1, 1))
    st.pyplot(fig)

    st.write("Sentence evaluations for selected conversation")
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

import numpy as np
import seaborn as sns
import pandas as pd
import matplotlib.pyplot as plt

from local_run_utils import *
from local_simulate_evaluate_utils import *

import streamlit as st
import shutil



if __name__ == "__main__":

    st.write("""
    # Chatbot Simulation and Evaluation
    Let's go!
    """)

    output_dir = st.text_input("Output Directory", value="simulated_convos")
 
    shutil.rmtree(output_dir)

    chatbot_output_files = st.text_input("Chatbot Output Files", value="/home/jacob/Dev/plan4dial/plan4dial/local_data/gold_standard_bot/output_files")

    n_convos = st.number_input("Number of Conversations", value=5)

    # Simulate conversations
    simulate_local_conversations(chatbot_output_files, 
                                 output_dir,
                                 n_convos)
    
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
    results = pd.DataFrame({"median_score": median_score_per_convo, 
                            "bot_name": [c['bot_name'] for c in loaded_convos],
                            "time_created": [c['time_created'] for c in loaded_convos]})
    
    st.write('Conversation Scores')
    st.write(results)

    n = st.number_input("Top n, n=", value=2)
    
    worst_n = results.sort_values(by='median_score').reset_index().iloc[:n]
    best_n = results.sort_values(by='median_score').reset_index().iloc[-n:]

    st.write(f'### Worst {n} conversations')
    st.write(worst_n)
    st.write(f'### Best {n} conversations')
    st.write(best_n)

    # show the worst & best conversation with highlighted sentence scores

    worst_convo_ind = results['median_score'].argmin()
    best_convo_ind = results['median_score'].argmax()

    st.write("Sentence evaluations for the worst conversation")

    fig, axes = plt.subplots(1, 1, sharey=True, dpi=300, figsize=(20,10))
    sns.heatmap(ax=axes, 
                data=np.array(convo_sentence_scores[worst_convo_ind]).reshape(-1,1), 
                annot=np.array(loaded_convos[worst_convo_ind]['utterances']).reshape(-1,1), 
                fmt='', 
                # linewidths=0.25,
                cmap="mako", 
                vmin=-10, 
                vmax=20, 
                cbar=True, 
                xticklabels=False, 
                yticklabels=False)
    st.pyplot(fig)

    st.write("Sentence evaluations for the best conversation")

    fig, axes = plt.subplots(1, 1, sharey=True, dpi=300, figsize=(20,10))
    sns.heatmap(ax=axes, 
                data=np.array(convo_sentence_scores[best_convo_ind]).reshape(-1,1), 
                annot=np.array(loaded_convos[best_convo_ind]['utterances']).reshape(-1,1), 
                fmt='', 
                # linewidths=0.25,
                cmap="mako", 
                vmin=-10, 
                vmax=20, 
                cbar=True, 
                xticklabels=False, 
                yticklabels=False)
    st.pyplot(fig)
    

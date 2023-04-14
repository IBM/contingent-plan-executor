import numpy as np
import seaborn as sns
import pandas as pd
import matplotlib.pyplot as plt

from local_run_utils import *
from local_simulate_evaluate_utils import *



if __name__ == "__main__":

    output_dir = "simulated_convos"

    # Simulate conversations
    simulate_local_conversations("/home/jacob/Dev/plan4dial/plan4dial/local_data/gold_standard_bot/output_files", 
                                 output_dir,
                                 5)
    
    # load detailed jsons
    loaded_convos = load_detailed_jsons(output_dir)

    # build the nsp model
    score_sentence_nsp = build_score_sentence_nsp_function_bert()
    
    # compute scores for every sentence in every convo
    convo_sentence_scores = experiment_dialogues_no_agg([c['utterances'] for c in loaded_convos], 
                                                    score_sentence_nsp, 
                                                    n_pretext_sentences=5)

    # make agg scores
    mean_score_per_convo = [np.mean(x) for x in convo_sentence_scores]
    median_score_per_convo = [np.median(x) for x in convo_sentence_scores]
    min_score_per_convo = [np.min(x) for x in convo_sentence_scores]

    # show distribution & agg scores
    sns.kdeplot(median_score_per_convo)

    # show top n and bottom n with conversation and score
    results = pd.DataFrame({"median_score": median_score_per_convo, 
                            "bot_name": [c['bot_name'] for c in loaded_convos],
                            "time_created": [c['time_created'] for c in loaded_convos]})
    
    print(results)

    n = 2
    
    worst_n = results.sort_values(by='median_score').reset_index().iloc[:n]
    best_n = results.sort_values(by='median_score').reset_index().iloc[-n:]

    print(worst_n)
    print(best_n)

    # show the worst & best conversation with highlighted sentence scores

    worst_convo_ind = results['median_score'].argmin()
    best_convo_ind = results['median_score'].argmax()

    fig, axes = plt.subplots(1, 1, sharey=True, dpi=300)
    fig.suptitle('Word-level log probabilities')
    sns.heatmap(ax=axes, 
                data=np.array(convo_sentence_scores[worst_convo_ind]).reshape(-1,1), 
                annot=np.array(loaded_convos[worst_convo_ind]['utterances']).reshape(-1,1), 
                fmt='', 
                cmap="mako", 
                vmin=-10, 
                vmax=20, 
                cbar=True, 
                xticklabels=False, 
                yticklabels=False)
    plt.plot()
    

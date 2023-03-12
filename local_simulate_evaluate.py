import time
import os
import json
import typing
import random
import torch
import numpy as np
import seaborn as sns
import pandas as pd
import matplotlib.pyplot as plt

from hovor.core import run_interaction, simulate_interaction
from local_run_utils import *
from typing import List, Callable
from transformers import AutoTokenizer, BertForNextSentencePrediction


def run_local_conversation(output_files_path):
    simulate_interaction(initialize_local_run(output_files_path))


def simulate_local_conversation(output_files_path, log_output_dir):
    if not os.path.exists(log_output_dir):
        os.mkdir(log_output_dir)
    # don't launch the server every time
    simulate_interaction(initialize_local_run_simulated(output_files_path, launch_server=False), output_dir=log_output_dir)

def simulate_local_conversations(output_files_path, log_output_dir, n_convos, sleep_time=0):

    # launch the server once at the start
    print('Launching the server...')
    run_rasa_model_server(output_files_path)
    print('Server should be launched! Now simulating conversations...')


    for i in range(n_convos):
        print(f"Simulating conversation {i}...")
        simulate_local_conversation(
            output_files_path,
            log_output_dir)
        time.sleep(sleep_time)

def load_detailed_jsons(ds_path):
    convos = [] # list of dicts
    for fpath in os.listdir(ds_path):
        if fpath[-5:]=='.json':
            with open(os.path.join(ds_path, fpath), 'r') as fin:     
                data = json.load(fin)
                utterances = []
                action_types = []
                action_names = []
                
                for pair in data['messages']:
                    if pair['agent_message'] is not None:
                        utterances.append(pair['agent_message'])
                        action_types.append(pair['action_type'])
                        action_names.append(pair['action'])
                    if pair['user_message'] is not None:
                        utterances.append(pair['user_message'])
                        action_types.append(pair['action_type'])
                        action_names.append(pair['action'])
                        
                convo = {
                    "bot_name": data['metadata']['bot_name'],
                    "time_created": data['metadata']['time_created'],
                    "utterances": utterances,
                    "action_names": action_names,
                    "action_types": action_types
                }    
                        
                
                convos.append(convo)
    return convos

def sample_except_ind(items, n_samples, ind_to_except):
    """
    A helper function to randomly sample items except for a given item. 
    """
    inds = list(range(len(items)))
    inds.remove(ind_to_except)
    selected_inds = random.sample(inds, n_samples)
    
    return [items[i] for i in selected_inds]

def score_sentences(sentences: List[str], 
                    sentence_scorer: Callable[[str, str], float],
                    n_pretext_sentences: int = 5, 
                    sentence_inds: List[int] = None, 
                    verbose: int = 3, 
                    random_pretext: bool = False) -> List[float]:
    """
    A function that will apply a sentence scorer to each sentence in a list of sentences. 
    It will provide the specified amount of pretext.
    This will use a function that scores a sentence & prefix pair from parameter.
    """
    
    sentence_results = []
    n_sentences = len(sentences)
    
    for i, sentence in enumerate(sentences):
        if sentence_inds is not None and i not in sentence_inds:
            print('Skipping sentence '+ str(i))
            sentence_results.append(None)
            continue
        
        # get pretext
        if random_pretext:
            # random sample of sentences to be pretext, except for the target sentence
            pretext = sample_except_ind(sentences, min(n_pretext_sentences, i), i)
        else:
            pretext = sentences[max(0, i-n_pretext_sentences):i]
        pretext = ' '.join(pretext)
        
        if verbose>1:
            print('---------------------------------------------------------------------------------------------------------------------------------------------')
            print('Pretext = ' + pretext)
            print(f'Sentence {i} = ' + sentence)
        
        sentence_result = sentence_scorer(pretext, sentence)
        sentence_results.append(sentence_result)
        if verbose>0:
            print(f'For Sentence {i}/{n_sentences}: \tThe score is: {sentence_result:.2f}')
        
    
    return sentence_results

def experiment_diologues_no_agg(articles: List[List[str]], scorer_function: Callable[[str, str], float], n_pretext_sentences: int = 5):
    """
    A function to run a comparison of a sentence scorer function applied to a list of articles,
    first with some pretext and second with random pretext from the article. 
    """
    experiment_results_per_article = []
    for i, article in enumerate(articles):

        print('------------------------------------------------------------------------------------------------------')
        print(f'Scoring sentences in article {i}...')
        sentence_scores_a = score_sentences(article, scorer_function, n_pretext_sentences=n_pretext_sentences, verbose=0)

        print('Saving results...')
        experiment_results_per_article.append(sentence_scores_a)
    return experiment_results_per_article

def build_score_sentence_nsp_function_bert():
    """
    Since we don't want to instantiate a new bert model or tokenizer
    inside the score_sentence_nsp function, we use a function that 
    builds these models into the function and returns the ready
    to use function object. 

    A different version of the function could build in a different 
    NSP model, but this one uses BERT. 
    """

    tokenizer = AutoTokenizer.from_pretrained("bert-base-uncased")
    model = BertForNextSentencePrediction.from_pretrained("bert-base-uncased")

    def score_sentence_nsp(previous: str, current: str) -> float:

        encoding = tokenizer(previous, current, return_tensors="pt")
        # print(encoding)
        outputs = model(**encoding, labels=torch.LongTensor([1]))
        # return logits
        # return outputs.logits
        result = outputs.logits[0, 0] - outputs.logits[0, 1]
        return result.item()
    
    return score_sentence_nsp


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
    convo_sentence_scores = experiment_diologues_no_agg([c['utterances'] for c in loaded_convos], 
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
    

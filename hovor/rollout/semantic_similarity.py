from typing import List, Dict
import requests
import numpy as np

api_token = ""
API_URL = "https://api-inference.huggingface.co/models/sentence-transformers/all-MiniLM-L6-v2"
headers = {"Authorization": f"Bearer {api_token}"}


def softmax(x):
    return(np.exp(x)/np.exp(x).sum())

def query(payload):
    response = requests.post(API_URL, headers=headers, json=payload)
    return response.json()

def semantic_similarity(source_sentence: str, sentences: List[str]):
    return sum(query(
    {
        "inputs": {
            "source_sentence": source_sentence,
            "sentences": sentences
        }
    }))/len(sentences)

def softmax_action_confidences(action_confidences: Dict):
    softmax_conversions = list(softmax(list(action_confidences.values())))
    index = 0
    for action in action_confidences:
        action_confidences[action] = softmax_conversions[index]
        index += 1
    return action_confidences

def get_action_confidences(configuration_data, source_sentence, applicable_actions):
    if len(applicable_actions) == 1:
        return {list(applicable_actions)[0]: 1.0}
    action_message_map = {act: configuration_data["actions"][act]["message_variants"] for act in applicable_actions if configuration_data["actions"][act]["message_variants"]}
    confidences = {}
    for action, messages in action_message_map.items():
        confidences[action] = semantic_similarity(source_sentence, messages)
    return softmax_action_confidences({k: v for k, v in sorted(confidences.items(), key=lambda item: item[1], reverse=True)})

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
    return query(
    {
        "inputs": {
            "source_sentence": source_sentence,
            "sentences": sentences
        }
    })

def softmax_action_confidences(action_confidences: Dict):
    softmax_conversions = [array[0] for array in softmax(list(action_confidences.values()))]
    index = 0
    for action in action_confidences:
        action_confidences[action] = softmax_conversions[index]
        index += 1
    return action_confidences


if __name__ == "__main__":
    print(semantic_similarity("I'm very happy", ["I'm filled with happiness", "I'm happy"]))
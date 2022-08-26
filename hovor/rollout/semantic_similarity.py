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

def softmax_confidences(confidences: Dict):
    softmax_conversions = list(softmax(list(confidences.values())))
    index = 0
    for action in confidences:
        confidences[action] = softmax_conversions[index]
        index += 1
    return confidences

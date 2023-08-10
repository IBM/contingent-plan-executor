from typing import List, Dict
import requests
import numpy as np

api_token = ""
API_URL = (
    "https://api-inference.huggingface.co/models/sentence-transformers/all-MiniLM-L6-v2"
)


def softmax(x):
    return np.exp(x) / np.exp(x).sum()


def query(payload):
    headers = {"Authorization": f"Bearer {api_token}"}
    response = requests.post(API_URL, headers=headers, json=payload)
    return response.json()


def semantic_similarity(source_sentence: str, sentences: List[str]):
    return sum(
        query({"inputs": {"source_sentence": source_sentence, "sentences": sentences}})
    ) / len(sentences)


def softmax_confidences(ranked_groups: List[Dict]):
    pure_confidences = [rank["confidence"] for rank in ranked_groups]
    softmax_conversions = list(softmax(pure_confidences))
    for idx in range(len(ranked_groups)):
        ranked_groups[idx]["confidence"] = softmax_conversions[idx]


def normalize_confidences(confidences: Dict):
    total = sum(confidences.values())
    for action in confidences:
        confidences[action] = confidences[action] / total
    return confidences

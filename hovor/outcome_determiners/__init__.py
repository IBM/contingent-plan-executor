import nltk
import subprocess
from time import sleep
import spacy

ws_action_outcome_determiner_config = []
all_entities = {}
nltk.download('wordnet')
nltk.download('omw-1.4')

SPACY_LABELS = spacy.load("en_core_web_md").get_pipe("ner").labels

import nltk
import subprocess
from time import sleep
import spacy

ws_action_outcome_determiner_config = []
all_entities = {}
nltk.download('wordnet')
nltk.download('omw-1.4')

try:
    SPACY_LABELS = spacy.load("en_core_web_md").get_pipe("ner").labels
except OSError:
    # download and wait for completion
    subprocess.run(["python -m spacy download en_core_web_md"])
    SPACY_LABELS = spacy.load("en_core_web_md").get_pipe("ner").labels

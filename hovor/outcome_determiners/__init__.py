import nltk
import subprocess
from time import sleep
import spacy

ws_action_outcome_determiner_config = []
all_entities = {}
nltk.download('wordnet')
nltk.download('omw-1.4')
subprocess.Popen("./spacy_setup.sh", shell=True)
while True:
    try:
        SPACY_LABELS = spacy.load("en_core_web_md").get_pipe("ner").labels
    except OSError:
        sleep(0.1)
    else:
        break


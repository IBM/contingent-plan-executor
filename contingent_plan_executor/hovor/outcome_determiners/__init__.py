import nltk
import spacy

nltk.download('wordnet')
nltk.download('omw-1.4')

SPACY_LABELS = spacy.load("en_core_web_md").get_pipe("ner").labels

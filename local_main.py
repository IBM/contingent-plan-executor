from hovor.core import run_interaction
from local_run_utils import *

def run_local_conversation(output_files_path):
    run_interaction(initialize_local_run(output_files_path))

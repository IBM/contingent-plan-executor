from hovor.core import run_interaction
from hovor.local_run_utils import *

def run_local_conversation(output_files_path):
    run_interaction(initialize_local_run(output_files_path))

if __name__ == "__main__":
    run_local_conversation("C:\\Users\\Rebecca\\Desktop\\plan4dial\\plan4dial\\local_data\\gold_standard_bot\\output_files")
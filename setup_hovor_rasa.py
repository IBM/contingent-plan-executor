import json
from rasa.model_training import train_nlu

def setup_hovor_rasa(domain_name: str, train: bool=True):
    # TODO: also set up parsing YAML, building directories, etc. here
    # (will have to merge directories first).
    with open(f"./{domain_name}/policy.out") as f:
        plan_data = json.load(f)
    plan_data = {f"plan": plan_data}
    with open(f"./{domain_name}/{domain_name}.prp.json", 'w') as f:
        json.dump(plan_data, f, indent=4)
    if train:
        # train rasa nlu
        train_nlu(
            config=f"./{domain_name}/config.yml",
            nlu_data=f"./{domain_name}/nlu.yml",
            output=f"./{domain_name}",
            fixed_model_name=f"{domain_name}-model"
        )
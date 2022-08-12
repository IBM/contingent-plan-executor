from hovor.outcome_determiners.rasa_outcome_determiner import RasaOutcomeDeterminer
from hovor.rollout.semantic_similarity import get_action_confidences

def get_k_action_confidences(k, data, utterance, applicable_actions):
    k_confidences = {}
    result = get_action_confidences(data, utterance, applicable_actions)
    if len(result) > k:
        keys = list(result.keys())
        for i in range(k):
            k_confidences[keys[i]] = result[keys[i]]
        return k_confidences
    else:
        return result

def get_k_highest_intents(k, configuration_provider, action, utterance):
    data = configuration_provider._configuration_data
    rasa_outcome_determiner = RasaOutcomeDeterminer(data["actions"][action]["effect"]["outcomes"], data["context-variables"], data["intents"])
    outcome_groups = configuration_provider._create_outcome_group(action, data["actions"][action]["effect"])._outcome_groups
    chosen_intent, entities, ranked_groups = rasa_outcome_determiner.get_final_rankings(utterance, outcome_groups)
    return ranked_groups[:k]

def get_applicable_actions(state, all_actions):
    return {act for act in all_actions if all_actions[act]["condition"].issubset(state)}

def update_state(state, new_fluents):
    for f in new_fluents:
        if "NegatedAtom" in f:
            raw_f = f.split("NegatedAtom ")[1][:-2]
            if f"Atom {raw_f}()" in state:
                state.remove(f"Atom {raw_f}()")
            state.add(f)
        else:
            raw_f = f.split("Atom ")[1][:-2]
            if f"NegatedAtom {raw_f}()" in state:
                state.remove(f"NegatedAtom {raw_f}()")
            state.add(f)
    return state

def run_partial_conversation(k, configuration_provider, rollout_cfg, conversation):
    data = configuration_provider._configuration_data

    for act in data["actions"]:
        data["actions"][act]["name"] = act

    applicable_actions = set()
    for act_cfg in rollout_cfg["actions"].values():
        act_cfg["condition"] = set(act_cfg["condition"])
        for out, out_vals in act_cfg["effect"].items():
            act_cfg["effect"][out] = set(out_vals)
    current_state = set(rollout_cfg["initial_state"])
    applicable_actions = get_applicable_actions(current_state, rollout_cfg["actions"])
    if len(applicable_actions) == 0:
        raise AssertionError("No valid initial state.")
    elif len(applicable_actions) > 1:
        raise AssertionError("Initial state is ambiguous.")

    for i in range(len(conversation)):
        most_conf_action = list(get_k_action_confidences(1, data, conversation[i]["HOVOR"], applicable_actions).keys())[0]
        most_conf_intent_out = get_k_highest_intents(1, configuration_provider, most_conf_action, conversation[i]["USER"])[0]
        current_state = update_state(current_state, rollout_cfg["actions"][most_conf_action]["effect"][most_conf_intent_out["outcome"].name])
        applicable_actions = get_applicable_actions(current_state, rollout_cfg["actions"])
        
    # TODO: return either action confidence or intent ranking depending on the point of the conversation
    print()

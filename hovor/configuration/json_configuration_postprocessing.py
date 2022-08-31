from copy import deepcopy


def hovor_config_postprocess(hovor_config):
    """
    Improves the config structure so it can be easier parsed.
    Probably this could/should be done inside MAI
    :param hovor_config:
    :return:
    """

    config = deepcopy(hovor_config)

    add_goal_action(config)
    add_subtypes(config)
    add_outcome_determiner_names(config)
    unify_updates(config)
    add_entity_definitions(config)
    fix_context_entity_determiner_configuration(config)
    fix_disambiguation_outcome_determiner_configuration(config)
    fix_web_actions(config)
    fix_web_actions_outcomes(config)
    fix_regex_outcome_determiner(config)
    change_dialogue_to_message_for_single_outcome(config)

    return config


def change_dialogue_to_message_for_single_outcome(config):
    for action in config["actions"].values():
        if action["type"] != "dialogue":
            continue

        if len(action["effect"]["outcomes"]) != 1:
            continue

        action["type"] = "message"
        action["effect"].update(action["effect"]["outcomes"][0])
        action["effect"]["type"] = None


def fix_web_actions_outcomes(config):
    for action in config["actions"].values():
        if action["type"] != "api":
            continue

        for index, outcome in enumerate(action["effect"]["outcomes"]):
            if "outcome_index" in outcome:
                raise ValueError("Config was fixed probably, remove this fix")

            outcome["outcome_index"] = outcome["name"]
            for variable in outcome["variable_list"]:
                outcome["updates"][variable] = {
                    "variable": variable,
                    "value": "$" + variable,
                    "certainty": "Known",
                    "interpretation": "spel"
                }


def fix_web_actions(config):
    for action in config["actions"].values():
        if action["type"] != "api":
            continue

        if "url" in action:
            raise ValueError("Config was fixed probably, remove this fix")

        action["url"] = action["call"]["endpoint"]
        action["default_payload"] = action["call"]["initial_payload"]
        action["effect"]["outcome_determiner"] = "web_call_outcome_determiner"

        action["posted_context_variables"] = posted_context_variables = []
        for condition in action["condition"]:
            posted_context_variables.append(condition[0])


def fix_disambiguation_outcome_determiner_configuration(config):
    for action in config["actions"].values():
        effect = action["effect"]
        if effect["outcome_determiner"] != "disambiguation_outcome_determiner":
            continue

        if "intents" in effect:
            raise ValueError("Intents were added to configuration on the right place. Remove this.")

        intents = {}
        intent_configs = action["intents"]
        for intent, intent_config in intent_configs.items():
            intents[intent] = intent_config["utterances"]

        effect["intents"] = intents

        entities_to_recognize = set()
        for outcome in effect["outcomes"]:
            entities_to_recognize.update(outcome["entity_requirements"].keys())

        effect["entities_to_recognize"] = entities_to_recognize


def fix_context_entity_determiner_configuration(config):
    for action in config["actions"].values():
        effect = action["effect"]
        if effect["outcome_determiner"] != "context_entity_outcome_determiner":
            continue

        if "example_utterances" in effect:
            raise ValueError("Examples were added to configuration on the right place. Remove this.")

        effect["example_utterances"] = action["utterances"]

        entities_to_recognize = set()
        for outcome in effect["outcomes"]:
            entities_to_recognize.update(outcome["entity_requirements"].keys())

        effect["entities_to_recognize"] = entities_to_recognize


def add_subtypes(config):
    for action in config["actions"].values():
        if "subtype" not in action:
            action["subtype"] = None


def add_goal_action(config):
    goal_action_name = "---"
    if goal_action_name in config["actions"]:
        raise ValueError("Action was probably done into the config - remove this postprocess")

    config["actions"][goal_action_name] = {
        "type": "goal_achieved",
        "effect": {
            "global-outcome-name": "END",
            "entity_requirements": {},
            "updates": {},
            "outcomes": []
        }
    }


def add_outcome_determiner_names(config):
    for action_name, action_config in config["actions"].items():
        outcome_determiner = map_action_to_outcome_determiner(action_config)
        action_config["effect"]["outcome_determiner"] = outcome_determiner


def unify_updates(config):
    for action_name, action_config in config["actions"].items():
        for outcome in action_config["effect"]["outcomes"]:
            if "assignments" in outcome:
                if "updates" not in outcome:
                    outcome["updates"] = {}

                # add implicit updates (they should be explicitly written in the config)
                for target_var, value in outcome["assignments"].items():
                    if target_var[1:] not in outcome["updates"]:
                        if value not in ["found", "maybe-found", "didnt-find"]:
                            raise ValueError(f"Unexpected value found in the config {value}")

                        if value in ["didnt-find"]:
                            # we don't want to assign this
                            continue

                        if not target_var.startswith("$"):
                            ValueError("Inconsistent variable names detected: " + str(target_var))

                        outcome["updates"][target_var[1:]] = {
                            "variable": target_var[1:],
                            "value": target_var,
                            "certainty": "Known",
                            "interpretation": "spel"
                        }


def add_entity_definitions(config):
    for action_name, action_config in config["actions"].items():
        for outcome in action_config["effect"]["outcomes"]:
            if "entity_requirements" in outcome:
                raise ValueError("this field was added to config probably")

            outcome["entity_requirements"] = entity_requirements = {}

            if "variable_list" in outcome:
                for variable in outcome["variable_list"]:
                    entity_requirements[variable] = "found"

            elif "assignments" in outcome:
                for variable, assignment_type in outcome["assignments"].items():
                    if not variable.startswith("$"):
                        ValueError("Inconsistent variable names")

                    variable = variable[1:]
                    if assignment_type in ["found", "maybe-found", "didnt-find"]:
                        entity_requirements[variable] = assignment_type
                    else:
                        raise ValueError(f"Unknown assignment type {assignment_type}")

            elif action_config["type"] == "api":
                pass  # no entity definitions here
            elif action_config["type"] == "system":
                pass

            else:
                raise NotImplementedError(f"Unknown type {action_config['type']}")


def map_action_to_outcome_determiner(action):
    a = action["type"]
    st = action["subtype"]

    if a == "system" and st == "Logic based determination":
        return "logic_outcome_determiner"

    if a == "system" and st == "Context dependent determination":
        return "context_dependent_outcome_determiner"

    if a == "system":
        return "default_system_outcome_determiner"

    if a == "api" or a == "goal_achieved":
        return "random_outcome_determiner"

    if a == "dialogue":
        if st == "Context entity extraction":
            return "context_entity_outcome_determiner"

        return "disambiguation_outcome_determiner"

    raise NotImplementedError(f"Unknown action type {a}")


def fix_regex_outcome_determiner(config):
    for action in config["actions"].values():
        if action["effect"]["outcome_determiner"] != "disambiguation_outcome_determiner":
            continue

        for intent_definition in action["intents"].values():
            for utterance in intent_definition["utterances"]:
                if "[regex]{" in utterance:
                    action["effect"]["outcome_determiner"] = "regex_disambiguation_outcome_determiner"

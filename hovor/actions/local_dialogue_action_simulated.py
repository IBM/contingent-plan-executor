import random
import re
import yaml
import json

from hovor.actions.local_dialogue_action import LocalDialogueAction
from hovor.outcome_determiners.random_outcome_determiner import RandomOutcomeDeterminer
from hovor.outcome_determiners.workspace_outcome_determiner import WorkspaceOutcomeDeterminer


class LocalDialogueActionSimulated(LocalDialogueAction):
    """Dialogue type of action - simulated version."""

    _apply_message_grouping = False

    def __init__(self, *args):
        super().__init__(*args)
        self.is_external = False
        self._utterance = "HOVOR: " + \
            random.choice(self.config["message_variants"])
        self._utterance = LocalDialogueActionSimulated.replace_pattern_entities(
            self._utterance, self.context)
        # this is only used in the deprecated method of generating a response
        # with open("/home/jacob/Dev/plan4dial/plan4dial/local_data/gold_standard_bot/output_files/nlu.yml") as fin:
        #     intents = yaml.safe_load(fin)
        # self.intents = intents['nlu']
        # This is used in the process of generating a response
        with open("/home/jacob/Dev/plan4dial/plan4dial/local_data/gold_standard_bot/output_files/data.json") as fin:
            data = json.load(fin)
        self.data = data

    def fill_params(self, utterance):
        # This regex allows me to grab each part:
        # re.sub(r'\[(.*?)\]\{\"entity\": \"(.*?)\", \"value\": \"(.*?)\"\}', r'\3', chosen_example)

        # This regex will replace the []{} block and the stuff inside with just
        # the stuff inside the []
        return re.sub(r'\[(.*?)\]\{(.*?)\}', r'\1', utterance)

    def get_entities_from_string(self, example):
        # takes in something like:

        # I have a [low]{"entity": "budget", "value": "low"} budget
        # and I would prefer a [high-energy]{"entity": "outing_type",
        # "value": "high-energy"} atmosphere today.

        # and returns the required entities
        # this will get the json part of the entity in the example:
        entity_jsons = [s.group() for s in re.finditer(r'\{(.*?)\}', example)]
        entity_dicts = [json.loads(s) for s in entity_jsons]
        return entity_dicts

    def get_entity_names_from_string(self, example):
        entity_dicts = self.get_entities_from_string(example)
        return [x['entity'] for x in entity_dicts]

    def get_intent_examples(self, intent):
        return [s.strip() for s in intent['examples'].strip('-').strip().split('\n-')]

    def example_spacy_entity(self, category):
        """
        Since Spacy won't generate a given entity type from nothing,
        I made this function which can generate a random example for
        each category of named entities.
        """
        examples = {
            "GPE": ['Kingston', 'Toronto'],
            "NORP": ['The Liberal Party of Canada', 'The Conservative Party of Canada'],
            "FAC": ['Toronto Pearson Airport', 'Golden Gate Bridge'],
            "ORG": ['Amazon', "Queen's University"],
            "PERSON": ['Ryan Reynolds', 'Harry Potter'],
            "LOC": ['Africa', 'Mount Everest'],
            "PRODUCT": ['Mazda 3', 'Smartphone'],
            "EVENT": ['Olympic Games', 'Christmas'],
            "WORK_OF_ART": ['Mona Lisa', 'The Starry Night'],
            "LAW": ['The Civil Rights Act', 'The Patriot Act'],
            "LANGUAGE": ['English', 'French'],
            "DATE": ['16th Janurary 2017', 'November 12th'],
            "TIME": ['ten minutes', 'four hours'],
            "PERCENT": ['sixty percent', '20%'],
            "MONEY": ['fifty dollars', '5 cents'],
            "QUANTITY": ['Several kilometers', '60kg'],
            "ORDINAL": ['9th', 'Ninth'],
            "CARDINAL": ['2', 'Three'],
        }
        if category.upper() not in examples:
            return None
        return random.choice(examples[category.upper()])

    def get_random_value_for_var(self, var_name):
        cv = self.data['context_variables'][var_name]
        if cv['type'] == 'enum':
            return random.choice(cv['config'])
        elif cv['type'] == 'json' and cv['config']['extraction']['method'] == 'spacy':
            return self.example_spacy_entity(cv['config']['extraction']['config_method'])
        else:
            raise TypeError(
                "Tried to fill in a non-enum or json var. Only enums and jsons are currently supported. ")

    def fill_dollar_vars(self, s):
        if '$' not in s:
            return s
        # finds the word starting with $ without the $
        var_names = re.findall(r'\$(\w+)', s)
        # get random values for these
        random_var_values = [
            self.get_random_value_for_var(n) for n in var_names]
        # sub them into the string
        for i in range(len(var_names)):
            # only replace the first element incase there are two of same type vars
            s = s.replace('$'+var_names[i], random_var_values[i], 1)
        return s

    def generate_response_by_required_entities(self):
        """
        A function that picks a random outcome group from self,
        extracts the required entities in a response,
        picks a random example of each intent,
        filters these examples to ones that have the same entities as the required entities,
        and returns a random choice from the possible examples as the response.

        This works well for share_cuisine or share_outing_type,
        but does not work well when the bot asks if you have allergies Y/N
        because there are no entities in the deny / confirm entities that can
        be extracted to match w required entity 'has_allergy'. 
        """
        random_sensible_outcome_group = random.choice(
            self.outcome_group._outcome_groups)
        entities_needed = random_sensible_outcome_group.required_present_entities

        random_example_per_intent = [random.choice(
            self.get_intent_examples(i)) for i in self.intents]
        possible_examples = [x for x in random_example_per_intent if set(
            self.get_entity_names_from_string(x)) == entities_needed]
        chosen_example = random.choice(possible_examples)

        simulated_input = self.fill_params(chosen_example)
        return simulated_input

    def generate_response_by_data(self):
        """
        A function that picks a random outcome group from self,
        and uses the information in data.json to find an appropriate response.
        It will see if the intent is named directly, otherwise it will look at
        the required entities and select an intent that has those entities.

        This works well and produces a reasonable conversation. It works for intents
        which don't have entities too. 
        """
        current_action_name = self.name
        possible_outcomes = self.data['actions'][current_action_name]['effect']['outcomes']
        outcome_intent_names = [outcome['intent']
                                for outcome in possible_outcomes]
        possible_intent_names = [
            intent_name for intent_name in outcome_intent_names if self.data['intents'][intent_name]['type'] != 'fallback']
        random_outcome_intent_name = random.choice(possible_intent_names)
        if isinstance(random_outcome_intent_name, str):
            # get the intent name and find the intent in data.json
            # randomly pick an utterance
            # use regex to replace variable with random variable from enum values
            # in data.json
            # done
            random_intent = self.data['intents'][random_outcome_intent_name]
            if len(random_intent['utterances']) != 0:
                random_utterance = random.choice(random_intent['utterances'])
                simulated_input = self.fill_dollar_vars(random_utterance)
            else:
                # must be fallback, there are no utterances for this intent
                simulated_input = "I'm not sure."
        elif isinstance(random_outcome_intent_name, dict):
            # we need to grab the keys and find an intent which has these vars
            var_names = random_outcome_intent_name.keys()
            possible_intent_names = []
            for intent_name in self.data['intents'].keys():
                if set(self.data['intents'][intent_name]['variables']) == {'$'+s for s in var_names} and self.data['intents'][intent_name]['type'] != 'fallback':
                    possible_intent_names.append(intent_name)
            random_intent_name = random.choice(possible_intent_names)
            random_intent_data = self.data['intents'][random_intent_name]
            random_utterance = random.choice(random_intent_data['utterances'])
            simulated_input = self.fill_dollar_vars(random_utterance)
        else:
            raise TypeError('Expected the intent to be string or dict. ')

        return simulated_input

    def _end_execution_callback(self, action_result, info):
        if self.action_type == "dialogue":
            LocalDialogueAction._apply_message_grouping = False

            simulated_input = self.generate_response_by_data()

            print(f'USER - SIMULATED: {simulated_input}')
            action_result.set_field("input", simulated_input)
        else:
            LocalDialogueAction._apply_message_grouping = True

from typing import Dict
from hovor.outcome_determiners.outcome_determiner_base import OutcomeDeterminerBase
from hovor import DEBUG
import requests
import json
import spacy
import random
from nltk.corpus import wordnet
LABELS = spacy.load("en_core_web_md").get_pipe("ner").labels

class RasaOutcomeDeterminer(OutcomeDeterminerBase):
    """Determiner"""
    def __init__(self, full_outcomes, context_variables, intents):
        self.full_outcomes = {outcome["name"]: outcome for outcome in full_outcomes}
        self.context_variables = context_variables
        self.intents = intents

    @staticmethod
    def find_rasa_entity(entity: str, rasa_entities: Dict):
        if entity in rasa_entities:
            return rasa_entities[entity]

    @staticmethod
    def find_spacy_entity(method: str, spacy_entities: Dict):
        if method in spacy_entities:
            if spacy_entities[method]:
                return spacy_entities[method].pop()

    def rank_groups(self, outcome_groups, progress):   
        payload = {'text': progress.json["action_result"]["fields"]["input"]}
        r = json.loads(requests.post('http://localhost:5005/model/parse', json=payload).text)
        print(json.dumps(r, indent=4))

        ranked_groups = []
        intent_to_outcome_map = {}
        for outcome in outcome_groups:
            intent_to_outcome_map[self.full_outcomes[outcome.name]["intent"]] = outcome

        spacy_entities = {}
        rasa_entities = {}
        for extracted in r["entities"]:
            if extracted["entity"] in LABELS:
                if extracted["entity"] in spacy_entities:
                    spacy_entities[extracted["entity"]].append(extracted)
                else:
                    spacy_entities[extracted["entity"]] = [extracted]
            else:
                rasa_entities[extracted["entity"]] = extracted   
        entities = {}
        chosen_intent = None
        for intent in r["intent_ranking"]:
            if intent["name"] in intent_to_outcome_map:
                unsure = False
                valid = True
                # if this intent expects entities, make sure we extract them
                if len(self.intents[intent["name"]]["variables"]) > 0:
                    for entity in self.intents[intent["name"]]["variables"]:
                        # get rid of $
                        entity = entity[1:]
                        # spacy
                        if type(self.context_variables[entity]["config"]) == dict:
                            if self.context_variables[entity]["config"]["extraction"] == "spacy":
                                extracted = RasaOutcomeDeterminer.find_spacy_entity(self.context_variables[entity]["config"]["method"].upper(), spacy_entities)
                                if not extracted:
                                    extracted = RasaOutcomeDeterminer.find_rasa_entity(entity)
                                    unsure = True
                                if extracted:
                                    entities[entity] = extracted
                        # rasa
                        else:
                            extracted = RasaOutcomeDeterminer.find_rasa_entity(entity, rasa_entities)
                            if not extracted:
                                if spacy_entities.values():
                                    extracted = []
                                    extracted.extend(val for method_vals in spacy_entities.values() for val in method_vals)
                                    extracted = random.choice(extracted)
                                    unsure = True
                            if extracted:
                                entities[entity] = extracted

                        # break and proceed to the next intent if we weren't able to find the next entity
                        if not extracted:
                            valid = False
                            break
                    if valid:
                        # stop looking for a suitable intent if we found all entities
                        chosen_intent = intent
                        break
                else:
                    # stop looking for a suitable intent if the intent extracted doesn't require entities
                    chosen_intent = intent
                    break
        if not chosen_intent:
            ranked_groups = [i for i in r["intent_ranking"] if i["name"] in intent_to_outcome_map]
            ranked_groups = [{"name": "fallback", "confidence": 1.0}] + ranked_groups
            ranked_groups = [(intent_to_outcome_map[intent["name"]], intent["confidence"]) for intent in ranked_groups]     
        else:
            not_picked = [i for i in r["intent_ranking"] if i["name"] in intent_to_outcome_map]
            not_picked.remove(chosen_intent)
            ranked_groups = [(intent_to_outcome_map[intent["name"]], intent["confidence"]) for intent in [chosen_intent] + not_picked]
            for entity, entity_info in entities.items():
                entity_sample = RasaOutcomeDeterminer._make_entity_sample(entity_info, progress)
                progress.add_detected_entity(entity, entity_sample)        

        DEBUG("\t top random ranking for group '%s'" % (chosen_intent))
        return ranked_groups, progress

    @classmethod
    def _make_entity_sample(cls, entity_info, progress):
        entity_type = progress.get_entity_type(entity_info["entity"])
        entity_config = progress.get_entity_config(entity_info["entity"])
        return cls._make_entity_type_sample(entity_type, entity_config, entity_info)

    @classmethod
    def _make_entity_type_sample(cls, entity_type, entity_config, entity_info):
        extracted = entity_info["value"]
        if entity_type == "enum":
            if extracted in entity_config:
                return extracted
            else:
                for syn in wordnet.synsets(extracted):
                    for l in syn.lemmas():
                        l = l.name()
                        if l in entity_config:
                            return l
                    for hyp in syn.hypernyms():
                        hyp = hyp.name()
                        if hyp in entity_config:
                            return hyp
                    for hyp in syn.hyponyms():
                        hyp = hyp.name()
                        if hyp in entity_config:
                            return hyp
                    for hol in syn.holonyms():
                        hol = hol.name()
                        if hol in entity_config:
                            return hol
        elif entity_type == "json":
            return extracted
        else:
            raise NotImplementedError("Cant sample from type: " + entity_type)

    def _report_sampled_entities(self, top_group, progress):
        # collected_entities = self.find_required_present_entities(outcome_groups)
        pass
        # add the entities like they were really detected during the determination
        # for entity in collected_entities:
        #     entity_sample = RandomOutcomeDeterminer._make_entity_sample(entity, progress)
        #     progress.add_detected_entity(entity, entity_sample)
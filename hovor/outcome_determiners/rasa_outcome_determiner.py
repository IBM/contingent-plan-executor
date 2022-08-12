from typing import Dict
from hovor import outcome_determiners
from hovor.outcome_determiners import SPACY_LABELS
from hovor.outcome_determiners.outcome_determiner_base import OutcomeDeterminerBase
from hovor import DEBUG
import requests
import json
import spacy
import random
from nltk.corpus import wordnet

THRESHOLD = 0.65

class RasaOutcomeDeterminer(OutcomeDeterminerBase):
    """Determiner"""
    def __init__(self, full_outcomes, context_variables, intents):
        self.full_outcomes = {outcome["name"]: outcome for outcome in full_outcomes}
        self.context_variables = context_variables
        self.intents = intents

    @staticmethod
    def parse_synset_name(synset):
        return synset.name().split(".")[0]

    def find_rasa_entity(self, entity: str):
        if entity in self.rasa_entities:
            return self.rasa_entities[entity]

    def find_spacy_entity(self, method: str):
        if method in self.spacy_entities:
            if self.spacy_entities[method]:
                return self.spacy_entities[method].pop()

    def extract_entity(self, entity: str):
        # spacy
        if type(self.context_variables[entity]["config"]) == dict:
            if self.context_variables[entity]["config"]["extraction"] == "spacy":
                extracted = self.find_spacy_entity(self.context_variables[entity]["config"]["method"].upper())
                if not extracted:
                    # if we can't parse with spacy, try with Rasa (may also return None)
                    extracted = self.find_rasa_entity(entity)
                    if not extracted:
                        return
                    certainty = "maybe-found"
                else:
                    certainty = "found"
        # rasa
        else:
            extracted = self.find_rasa_entity(entity)
            if not extracted:
                if self.spacy_entities.values():
                    extracted = []
                    extracted.extend(val for method_vals in self.spacy_entities.values() for val in method_vals)
                    extracted = random.choice(extracted)
                    certainty = "maybe-found"
                else:
                    return
            else:
                certainty = "found"
        return {"extracted": extracted, "value": extracted["value"], "certainty": certainty}

    def extract_entities(self, intent):
        entities = {}
        # get entities from frozenset
        for entity in [f[0] for f in intent["name"]]:
            # raw extract single entity, then validate
            extracted_info = self.extract_entity(entity)
            if extracted_info:
                extracted_info = RasaOutcomeDeterminer._make_entity_type_sample(self.context_variables[entity]["type"], self.context_variables[entity]["config"], extracted_info,)
            else:
                extracted_info = {"certainty": "didnt-find", "sample": None}               
            entities[entity] = extracted_info
        return entities

    def extract_intents(self, r, intent_to_outcome_map, intent_map):
        entities = {}
        chosen_intent = None
        for intent in r["intent_ranking"]:
            if intent["name"] in intent_to_outcome_map:
                # if this intent expects entities, make sure we extract them
                if type(intent["name"]) == frozenset:
                    entities = self.extract_entities(intent)
                    # if no entities were successfully extracted
                    if {entities[e]["sample"] for e in entities} != {None}:
                        chosen_intent = intent
                        chosen_intent["name"] = frozenset({k : v["certainty"] for k, v in entities.items() if v["sample"]}.items())
                        # stop looking for a suitable intent as we have found one that maps to a valid outcome :)
                        # note that this check allows you to use full or partial information depending on how you set up your actions
                        if chosen_intent["name"] in intent_to_outcome_map:
                            break
                        else:
                            # need to reassign to None in case we break on the last intent
                            chosen_intent = None
                else:        
                    if intent["confidence"] > THRESHOLD:
                        # stop looking for a suitable intent if the intent extracted doesn't require entities
                        chosen_intent = intent
                        break
        if chosen_intent:
            not_picked = [i for i in r["intent_ranking"] if i["name"] in intent_to_outcome_map]
            not_picked.remove(chosen_intent)
            intent_ranking = [chosen_intent] + not_picked
        else:
            chosen_intent = "fallback"
            not_picked = [i for i in r["intent_ranking"] if i["name"] in intent_to_outcome_map]
            intent_ranking = [{"name": chosen_intent, "confidence": 1.0}] + not_picked
        ranked_groups = [{"intent": intent_map[intent["name"]]["name"] if intent["name"] in intent_map else intent["name"], "outcome": intent_to_outcome_map[intent["name"]], "confidence": intent["confidence"]} for intent in intent_ranking]
        return chosen_intent, entities, ranked_groups

    def initialize_extracted_entities(self, entities: Dict):
        self.spacy_entities = {}
        self.rasa_entities = {}
        for extracted in entities:
            if extracted["entity"] in SPACY_LABELS:
                if extracted["entity"] in self.spacy_entities:
                    self.spacy_entities[extracted["entity"]].append(extracted)
                else:
                    self.spacy_entities[extracted["entity"]] = [extracted]
            else:
                self.rasa_entities[extracted["entity"]] = extracted

    def rename_intents(self, r):
        intent_map = {}
        for i in range(len(r["intent_ranking"])):
            extracted_intent = r["intent_ranking"][i]
            if len(self.intents[extracted_intent["name"]]["variables"]) > 0:
                new_name = frozenset({v[1:]: "found" for v in self.intents[extracted_intent["name"]]["variables"]}.items())
                intent_map[new_name] = r["intent_ranking"][i]
                r["intent_ranking"][i] = {"name": new_name, "confidence": extracted_intent["confidence"]}
        return intent_map        

    def get_intent_outcome_map(self, outcome_groups):
        intent_to_outcome_map = {}
        for out in outcome_groups:
            intent = self.full_outcomes[out.name]["intent"]
            if type(intent) == dict:
                updated_intent = frozenset(intent.items())
            else:
                updated_intent = intent
                if len(self.intents[intent]["variables"]) > 0:
                    entity_requirements = self.full_outcomes[out.name]["entity_requirements"]
                    if entity_requirements:
                        updated_intent = frozenset(entity_requirements.items())
            intent_to_outcome_map[updated_intent] = out
        return intent_to_outcome_map

    def get_final_rankings(self, input, outcome_groups):
        r = json.loads(requests.post('http://localhost:5005/model/parse', json={"text": input}).text)

        intent_to_outcome_map = self.get_intent_outcome_map(outcome_groups)
        intent_map = self.rename_intents(r)
        self.initialize_extracted_entities(r["entities"])
    
        return self.extract_intents(r, intent_to_outcome_map, intent_map)

    def rank_groups(self, outcome_groups, progress):   
        chosen_intent, entities, ranked_groups = self.get_final_rankings(progress.json["action_result"]["fields"]["input"], outcome_groups)
        ranked_groups = [(intent["outcome"], intent["confidence"]) for intent in ranked_groups]
        if chosen_intent:
            for entity, entity_info in entities.items():
                if "sample" in entity_info:
                    progress.add_detected_entity(entity, entity_info["sample"]) 
        DEBUG("\t top random ranking for group '%s'" % (chosen_intent))
        return ranked_groups, progress

    @classmethod
    def _make_entity_type_sample(cls, entity_type, entity_config, extracted_info):
        entity_value = extracted_info["value"]
        if entity_type == "enum":
            if entity_value in entity_config:
                extracted_info["sample"] = entity_value
                return extracted_info
            else:
                extracted_info["certainty"] = "maybe-found"
                for syn in wordnet.synsets(entity_value):
                    for option in entity_config:
                        if option in syn._definition:
                            extracted_info["sample"] = option
                            return extracted_info
                    for lemma in syn.lemmas():
                        for p in lemma.pertainyms():
                            p = p.name()
                            if p in entity_config:
                                extracted_info["sample"] = p
                                return extracted_info
                        for d in lemma.derivationally_related_forms():
                            d = d.name()
                            if d in entity_config:
                                extracted_info["sample"] = d
                                return extracted_info
                    for hyp in syn.hypernyms():
                        hyp = RasaOutcomeDeterminer.parse_synset_name(hyp)
                        if hyp in entity_config:
                            extracted_info["sample"] = hyp
                            return extracted_info
                    for hyp in syn.hyponyms():
                        hyp = RasaOutcomeDeterminer.parse_synset_name(hyp)
                        if hyp in entity_config:
                            extracted_info["sample"] = hyp
                            return extracted_info
                    for hol in syn.member_holonyms():
                        hol = RasaOutcomeDeterminer.parse_synset_name(hol)
                        if hol in entity_config:
                            extracted_info["sample"] = hol
                            return extracted_info
                    for hol in syn.root_hypernyms():
                        hol = RasaOutcomeDeterminer.parse_synset_name(hol)
                        if hol in entity_config:
                            extracted_info["sample"] = hol
                            return extracted_info
        elif entity_type == "json":
            extracted_info["sample"] = extracted_info["value"]
            return extracted_info
        else:
            raise NotImplementedError("Cant sample from type: " + entity_type)
        extracted_info["certainty"] = "didnt-find"
        extracted_info["sample"] = None
        return extracted_info

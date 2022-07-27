from typing import Dict
from hovor.outcome_determiners.outcome_determiner_base import OutcomeDeterminerBase
from hovor import DEBUG
import requests
import json
import spacy
import random
from copy import deepcopy
from nltk.corpus import wordnet

LABELS = spacy.load("en_core_web_md").get_pipe("ner").labels
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

    def initialize_extracted_entities(self, entities: Dict):
        self.spacy_entities = {}
        self.rasa_entities = {}
        for extracted in entities:
            if extracted["entity"] in LABELS:
                if extracted["entity"] in self.spacy_entities:
                    self.spacy_entities[extracted["entity"]].append(extracted)
                else:
                    self.spacy_entities[extracted["entity"]] = [extracted]
            else:
                self.rasa_entities[extracted["entity"]] = extracted 

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

    def extract_entities(self, intent, progress):
        entities = {}
        # get entities from frozenset
        for entity in [f[0] for f in intent["name"]]:
            # raw extract single entity, then validate
            extracted_info = self.extract_entity(entity)
            if extracted_info:
                extracted_info = RasaOutcomeDeterminer._make_entity_sample(entity, extracted_info, progress)
                if not extracted_info["sample"]:
                    return
            else:
                extracted_info = {"certainty": "didnt-find", "sample": None}               
            # TODO: instead, check if we can map the entities to an outcome
            # have to extract ALL entities to pass
            # else:
            #     return
            entities[entity] = extracted_info
        return entities

    def rank_groups(self, outcome_groups, progress):   
        payload = {'text': progress.json["action_result"]["fields"]["input"]}
        r = json.loads(requests.post('http://localhost:5005/model/parse', json=payload).text)

        ranked_groups = []
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
                    # for i in range(len(r["intent_ranking"])):
                    #     if r["intent_ranking"][i]["name"] == intent:
                    #         r["intent_ranking"][i]["name"] = updated_intent
            intent_to_outcome_map[updated_intent] = out

        for i in range(len(r["intent_ranking"])):
            extracted_intent = r["intent_ranking"][i]
            if len(self.intents[extracted_intent["name"]]["variables"]) > 0:
                r["intent_ranking"][i] = {"name": frozenset({v[1:]: "found" for v in self.intents[extracted_intent["name"]]["variables"]}.items()), "confidence": extracted_intent["confidence"]}

        self.initialize_extracted_entities(r["entities"])
        chosen_intent = None
        entities = {}
        for intent in r["intent_ranking"]:
            if intent["name"] in intent_to_outcome_map:
                # if this intent expects entities, make sure we extract them
                if type(intent["name"]) == frozenset:
                    entities = self.extract_entities(intent, progress)
                    # if no entities were successfully extracted
                    if {entities[e]["sample"] for e in entities} != {None}:
                        # stop looking for a suitable intent if we found all entities
                        chosen_intent = intent
                        # adjust to match clarity if necessary
                        key = {}
                        for entity, entity_config in entities.items():
                            key[entity] = entity_config["certainty"]
                        if "maybe-found" in key.values() or "didnt-find" in key.values():
                            chosen_intent["name"] = frozenset(key.items())
                        break
                else:        
                    if intent["confidence"] > THRESHOLD:
                        # stop looking for a suitable intent if the intent extracted doesn't require entities
                        chosen_intent = intent
                        break
        if chosen_intent:
            not_picked = [i for i in r["intent_ranking"] if i["name"] in intent_to_outcome_map]
            not_picked.remove(chosen_intent)
            ranked_groups = [(intent_to_outcome_map[intent["name"]], intent["confidence"]) for intent in [chosen_intent] + not_picked]
            for entity, entity_info in entities.items():
                if "sample" in entity_info:
                    progress.add_detected_entity(entity, entity_info["sample"])  
        else:
            chosen_intent = "fallback"
            ranked_groups = [i for i in r["intent_ranking"] if i["name"] in intent_to_outcome_map]
            ranked_groups = [{"name": chosen_intent, "confidence": 1.0}] + ranked_groups
            ranked_groups = [(intent_to_outcome_map[intent["name"]], intent["confidence"]) for intent in ranked_groups]     
        DEBUG("\t top random ranking for group '%s'" % (chosen_intent))
        return ranked_groups, progress

    @classmethod
    def _make_entity_sample(cls, entity, extracted_info, progress):
        entity_type = progress.get_entity_type(entity)
        entity_config = progress.get_entity_config(entity)
        return cls._make_entity_type_sample(entity_type, entity_config, extracted_info)

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
        extracted_info["sample"] = None
        return extracted_info

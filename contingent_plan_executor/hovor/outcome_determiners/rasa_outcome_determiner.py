from dataclasses import dataclass
from typing import Dict
from operator import attrgetter
from hovor.outcome_determiners import SPACY_LABELS
from hovor.outcome_determiners.outcome_determiner_base import OutcomeDeterminerBase
from hovor.planning.outcome_groups.deterministic_outcome_group import (
    DeterministicOutcomeGroup,
)
from hovor import DEBUG
import requests
import json
import random
from nltk.corpus import wordnet
from typing import Union
from textblob import TextBlob
import re


@dataclass
class Intent:
    name: str
    entity_reqs: Union[frozenset, None]
    outcome: DeterministicOutcomeGroup
    confidence: float

    def __eq__(self, other):
        return (
            self.name == other.name
            and self.entity_reqs == other.entity_reqs
            and self.outcome == other.outcome
            and self.confidence == other.confidence
        )

    def __lt__(self, other):
        return self.confidence > other.confidence


class RasaOutcomeDeterminer(OutcomeDeterminerBase):
    """Determiner"""

    def __init__(self, action_name, full_outcomes, context_variables, intents):
        self.action_name = action_name
        self.full_outcomes = {outcome["name"]: outcome for outcome in full_outcomes}
        self.context_variables = context_variables
        self.intents = intents
        # cache the extracted entities so we don't have to extract anything multiple times
        self.extracted_entities = {}


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
            if extracted["entity"] in SPACY_LABELS:
                if extracted["entity"] in self.spacy_entities:
                    self.spacy_entities[extracted["entity"]].append(extracted)
                else:
                    self.spacy_entities[extracted["entity"]] = [extracted]
            else:
                self.rasa_entities[extracted["entity"]] = extracted

    def try_rasa_then_spacy(self, entity: str):
        extracted = self.find_rasa_entity(entity)
        if not extracted:
            if self.spacy_entities.values():
                extracted = []
                extracted.extend(
                    val
                    for method_vals in self.spacy_entities.values()
                    for val in method_vals
                )
                extracted = random.choice(extracted)
                certainty = "maybe-found"
            else:
                return None, None
        else:
            certainty = "found"
        return extracted, certainty

    def try_spacy_then_rasa(self, entity: str):
        extracted = self.find_spacy_entity(
            self.context_variables[entity]["config"]["extraction"]["config_method"].upper()
        )
        if not extracted:
            # if we can't parse with spacy, try with Rasa (may also return None)
            extracted = self.find_rasa_entity(entity)
            if not extracted:
                return None, None
            certainty = "maybe-found"
        else:
            certainty = "found"
        return extracted, certainty

    def extract_regex(self, entity):
        """For regexes, it doesn't matter whether spacy or rasa extracted it
        ("regex" is its own category). Just try with either-- results will always be
        found or didnt-find. Also, for spacy, we will only check for "CARDINAL"
        extractions.
        """
        extracted = None

        pattern = self.context_variables[entity]["config"]["extraction"]["pattern"]
        raw_extracted = self.find_rasa_entity(entity)
        if raw_extracted:
            match = re.search(raw_extracted["value"], pattern)
            if match:
                extracted = ext_ent
        if not extracted:
            if self.spacy_entities:
                if "CARDINAL" in self.spacy_entities:
                    # iterate through all CARDINAL entities and see if any match
                    for ext_ent in self.spacy_entities["CARDINAL"]:
                        match = re.search(pattern, ext_ent["value"])
                        if match:
                            extracted = ext_ent
                            break
            else:
                return None, None
        return extracted, "found"

    def extract_entity(self, entity: str):
        # for "complex" json configurations
        if self.context_variables[entity]["type"] == "json":
            # can be either "method" (like spacy) or "pattern" (like a regex)
            method = self.context_variables[entity]["config"]["extraction"]["method"]
            if method == "spacy":
                extracted, certainty = self.try_spacy_then_rasa(entity)
            elif method == "regex":
                extracted, certainty = self.extract_regex(entity)
        # rasa
        else:
            extracted, certainty = self.try_rasa_then_spacy(entity)
        if extracted:
            return {
                "extracted": extracted,
                "value": extracted["value"],
                "certainty": certainty,
            }

    def extract_entities(self, intent):
        entities = {}
        # get entities from frozenset
        for entity in {f[0] for f in intent.entity_reqs}:
            if entity in self.extracted_entities:
                entities[entity] = self.extracted_entities[entity]
            else:
                # raw extract single entity, then validate
                extracted_info = self.extract_entity(entity)
                if extracted_info:
                    extracted_info = self._make_entity_type_sample(
                        entity,
                        self.context_variables[entity]["type"],
                        self.context_variables[entity]["config"],
                        extracted_info,
                    )
                    if extracted_info["sample"] != None:
                        entities[entity] = extracted_info
                    self.extracted_entities[entity] = extracted_info
        return entities

    def filter_intents(self, r, outcome_groups):
        # make outcome groups accessible by name
        outcome_groups = {out.name : out for out in outcome_groups}
        intents_detected = {ranking["name"]: ranking["confidence"] for ranking in r["intent_ranking"]}
        intents = []
        for out, out_cfg in self.full_outcomes.items():
            # check to make sure this intent was at least DETECTED by rasa
            if out_cfg["intent"] in intents_detected:
                if self.intents[out_cfg["intent"]]["entities"]:
                    # we only want to consider assignments that are variables of the intent, as outcomes often
                    # have other updates for existing entities.
                    entity_reqs = {e[1:]:cert for e, cert in out_cfg["assignments"].items() if e in self.intents[out_cfg["intent"]]["entities"]}

                    intents.append(
                        Intent(
                            out_cfg["intent"],
                            # use the assignments key so we get the required certainty for each entity
                            frozenset(entity_reqs.items()),
                            outcome_groups[out],
                            intents_detected[out_cfg["intent"]]
                        )
                    )
                else:
                    intents.append(
                        Intent(
                            out_cfg["intent"],
                            None,
                            outcome_groups[out],
                            intents_detected[out_cfg["intent"]]
                        )
                    )
            elif out_cfg["intent"] == "fallback":
                intents.append(
                    Intent(
                        "fallback",
                        None,
                        outcome_groups[out],
                        0
                    )
                )
        intents.sort()
        return intents

    def extract_intents(self, intents):
        entities = {}
        extracted_intent = None
        for intent in intents:
            # if this intent expects entities, make sure we extract them
            if intent.entity_reqs != None:
                entities = self.extract_entities(intent)
                if intent.entity_reqs == frozenset({entity: entities[entity]["certainty"] for entity in entities if entities[entity]["certainty"] != "didnt-find"}.items()):
                    extracted_intent = intent
                    break
                # need to reassign to None because we only get here if for some reason we weren't
                # able to extract the intent correctly
                extracted_intent = None
                # an intent with entities we were not able to extract gets a confidence of 0
                intent.confidence = 0
            else:
                # stop looking for a suitable intent if the intent extracted doesn't require entities
                extracted_intent = intent
                break
        if extracted_intent:
            # in the case that there are multiple intents with the same name and confidence
            # because we're going by entity assignment, we only want the intent that reflects
            # our extracted entity assignment to be chosen. i.e. at this point, an intent share_cuisine where
            # cuisine is "found" and the sister intent share_cuisine where cuisine is "maybe-found" will
            # have the same confidence, but we only want the right one to be chosen.
            for intent in intents:
                if intent.name == extracted_intent.name and intent.entity_reqs != extracted_intent.entity_reqs:
                    intent.confidence = 0

        for intent in intents:
            if intent.name == "fallback":
                intent.confidence = 1 - max(intents, key=attrgetter("confidence")).confidence
                break

        # rearrange intent ranking
        intents.sort()

        ranked_groups = [
            {
                "intent": intent.name,
                "outcome": intent.outcome,
                "confidence": intent.confidence,
            }
            for intent in intents
        ]
        return intents[0], ranked_groups


    def get_final_rankings(self, input, outcome_groups):
        r = json.loads(
            requests.post(
                "http://localhost:5005/model/parse", json={"text": input}
            ).text
        )
        intents = self.filter_intents(r, outcome_groups)
        self.initialize_extracted_entities(r["entities"])
        return self.extract_intents(intents)

    def rank_groups(self, outcome_groups, progress):
        chosen_intent, ranked_groups = self.get_final_rankings(
            progress.json["action_result"]["fields"]["input"], outcome_groups
        )
        ranked_groups = [
            (intent["outcome"], intent["confidence"]) for intent in ranked_groups
        ]
        # entities required by the extracted intent
        if chosen_intent.entity_reqs:
            ci_ent_reqs = [er[0] for er in chosen_intent.entity_reqs]
        # note we shouldn't only add samples for extracted entities; some outcomes don't
        # extract entities themselves but update the values of existing entities
        for update_var, update_config in progress.get_description(chosen_intent.outcome.name)["updates"].items():
            if "value" in update_config:
                if progress.get_entity_type(update_var) in ["json", "enum"]:
                    value = update_config["value"]
                    # if value is not null
                    if value:
                        # if the value is a variable (check without the $)
                        if value[1:] in progress.actual_context.field_names:
                            value = value[1:]
                            if progress.actual_context._fields[value]:
                                value = progress.actual_context._fields[value]
                            else:
                                # if it is not part of the progress yet and we just extracted entities,
                                if chosen_intent.entity_reqs:
                                    # check if we just extracted it
                                    if value in ci_ent_reqs:
                                        value = self.extracted_entities[value]["sample"]
                                    # otherwise, we tried to assign an entity to a value we don't have yet
                                    else:
                                        raise ValueError("Tried to assign an entity to \
                                                        an unknown variable value.")
                    progress.add_detected_entity(update_var, value)
        DEBUG("\t top random ranking for group '%s'" % (chosen_intent.name))
        return ranked_groups, progress

    def _make_entity_type_sample(self, entity, entity_type, entity_config, extracted_info):
        entity_value = extracted_info["value"]
        # entity is extracted with spacy and has options specified
        spacy_w_opts = (entity_config["extraction"]["method"] == "spacy" and "options" in entity_config) if entity_type == "json" else False
        if spacy_w_opts:
            entity_config = entity_config["options"]
        if spacy_w_opts or entity_type == "enum":
            # lowercase all strings in entity_config, map back to original casing
            entity_config = {e.lower(): e for e in entity_config}
            entity_value = entity_value.lower()
            if entity_value in entity_config:
                extracted_info["sample"] = entity_config[entity_value]
                return extracted_info
            else:
                if "known" in self.context_variables[entity]:
                    if self.context_variables[entity]["known"]["type"] == "fflag":
                        extracted_info["certainty"] = "maybe-found"
                        # first try correcting spelling
                        spell_corrected_e_val = TextBlob(entity_value).correct().raw.lower()
                        if spell_corrected_e_val != entity_value:
                            entity_value = spell_corrected_e_val
                            if entity_value in entity_config:
                                extracted_info["sample"] = entity_config[entity_value]
                                return extracted_info
                        # as a last ditch effort, try to use wordnet to decipher what the user meant
                        for syn in wordnet.synsets(entity_value):
                            for option in entity_config:
                                if option in syn._definition.lower():
                                    extracted_info["sample"] = entity_config[option]
                                    return extracted_info
                            for lemma in syn.lemmas():
                                for p in lemma.pertainyms():
                                    p = p.name().lower()
                                    if p in entity_config:
                                        extracted_info["sample"] = entity_config[p]
                                        return extracted_info
                                for d in lemma.derivationally_related_forms():
                                    d = d.name().lower()
                                    if d in entity_config:
                                        extracted_info["sample"] = entity_config[d]
                                        return extracted_info
                            for hyp in syn.hypernyms():
                                hyp = RasaOutcomeDeterminer.parse_synset_name(hyp).lower()
                                if hyp in entity_config:
                                    extracted_info["sample"] = entity_config[hyp]
                                    return extracted_info
                            for hyp in syn.hyponyms():
                                hyp = RasaOutcomeDeterminer.parse_synset_name(hyp).lower()
                                if hyp in entity_config:
                                    extracted_info["sample"] = entity_config[hyp]
                                    return extracted_info
                            for hol in syn.member_holonyms():
                                hol = RasaOutcomeDeterminer.parse_synset_name(hol).lower()
                                if hol in entity_config:
                                    extracted_info["sample"] = entity_config[hol]
                                    return extracted_info
                            for hol in syn.root_hypernyms():
                                hol = RasaOutcomeDeterminer.parse_synset_name(hol).lower()
                                if hol in entity_config:
                                    extracted_info["sample"] = entity_config[hol]
                                    return extracted_info
        elif entity_type == "json":
            # note: regex would have been checked already, and for spacy w/o options specified just
            # set the entity value
            extracted_info["sample"] = entity_value
            return extracted_info
        else:
            raise NotImplementedError("Cant sample from type: " + entity_type)
        extracted_info["certainty"] = "didnt-find"
        extracted_info["sample"] = None
        return extracted_info

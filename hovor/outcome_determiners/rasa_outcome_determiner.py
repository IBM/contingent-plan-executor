from hovor.outcome_determiners.outcome_determiner_base import OutcomeDeterminerBase
from hovor import DEBUG
import requests
import json
from .random_outcome_determiner import RandomOutcomeDeterminer


class RasaOutcomeDeterminer(OutcomeDeterminerBase):
    """Determiner"""
    def __init__(self, full_outcomes, context_variables):
        self.full_outcomes =  {outcome["name"]: outcome for outcome in full_outcomes}
        self.context_variables = context_variables
    
    def rank_groups(self, outcome_groups, progress):
        import spacy
        nlp = spacy.load("en_core_web_md")
        print(nlp.get_pipe("ner").labels)
        payload = {'text': progress.json["action_result"]["fields"]["input"]}
        r = json.loads(requests.post('http://localhost:5005/model/parse', json=payload).text)
        for info, val in r.items():
            print(f"{info}: {val}\n")
        ranked_groups = []
        intent_to_outcome_map = {}
        for outcome in outcome_groups:
            if "intent" in self.full_outcomes[outcome.name]:
                intent_to_outcome_map[self.full_outcomes[outcome.name]["intent"]] = outcome
        # separate spacy entities from rasa entities
        spacy_entities = {}
        rasa_entities = {}
        # sort by start (necessary in case multiple intenties are extracted, so we can map the
        # spacy ones correctly).
        for extracted in sorted(r["entities"], key=lambda x: x["start"]):
            if extracted["entity"] in nlp.get_pipe("ner").labels:
                spacy_entities[extracted["start"]] = extracted
            else:
                rasa_entities[extracted["start"]] = extracted
        # NOTE: ENTITY EXTRACTION/INTENT SELECTION ALGORITHM
        # we're running into a problem here where we need to pick (spacy) entities by intent, and pick intents based on entities.
        # ultimately the spacy entities really need to be based on intents (no way to map them otherwise). so we should: 
        # (LOOP): iterate through intents in order of confidence.
        #   (LOOP): iterate through the entities this intent expects. for each entity:
        #       check what type it expects (i.e. a simple pizza "order" (pure rasa), or something from spacy).
        #       (IF): something from rasa:
        #           try to match the entity type of any (NLTK pre-processed) pure-rasa entity to this current entity type.
        #       (ELSE): something from spacy:
        #           gather all spacy extractions that match the corresponding entity extraction type (i.e. GPE).
        #           based on the position of the entity, pick the appropriate spacy extraction.
        #           NOTE: clarify how we're supposed to deal with this? how would we know how to "position" spacy extractions,
        #               if there are multiple with the same extraction type (i.e. GPE)?
        #   break as soon as you find an intent where all entities can be filled appropriately
        
        # TODO: fix below code by implementing the above algorithm.

        entities = {}
        for intent in r["intent_ranking"]:
            # if len(r["entities"]) == len(intent_to_outcome_map[intent["name"]].required_present_entities):

            # SECOND: map spacy-extracted entities to user-supplied entities when appropriate
            # NOTE: based on intents
            for spacy_ent in spacy_entities:
                entity_name = spacy_ent["entity"]
                for ent in intent_to_outcome_map[intent["name"]].required_present_entities:
                    if "method" in self.context_variables[ent]["config"]:
                        if self.context_variables[ent]["config"]["method"].upper() == entity_name:
                            entities[ent] = self.context_variables[ent]
                else:
                    if entity_name not in entities:
                        entities[ent] = entity_name
                # NOTE: this just randomly picks from the list of enums (see the enum option)
                # add to the rasa configuration which option is explicitly picked each time.
                # entity "keys" are also sometimes wrongly extracted, i.e. "kingston" is parsed as a
                # payment_method entity. not sure where exactly this is caused (maybe just need more examples,
                # or to attach the appropriate classifiers i.e. spacy, or maybe something else is breaking this?).
                # this entity keys bug causes errors when trying to update values.
                for entity in entities:
                    entity_sample = RandomOutcomeDeterminer._make_entity_sample(entity, progress)
                    progress.add_detected_entity(entity, entity_sample)
            ranked_groups.append((intent_to_outcome_map[intent["name"]], intent["confidence"]))
        DEBUG("\t top random ranking for group '%s'" % (ranked_groups[0][0].name))
        return ranked_groups, progress

    def _report_sampled_entities(self, top_group, progress):
        # collected_entities = self.find_required_present_entities(outcome_groups)
        pass
        # add the entities like they were really detected during the determination
        # for entity in collected_entities:
        #     entity_sample = RandomOutcomeDeterminer._make_entity_sample(entity, progress)
        #     progress.add_detected_entity(entity, entity_sample)
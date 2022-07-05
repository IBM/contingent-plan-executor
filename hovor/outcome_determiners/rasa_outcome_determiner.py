from hovor.outcome_determiners.outcome_determiner_base import OutcomeDeterminerBase
from hovor import DEBUG
import requests
import json
from .random_outcome_determiner import RandomOutcomeDeterminer


class RasaOutcomeDeterminer(OutcomeDeterminerBase):
    """Determiner"""
    def __init__(self, full_outcomes, context_variables, intents):
        self.full_outcomes = {outcome["name"]: outcome for outcome in full_outcomes}
        self.context_variables = context_variables
        self.intents = intents
    
    def rank_groups(self, outcome_groups, progress):

        import spacy
        nlp = spacy.load("en_core_web_md")
        print(nlp.get_pipe("ner").labels)

        payload = {'text': progress.json["action_result"]["fields"]["input"]}
        r = json.loads(requests.post('http://localhost:5005/model/parse', json=payload).text)
        print(json.dumps(r, indent=4))

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
        for extracted in r["entities"]:
            if extracted["entity"] in nlp.get_pipe("ner").labels:
                if extracted["entity"] in spacy_entities:
                    spacy_entities[extracted["entity"]].append(extracted)
                else:
                    spacy_entities[extracted["entity"]] = [extracted]
            else:
                if extracted["entity"] in rasa_entities:
                    rasa_entities[extracted["entity"]].append(extracted)
                else:
                    rasa_entities[extracted["entity"]] = [extracted]       

        entities = {}
        chosen_intent = None
        for intent in r["intent_ranking"]:
            valid = True
            # if this intent expects entities, make sure we extract them
            if len(self.intents[intent["name"]]["variables"]) > 0:
                for entity in self.intents[intent["name"]]["variables"]:
                    # get rid of $
                    entity = entity[1:]
                    entities[entity] = []

                    # start integrating roles/groups here
                    if "roles" in self.context_variables[entity]:
                        roles = [str(r) for r in self.context_variables[entity]["roles"]]
                        roles_so_far = []
                    if "groups" in self.context_variables[entity]:
                        groups = [str(g) for g in self.context_variables[entity]["groups"]]
                        groups_so_far = []

                    # also account for duplicates (for example, extracting 2 locations, neither of which has a distinguishing role/group)
                    for _ in range(self.intents[intent["name"]]["utterances"][0].count(entity)):
                        prev_length = len(entities[entity])
                        got_from_spacy = False
                        # spacy
                        if type(self.context_variables[entity]["config"]) == dict:
                            if self.context_variables[entity]["config"]["extraction"] == "spacy":
                                if self.context_variables[entity]["config"]["method"].upper() in spacy_entities:
                                    if spacy_entities[self.context_variables[entity]["config"]["method"].upper()]:
                                        entities[entity].append(spacy_entities[self.context_variables[entity]["config"]["method"].upper()].pop())
                                        got_from_spacy = True
                        # rasa
                        if not got_from_spacy:   
                            if entity in rasa_entities:
                                if rasa_entities[entity]:
                                    extracted = rasa_entities[entity].pop()
                                    added = False
                                    if roles:
                                        if "role" in extracted:
                                            if extracted["role"] in roles and extracted["role"] not in roles_so_far:
                                                roles_so_far.append(extracted["role"])
                                                entities[entity].append(extracted)
                                                added = True
                                    if not added:
                                        if groups:
                                            if "group" in extracted:
                                                if extracted["group"] in groups and extracted["group"] not in groups_so_far:
                                                    groups_so_far.append(extracted["group"])
                                                    entities[entity].append(extracted)
                                        else:
                                            entities[entity].append(extracted)
                        # break and proceed to the next intent if we weren't able to find the next entity
                        if len(entities[entity]) == prev_length:
                            valid = False
                            break
                    # HAVING PROBLEMS HERE - need to keep track of roles/groups a different way
                    if roles_so_far != roles or groups_so_far != groups:
                        valid = False
                    roles = None
                    groups = None
                    if not valid:
                        break
                if valid:
                    # stop looking for a suitable intent if we found all entities
                    chosen_intent = intent
                break
            else:
                # stop looking or a suitable intent if the intent extracted doesn't require entities
                chosen_intent = intent
                break
        if not chosen_intent:
            print("no suitable intent found.")

        # entities = {}
        # for intent in r["intent_ranking"]:
        #     # if len(r["entities"]) == len(intent_to_outcome_map[intent["name"]].required_present_entities):

        #     # SECOND: map spacy-extracted entities to user-supplied entities when appropriate
        #     # NOTE: based on intents
        #     for spacy_ent in spacy_entities:
        #         entity_name = spacy_ent["entity"]
        #         for ent in intent_to_outcome_map[intent["name"]].required_present_entities:
        #             if "method" in self.context_variables[ent]["config"]:
        #                 if self.context_variables[ent]["config"]["method"].upper() == entity_name:
        #                     entities[ent] = self.context_variables[ent]
        #         else:
        #             if entity_name not in entities:
        #                 entities[ent] = entity_name
        #         # NOTE: this just randomly picks from the list of enums (see the enum option)
        #         # add to the rasa configuration which option is explicitly picked each time.
        #         # entity "keys" are also sometimes wrongly extracted, i.e. "kingston" is parsed as a
        #         # payment_method entity. not sure where exactly this is caused (maybe just need more examples,
        #         # or to attach the appropriate classifiers i.e. spacy, or maybe something else is breaking this?).
        #         # this entity keys bug causes errors when trying to update values.
        #         for entity in entities:
        #             entity_sample = RandomOutcomeDeterminer._make_entity_sample(entity, progress)
        #             progress.add_detected_entity(entity, entity_sample)
        #     ranked_groups.append((intent_to_outcome_map[intent["name"]], intent["confidence"]))

        DEBUG("\t top random ranking for group '%s'" % (ranked_groups[0][0].name))
        return ranked_groups, progress

    def _report_sampled_entities(self, top_group, progress):
        # collected_entities = self.find_required_present_entities(outcome_groups)
        pass
        # add the entities like they were really detected during the determination
        # for entity in collected_entities:
        #     entity_sample = RandomOutcomeDeterminer._make_entity_sample(entity, progress)
        #     progress.add_detected_entity(entity, entity_sample)
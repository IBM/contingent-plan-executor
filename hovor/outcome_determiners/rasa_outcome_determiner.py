from hovor.outcome_determiners.outcome_determiner_base import OutcomeDeterminerBase
from hovor import DEBUG
import requests
import json
from .random_outcome_determiner import RandomOutcomeDeterminer


class RasaOutcomeDeterminer(OutcomeDeterminerBase):
    """Determiner"""
    def __init__(self, full_outcomes):
        self.full_outcomes =  {outcome["name"]: outcome for outcome in full_outcomes}
    
    def rank_groups(self, outcome_groups, progress):
        payload = {'text': progress.json["action_result"]["fields"]["input"]}
        r = json.loads(requests.post('http://localhost:5005/model/parse', json=payload).text)
        ranked_groups = []
        intent_to_outcome_map = {}
        intent_to_outcome_map["null"] = []
        for outcome in outcome_groups:
            if "intent" in self.full_outcomes[outcome.name]:
                intent_to_outcome_map[self.full_outcomes[outcome.name]["intent"]] = outcome
            else:
                intent_to_outcome_map["null"].append((outcome, 0))
        for intent in r["intent_ranking"]:
            if intent["name"] in intent_to_outcome_map:
                if len(r["entities"]) == len(intent_to_outcome_map[intent["name"]].required_present_entities):
                    for entity in r["entities"]:
                        # NOTE: this just randomly picks from the list of enums (see the enum option)
                        # add to the rasa configuration which option is explicitly picked each time.
                        # entity "keys" are also sometimes wrongly extracted, i.e. "kingston" is parsed as a
                        # payment_method entity. not sure where exactly this is caused (maybe just need more examples,
                        # or to attach the appropriate classifiers i.e. spacy, or maybe something else is breaking this?).
                        # this entity keys bug causes errors when trying to update values.
                        entity_sample = RandomOutcomeDeterminer._make_entity_sample(entity["entity"], progress)
                        progress.add_detected_entity(entity["entity"], entity_sample)
                    ranked_groups.append((intent_to_outcome_map[intent["name"]], intent["confidence"]))
        ranked_groups.extend(intent_to_outcome_map["null"])
        DEBUG("\t top random ranking for group '%s'" % (ranked_groups[0][0].name))
        return ranked_groups, progress

    def _report_sampled_entities(self, top_group, progress):
        # collected_entities = self.find_required_present_entities(outcome_groups)
        pass
        # add the entities like they were really detected during the determination
        # for entity in collected_entities:
        #     entity_sample = RandomOutcomeDeterminer._make_entity_sample(entity, progress)
        #     progress.add_detected_entity(entity, entity_sample)
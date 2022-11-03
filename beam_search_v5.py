from cmath import log
from dataclasses import dataclass
from typing import List, Union
from hovor.rollout.rollout_core import Rollout
from hovor.rollout.graph_setup import BeamSearchGraphGenerator
from local_main_rollout import create_rollout

@dataclass
class Action:
    name: str
    probability: float
    beam: int
    score: float

    def __lt__(self, other):
        return self.score > other.score

    def __str__(self):
        return f"action: {self.name}, probability: {self.probability}"

    def __post_init__(self):
        # sort by scores
        self.sort_index = self.score

@dataclass
class Intent:
    name: str
    probability: float
    outcome: str
    beam: int
    score: float

    def __eq__(self, other):
        return self.name == other.name and self.probability == other.probability and self.outcome == other.outcome

    def __lt__(self, other):
        return self.score > other.score

    def __str__(self):
        return f"intent: {self.name}, outcome: {self.outcome}, probability: {self.probability}"
    
    def __post_init__(self):
        # sort by scores
        self.sort_index = self.score

@dataclass
class Beam:
    id: int
    last_action: Union[Action, None]
    last_intent: Union[Intent, None]
    rankings: List[Union[Action, Intent]]
    rollout_cfg: Rollout
    scores: list

    def __str__(self):
        return f"BEAM {self.id}\n" + "\n".join(str(r) for r in self.rankings)

    # alternatively, use functions instead of attributes
    def get_last_action(self):
        pass

    def get_last_intent(self):
        pass

# action = Action("get_order", 1.0)
# intent = Intent("share_order", "valid", 0.5)
# beam = Beam(0, action, intent, [action, intent])
# print(beam, "\n")

# next_action = Action("get_side", 0.7)
# beam.rankings.append(next_action)
# beam.last_action = next_action

# next_intent = Intent("share_side", "valid", 0.6)
# beam.rankings.append(next_intent)
# beam.last_intent = next_intent

# print(beam)
# print(beam.last_action.name)

# beams = []
# for i in range(3):
#     beams.append(Beam(i, None, None, []))
# print(beams)

def create_rollout_from_old(rollout_cfg, output_files_path):
    new_rollout = create_rollout(output_files_path)
    new_rollout.current_state = {f for f in rollout_cfg.current_state}
    new_rollout.applicable_actions = {a for a in rollout_cfg.applicable_actions}
    return new_rollout


def beam_search(k, max_fallbacks, conversation, output_files_path):
    beams = []
    graph_gen = BeamSearchGraphGenerator(k)
    for i in range(len(conversation)): 
        print(conversation[i])
        if i == 0: 
            start_rollout = create_rollout(output_files_path)
            starting_values = start_rollout.update_action_get_confidences(conversation[i])
            outputs = []
            for index, (key, val) in enumerate(starting_values.items()):
                action = Action(key, val, index, log(val))
                outputs.append(action)         
            print("OUTPUTS", outputs)

            action_names = [action.name for action in outputs]
            start = "START"
            for beam in range(k):
                first_score = [log(outputs[beam].probability)]
                beams.append(Beam(beam, outputs[beam], None, [outputs[beam]], create_rollout(output_files_path), first_score))
                # assign each chosen value to a distinct beam
                graph_gen.create_nodes_highlight_k([outputs[beam].name], "skyblue", start, beam, [outputs[beam].name])

            # generate nodes that won't be picked
            graph_gen.create_from_parent(action_names[k:], "skyblue")
            
        else: 
            outputs = []
            given_conv = [[] for _  in range(k)]
            for beam in range(k):
                #call hovor to predict next for now using dummy function
                if "USER" in  conversation[i].keys():
                    given_conv[beam]= beams[beam].rollout_cfg.get_highest_intents(beams[beam].last_action.name, conversation[i])
                    for val in range(len(given_conv[beam])):
                        intent = given_conv[beam][val]["intent"]
                        probs= given_conv[beam][val]["confidence"]
                        outcome = given_conv[beam][val]["outcome"]
                        #find the score by taking the sum of the current beam thread which should be a list of log(prob)
                        score = sum(beams[beam].scores) + log(probs)
                        outputs.append(Intent(intent, probs, outcome, beam, score.real))
                        
                        
                elif "HOVOR" in conversation[i].keys():
                    given_conv[beam] = beams[beam].rollout_cfg.update_action_get_confidences(conversation[i], beams[beam].last_action.name, beams[beam].last_intent.name, beams[beam].last_intent.outcome)
                    for index, (key, val) in enumerate(given_conv[beam].items()):
                        score = sum(beams[beam].scores) + log(val)
                        outputs.append(Action(key, val, beam, score.real))
                        print(outputs)
            #sort the new lsit keeping track of each thread instead of the outputs
            print("OUTPUTS", outputs)
            outputs.sort()
            outputs = outputs[0:k]
            # sorted_out = sorted(outputs)
            # outputs = sorted_out[0:k]
            print("SRT OUTPUTS", outputs)

            
            if "USER" in conversation[i].keys():
                beam_holders = [[] for _  in range(k)]
                list_intents = []
                list_actions = []
                list_rollout = []
                list_scores = [[] for _  in range(k)]
                graph_beam_chosen_map = {idx: [] for idx in range(k)}
                for seq in range(k):
                    at_beam = outputs[seq].beam

                    #setting up the next intents to add to the beam
                    next_intent = outputs[seq]
                    list_intents.append(next_intent)

                    #carrying thrugh the proper last actions from previous beams
                    last_action = beams[at_beam].last_action
                    list_actions.append(last_action)
                    last_rollout = beams[at_beam].rollout_cfg
                    list_rollout.append(last_rollout)

                    #keeping track of the old beam scores all unadded
                    list_scores[seq].extend(beams[at_beam].scores)
                    list_scores[seq].append(log(next_intent.probability))

                    #setting the root of the current beam that will get additions
                    current_beam = beams[at_beam].rankings
                    beam_holders[seq].extend(current_beam)
                    beam_holders[seq].append(next_intent)

                    graph_beam_chosen_map[at_beam].append(next_intent.name)

                for beam, chosen_intents in graph_beam_chosen_map.items():
                    graph_gen.create_nodes_highlight_k(list(beams[beam].rollout_cfg.configuration_provider._configuration_data["actions"][beams[beam].last_action.name]["intents"].keys()), "lightgoldenrod1", beams[beam].last_action.name, beam, chosen_intents)


                # print("Holders", beam_holders)
                # print("Intents", list_intents)

                beams = []
                graph_beams_copy = graph_gen.beams
                graph_gen.beams = []
                # print("Final beams", beams)
                for new_beam in range(k):
                    beams.append(Beam(new_beam, list_actions[new_beam], list_intents[new_beam], beam_holders[new_beam], create_rollout_from_old(list_rollout[new_beam], output_files_path), list_scores[new_beam]))
                    beams[new_beam].rollout_cfg.update_state_applicable_actions(beams[new_beam].last_action.name, beams[new_beam].last_intent.outcome)
                    # also update the graph so they point to the right beams
                    # grab the old beam placement
                    old_beam_placement = list_intents[new_beam].beam
                    graph_gen.beams.append(BeamSearchGraphGenerator.Beam({k: v for k, v in graph_beams_copy[old_beam_placement].parent_nodes_id_map.items()}))
                    print()
                #print("New Beams Intents", beams)
            else:
                beam_holders = [[] for _  in range(k)]
                list_intents = []
                list_actions = []
                list_rollout = []
                list_scores = [[] for _  in range(k)]
                graph_beam_chosen_map = {idx: [] for idx in range(k)}
                for seq in range(k):
                    at_beam = outputs[seq].beam
                    #setting up the next actions to add to the beam
                    next_action = outputs[seq]
                    list_actions.append(next_action)
                    #carry through the last intents from the previous beams
                    last_intent = beams[at_beam].last_intent
                    list_intents.append(last_intent)

                    last_rollout = beams[at_beam].rollout_cfg
                    list_rollout.append(last_rollout)

                    list_scores[seq].extend(beams[at_beam].scores)
                    list_scores[seq].append(log(next_action.probability))

                    current_beam = beams[at_beam].rankings
                    beam_holders[seq].extend(current_beam)
                    beam_holders[seq].append(next_action)


                    graph_beam_chosen_map[at_beam].append(next_action.name)

                for beam, chosen_acts in graph_beam_chosen_map.items():
                    graph_gen.create_nodes_highlight_k(beams[beam].rollout_cfg.applicable_actions, "skyblue", beams[beam].last_intent.name, beam, chosen_acts)



                # print("Holders", beam_holders)
                # print("Intents", list_intents)
                print("Last Rollout", list_rollout)

                beams = []
                #print("Final beams", beams)
                graph_beams_copy = graph_gen.beams
                graph_gen.beams = []
                for new_beam in range(k):
                    beams.append(Beam(new_beam, list_actions[new_beam], list_intents[new_beam], beam_holders[new_beam], create_rollout_from_old(list_rollout[new_beam], output_files_path), list_scores[new_beam]))
                    
                    # also update the graph so they point to the right beams
                    # grab the old beam placement
                    old_beam_placement = list_actions[new_beam].beam
                    graph_gen.beams.append(BeamSearchGraphGenerator.Beam({k: v for k, v in graph_beams_copy[old_beam_placement].parent_nodes_id_map.items()}))


                    result = beams[new_beam].rollout_cfg.update_if_message_action(beams[new_beam].last_action.name, {"intent": beams[new_beam].last_intent.name, "outcome": beams[new_beam].last_intent.outcome, "confidence": beams[new_beam].last_intent.probability, "score": list_scores[new_beam]})
                    intent = Intent(name=result["intent"], probability=result["confidence"], outcome=result["outcome"], beam=new_beam, score = log(result["confidence"])+beams[new_beam].last_action.score)
                    if intent != beams[new_beam].last_intent:
                        beams[new_beam].last_intent = intent
                        beams[new_beam].rankings.append(intent)
                        graph_gen.create_nodes_highlight_k([intent.name], "lightgoldenrod1", beams[new_beam].last_action.name, new_beam, [intent.name])

            for beam in range(k):
                fallbacks = 0
                for ranking in beams[beam].rankings:
                    if type(ranking) == Intent and ranking.name == "fallback":
                        fallbacks += 1
                if fallbacks >= max_fallbacks:
                    # prune the beam ??
                    beams[beam].scores = [log(0.00000001)]

                #print("New Beam Actions", beams)

    #print("Final beams", beams)

    for final in range(len(beams)): 
        final_path=[]
        final_probs = []
        print("Final Scores", beams[final].scores)
        #print("Beam @ ", final , beams[final].rankings)
        for names in range(len(beams[final].rankings)):
            final_path.append(beams[final].rankings[names].name)
            #final_probs.append(log(beams[final].rankings[names].probability))
        #beams[final].score
        # print(beams[final].rollout_cfg.get_reached_goal())
        print(final_path)
        if beams[final].rollout_cfg.get_reached_goal():
            graph_gen.set_last_chosen(beams[final].rankings[-1].name, final)
            graph_gen.complete_conversation()
        # print(final_probs)
        # print(sum(final_probs))
    graph_gen.graph.render(f"beam_search.gv", view=True)


conversation = [{"HOVOR": "Hello I am a Pizza bot what toppings do you want?"}, 
                {"USER": "I want it to have pepperoni"}, 
                {'HOVOR':"Ok what size do you want?"},
                {"USER": "I want a large pizza."}, 
                {'HOVOR': "What side do you want with your order?"},
                {"USER": "I want to have fries on the side."}, 
                {'HOVOR':"What drink do you want with your order?"},
                {"USER": "I want to drink coke."}, 
                {'HOVOR':"What base do you want for your pizza?"},
                {"USER": "I want a pizza with a ranch base"}, 
                {"HOVOR":"Ordering a pizza of size large with ranch as a base and pepperoni as toppings, as well as a coke and fries."},
             
]

test2 =[{"HOVOR": "Hello I am a Pizza bot what toppings do you want?"}, 
                 {"USER": "I want it to have pepperoni"}, 
                {'HOVOR':"Ok what size do you want?"},
                {"USER": "I want a large pizza."}, 
                {'HOVOR': "What side do you want with your order?"},
                {"USER": "I want to have fries on the side."}, 
                {'HOVOR':"What drink do you want with your order?"},
                {"USER": "I want to drink coke."}, 
                {'HOVOR':"What base do you want for your pizza?"},
                {"USER": "I want a pizza with a ranch base"}, 
                {"HOVOR":"Ordering a pizza of size large with ranch as a base and pepperoni as toppings, as well as a coke and fries."},
                {"USER": "Thanks!"}, 

]

test1= [{"HOVOR": "Hello I am a Pizza bot how are you!"}, 
                {"USER": "I want it to have pepperoni and cheese?"}, 
                {'HOVOR':"Sorry I did not get that"},
                {'HOVOR':"Ok what size do you want?"},
                {"USER": "I want a large pizza."}, 
                {'HOVOR': "What side do you want with your order?"},
                {"USER": "I want to have fries on the side."}, 
                {'HOVOR':"What drink do you want with your order?"},
                {"USER": "I want to drink coke."}, 
                {'HOVOR':"What base do you want for your pizza?"},
                {"USER": "I want a pizza with a ranch base"}, 
                {"HOVOR": "What toppings do you want for your pizza?"},
                {"USER": "Can I get a pizza with pepperoni"},
                {"HOVOR":"Ordering a pizza of size large with ranch as a base and pepperoni as toppings, as well as a coke and fries."},
                {"USER": "Thanks!"}, 

]

if __name__ == "__main__":
    beam_search(
        4,
        1,
        conversation,
        "C:\\Users\\Rebecca\\Desktop\\plan4dial\\plan4dial\\local_data\\rollout_no_system_gold_standard_bot\\output_files"
    )

from collections import OrderedDict

psgraph = {
    "init": 31,
    "goal": 0,
    "nodes": {
        0: {
            "expected_successor": False,
            "action": "---",
            "state": "0x97918d0",
            "distance": 0,
            "is_relevant": 1,
            "is_goal": 1,
            "is_sc": 1,
            "successors": [
            ],
        },
        1: {
            "expected_successor": "0",
            "action": "system-book_trip ",
            "state": "0x97b3c58",
            "distance": 1,
            "is_relevant": 0,
            "is_goal": 0,
            "is_sc": 1,
            "successors": [
                0,
            ],
        },
        5: {
            "expected_successor": "1",
            "action": "dialogue-followup warn-no_weather",
            "state": "0x97bbe18",
            "distance": 2,
            "is_relevant": 0,
            "is_goal": 0,
            "is_sc": 1,
            "successors": [
                1,
            ],
        },
        9: {
            "expected_successor": "16",
            "action": "dialogue-ask_location src",
            "state": "0x97ec978",
            "distance": 5,
            "is_relevant": 0,
            "is_goal": 0,
            "is_sc": 1,
            "successors": [
                16,
                18,
            ],
        },
        10: {
            "expected_successor": "9",
            "action": "dialogue-ask_location dst",
            "state": "0x97eca48",
            "distance": 6,
            "is_relevant": 0,
            "is_goal": 0,
            "is_sc": 1,
            "successors": [
                9,
                19,
            ],
        },
        11: {
            "expected_successor": "13",
            "action": "dialogue-ask-to-change err-bad_weather",
            "state": "0x97ed2d0",
            "distance": 4,
            "is_relevant": 0,
            "is_goal": 0,
            "is_sc": 1,
            "successors": [
                13,
                16,
                20,
                9,
                26,
                24,
                21,
                10,
            ],
        },
        12: {
            "expected_successor": "1",
            "action": "web-lookup_weather dst",
            "state": "0x97ed4f0",
            "distance": 2,
            "is_relevant": 0,
            "is_goal": 0,
            "is_sc": 1,
            "successors": [
                1,
                11,
                5,
            ],
        },
        13: {
            "expected_successor": "12",
            "action": "web-lookup_travel ",
            "state": "0x97ed5f0",
            "distance": 3,
            "is_relevant": 0,
            "is_goal": 0,
            "is_sc": 1,
            "successors": [
                12,
                28,
            ],
        },
        17: {
            "expected_successor": "16",
            "action": "dialogue-followup err-bad_dates",
            "state": "0x9815848",
            "distance": 5,
            "is_relevant": 0,
            "is_goal": 0,
            "is_sc": 1,
            "successors": [
                16,
            ],
        },
        18: {
            "expected_successor": "9",
            "action": "dialogue-followup err-bad_location",
            "state": "0x9849508",
            "distance": 6,
            "is_relevant": 0,
            "is_goal": 0,
            "is_sc": 1,
            "successors": [
                9,
            ],
        },
        16: {
            "expected_successor": "13",
            "action": "dialogue-ask_dates dates",
            "state": "0x97ba6c0",
            "distance": 4,
            "is_relevant": 0,
            "is_goal": 0,
            "is_sc": 1,
            "successors": [
                13,
                17,
            ],
        },
        19: {
            "expected_successor": "10",
            "action": "dialogue-followup err-bad_location",
            "state": "0x98331e8",
            "distance": 7,
            "is_relevant": 0,
            "is_goal": 0,
            "is_sc": 1,
            "successors": [
                10,
            ],
        },
        21: {
            "expected_successor": "20",
            "action": "dialogue-ask_location dst",
            "state": "0x986de20",
            "distance": 5,
            "is_relevant": 0,
            "is_goal": 0,
            "is_sc": 1,
            "successors": [
                20,
                23,
            ],
        },
        20: {
            "expected_successor": "13",
            "action": "dialogue-ask_location src",
            "state": "0x985f840",
            "distance": 4,
            "is_relevant": 0,
            "is_goal": 0,
            "is_sc": 1,
            "successors": [
                13,
                22,
            ],
        },
        22: {
            "expected_successor": "20",
            "action": "dialogue-followup err-bad_location",
            "state": "0x9875418",
            "distance": 5,
            "is_relevant": 0,
            "is_goal": 0,
            "is_sc": 1,
            "successors": [
                20,
            ],
        },
        23: {
            "expected_successor": "21",
            "action": "dialogue-followup err-bad_location",
            "state": "0x9875518",
            "distance": 6,
            "is_relevant": 0,
            "is_goal": 0,
            "is_sc": 1,
            "successors": [
                21,
            ],
        },
        24: {
            "expected_successor": "16",
            "action": "dialogue-ask_location dst",
            "state": "0x98aaa30",
            "distance": 5,
            "is_relevant": 0,
            "is_goal": 0,
            "is_sc": 1,
            "successors": [
                16,
                25,
            ],
        },
        25: {
            "expected_successor": "24",
            "action": "dialogue-followup err-bad_location",
            "state": "0x989e8a0",
            "distance": 6,
            "is_relevant": 0,
            "is_goal": 0,
            "is_sc": 1,
            "successors": [
                24,
            ],
        },
        26: {
            "expected_successor": "13",
            "action": "dialogue-ask_location dst",
            "state": "0x98c5ef0",
            "distance": 4,
            "is_relevant": 0,
            "is_goal": 0,
            "is_sc": 1,
            "successors": [
                13,
                27,
            ],
        },
        27: {
            "expected_successor": "26",
            "action": "dialogue-followup err-bad_location",
            "state": "0x98d8508",
            "distance": 5,
            "is_relevant": 0,
            "is_goal": 0,
            "is_sc": 1,
            "successors": [
                26,
            ],
        },
        28: {
            "expected_successor": "13",
            "action": "dialogue-ask-to-change err-bad_dates_for_travel",
            "state": "0x98ea6c0",
            "distance": 4,
            "is_relevant": 0,
            "is_goal": 0,
            "is_sc": 1,
            "successors": [
                13,
                16,
                20,
                9,
                26,
                24,
                21,
                10,
            ],
        },
        29: {
            "expected_successor": "16",
            "action": "dialogue-confirm_location src",
            "state": "0x98fc758",
            "distance": 5,
            "is_relevant": 0,
            "is_goal": 0,
            "is_sc": 1,
            "successors": [
                16,
                9,
                32,
                18,
            ],
        },
        30: {
            "expected_successor": "29",
            "action": "dialogue-ask_location dst",
            "state": "0x98fc678",
            "distance": 6,
            "is_relevant": 0,
            "is_goal": 0,
            "is_sc": 1,
            "successors": [
                29,
                33,
            ],
        },
        31: {
            "expected_successor": "13",
            "action": "system-assess_initial_data ",
            "state": "0x98fd160",
            "distance": 4,
            "is_relevant": 0,
            "is_goal": 0,
            "is_sc": 1,
            "successors": [
                13,
                16,
                21,
                10,
                26,
                24,
                34,
                29,
                35,
                30,
                20,
                9,
            ],
        },
        32: {
            "expected_successor": "16",
            "action": "dialogue-followup msg-affirm",
            "state": "0x990b128",
            "distance": 5,
            "is_relevant": 0,
            "is_goal": 0,
            "is_sc": 1,
            "successors": [
                16,
            ],
        },
        33: {
            "expected_successor": "30",
            "action": "dialogue-followup err-bad_location",
            "state": "0x9904f70",
            "distance": 7,
            "is_relevant": 0,
            "is_goal": 0,
            "is_sc": 1,
            "successors": [
                30,
            ],
        },
        34: {
            "expected_successor": "13",
            "action": "dialogue-confirm_location src",
            "state": "0x99117d0",
            "distance": 4,
            "is_relevant": 0,
            "is_goal": 0,
            "is_sc": 1,
            "successors": [
                13,
                20,
                36,
                22,
            ],
        },
        35: {
            "expected_successor": "34",
            "action": "dialogue-ask_location dst",
            "state": "0x9905388",
            "distance": 5,
            "is_relevant": 0,
            "is_goal": 0,
            "is_sc": 1,
            "successors": [
                34,
                37,
            ],
        },
        36: {
            "expected_successor": "13",
            "action": "dialogue-followup msg-affirm",
            "state": "0x9911db0",
            "distance": 4,
            "is_relevant": 0,
            "is_goal": 0,
            "is_sc": 1,
            "successors": [
                13,
            ],
        },
        37: {
            "expected_successor": "35",
            "action": "dialogue-followup err-bad_location",
            "state": "0x99168c0",
            "distance": 6,
            "is_relevant": 0,
            "is_goal": 0,
            "is_sc": 1,
            "successors": [
                35,
            ],
        },
    },
    "edges": [
        [1, ">", 0],
        [5, ">", 1],
        [9, ">", 16],
        [9, ">", 18],
        [10, ">", 9],
        [10, ">", 19],
        [11, ">", 13],
        [11, ">", 16],
        [11, ">", 20],
        [11, ">", 9],
        [11, ">", 26],
        [11, ">", 24],
        [11, ">", 21],
        [11, ">", 10],
        [12, ">", 1],
        [12, ">", 11],
        [12, ">", 5],
        [13, ">", 12],
        [13, ">", 28],
        [17, ">", 16],
        [18, ">", 9],
        [16, ">", 13],
        [16, ">", 17],
        [19, ">", 10],
        [21, ">", 20],
        [21, ">", 23],
        [20, ">", 13],
        [20, ">", 22],
        [22, ">", 20],
        [23, ">", 21],
        [24, ">", 16],
        [24, ">", 25],
        [25, ">", 24],
        [26, ">", 13],
        [26, ">", 27],
        [27, ">", 26],
        [28, ">", 13],
        [28, ">", 16],
        [28, ">", 20],
        [28, ">", 9],
        [28, ">", 26],
        [28, ">", 24],
        [28, ">", 21],
        [28, ">", 10],
        [29, ">", 16],
        [29, ">", 9],
        [29, ">", 32],
        [29, ">", 18],
        [30, ">", 29],
        [30, ">", 33],
        [31, ">", 13],
        [31, ">", 16],
        [31, ">", 21],
        [31, ">", 10],
        [31, ">", 26],
        [31, ">", 24],
        [31, ">", 34],
        [31, ">", 29],
        [31, ">", 35],
        [31, ">", 30],
        [31, ">", 20],
        [31, ">", 9],
        [32, ">", 16],
        [33, ">", 30],
        [34, ">", 13],
        [34, ">", 20],
        [34, ">", 36],
        [34, ">", 22],
        [35, ">", 34],
        [35, ">", 37],
        [36, ">", 13],
        [37, ">", 35],
    ],
    "states": {
        "0x97918d0": [
            "Atom intent-handled-book_ski_trip()",
        ],
        "0x97b3c58": [
            "NegatedAtom forced-followup(system)",
            "NegatedAtom forced-followup(dialogue)",
            "NegatedAtom forced-followup(dialogue-change_option)",
            "Atom ok-travel()",
            "Atom ok-weather(dst)",
        ],
        "0x97bbe18": [
            "NegatedAtom forced-followup(system)",
            "Atom followup-reason(warn-no_weather)",
            "Atom forced-followup(dialogue)",
            "NegatedAtom forced-followup(dialogue-change_option)",
            "Atom ok-travel()",
            "Atom ok-weather(dst)",
        ],
        "0x97ec978": [
            "NegatedAtom forced-followup(system)",
            "NegatedAtom maybe-have-location(src)",
            "NegatedAtom forced-followup(dialogue)",
            "NegatedAtom forced-followup(dialogue-change_option)",
            "Atom have-location(dst)",
            "NegatedAtom have-location(src)",
            "NegatedAtom have-travel_dates(dates)",
            "NegatedAtom ok-travel()",
        ],
        "0x97eca48": [
            "NegatedAtom forced-followup(system)",
            "NegatedAtom maybe-have-location(src)",
            "NegatedAtom forced-followup(dialogue)",
            "NegatedAtom forced-followup(dialogue-change_option)",
            "NegatedAtom have-location(dst)",
            "NegatedAtom have-location(src)",
            "NegatedAtom have-travel_dates(dates)",
            "NegatedAtom ok-travel()",
        ],
        "0x97ed2d0": [
            "NegatedAtom forced-followup(system)",
            "NegatedAtom maybe-have-location(src)",
            "Atom followup-reason(err-bad_weather)",
            "NegatedAtom forced-followup(dialogue)",
            "Atom forced-followup(dialogue-change_option)",
            "Atom have-location(dst)",
            "Atom have-location(src)",
            "Atom have-travel_dates(dates)",
        ],
        "0x97ed4f0": [
            "NegatedAtom forced-followup(system)",
            "NegatedAtom maybe-have-location(src)",
            "NegatedAtom forced-followup(dialogue)",
            "NegatedAtom forced-followup(dialogue-change_option)",
            "Atom have-location(dst)",
            "Atom have-location(src)",
            "Atom have-travel_dates(dates)",
            "Atom ok-travel()",
        ],
        "0x97ed5f0": [
            "NegatedAtom forced-followup(system)",
            "NegatedAtom maybe-have-location(src)",
            "NegatedAtom forced-followup(dialogue)",
            "NegatedAtom forced-followup(dialogue-change_option)",
            "Atom have-location(dst)",
            "Atom have-location(src)",
            "Atom have-travel_dates(dates)",
            "NegatedAtom ok-travel()",
        ],
        "0x9815848": [
            "NegatedAtom forced-followup(system)",
            "Atom followup-reason(err-bad_dates)",
            "NegatedAtom maybe-have-location(src)",
            "Atom forced-followup(dialogue)",
            "NegatedAtom forced-followup(dialogue-change_option)",
            "Atom have-location(dst)",
            "Atom have-location(src)",
            "NegatedAtom have-travel_dates(dates)",
            "NegatedAtom ok-travel()",
        ],
        "0x9849508": [
            "NegatedAtom forced-followup(system)",
            "NegatedAtom maybe-have-location(src)",
            "Atom forced-followup(dialogue)",
            "Atom followup-reason(err-bad_location)",
            "NegatedAtom forced-followup(dialogue-change_option)",
            "Atom have-location(dst)",
            "NegatedAtom have-location(src)",
            "NegatedAtom have-travel_dates(dates)",
            "NegatedAtom ok-travel()",
        ],
        "0x97ba6c0": [
            "NegatedAtom forced-followup(system)",
            "NegatedAtom maybe-have-location(src)",
            "NegatedAtom forced-followup(dialogue)",
            "NegatedAtom forced-followup(dialogue-change_option)",
            "Atom have-location(dst)",
            "Atom have-location(src)",
            "NegatedAtom have-travel_dates(dates)",
            "NegatedAtom ok-travel()",
        ],
        "0x98331e8": [
            "NegatedAtom forced-followup(system)",
            "NegatedAtom maybe-have-location(src)",
            "Atom forced-followup(dialogue)",
            "Atom followup-reason(err-bad_location)",
            "NegatedAtom forced-followup(dialogue-change_option)",
            "NegatedAtom have-location(dst)",
            "NegatedAtom have-location(src)",
            "NegatedAtom have-travel_dates(dates)",
            "NegatedAtom ok-travel()",
        ],
        "0x986de20": [
            "NegatedAtom forced-followup(system)",
            "NegatedAtom maybe-have-location(src)",
            "NegatedAtom forced-followup(dialogue)",
            "NegatedAtom forced-followup(dialogue-change_option)",
            "NegatedAtom have-location(dst)",
            "NegatedAtom have-location(src)",
            "Atom have-travel_dates(dates)",
            "NegatedAtom ok-travel()",
        ],
        "0x985f840": [
            "NegatedAtom forced-followup(system)",
            "NegatedAtom maybe-have-location(src)",
            "NegatedAtom forced-followup(dialogue)",
            "NegatedAtom forced-followup(dialogue-change_option)",
            "Atom have-location(dst)",
            "NegatedAtom have-location(src)",
            "Atom have-travel_dates(dates)",
            "NegatedAtom ok-travel()",
        ],
        "0x9875418": [
            "NegatedAtom forced-followup(system)",
            "NegatedAtom maybe-have-location(src)",
            "Atom forced-followup(dialogue)",
            "Atom followup-reason(err-bad_location)",
            "NegatedAtom forced-followup(dialogue-change_option)",
            "Atom have-location(dst)",
            "NegatedAtom have-location(src)",
            "Atom have-travel_dates(dates)",
            "NegatedAtom ok-travel()",
        ],
        "0x9875518": [
            "NegatedAtom forced-followup(system)",
            "NegatedAtom maybe-have-location(src)",
            "Atom forced-followup(dialogue)",
            "Atom followup-reason(err-bad_location)",
            "NegatedAtom forced-followup(dialogue-change_option)",
            "NegatedAtom have-location(dst)",
            "NegatedAtom have-location(src)",
            "Atom have-travel_dates(dates)",
            "NegatedAtom ok-travel()",
        ],
        "0x98aaa30": [
            "NegatedAtom forced-followup(system)",
            "NegatedAtom maybe-have-location(src)",
            "NegatedAtom forced-followup(dialogue)",
            "NegatedAtom forced-followup(dialogue-change_option)",
            "NegatedAtom have-location(dst)",
            "Atom have-location(src)",
            "NegatedAtom have-travel_dates(dates)",
            "NegatedAtom ok-travel()",
        ],
        "0x989e8a0": [
            "NegatedAtom forced-followup(system)",
            "NegatedAtom maybe-have-location(src)",
            "Atom forced-followup(dialogue)",
            "Atom followup-reason(err-bad_location)",
            "NegatedAtom forced-followup(dialogue-change_option)",
            "NegatedAtom have-location(dst)",
            "Atom have-location(src)",
            "NegatedAtom have-travel_dates(dates)",
            "NegatedAtom ok-travel()",
        ],
        "0x98c5ef0": [
            "NegatedAtom forced-followup(system)",
            "NegatedAtom maybe-have-location(src)",
            "NegatedAtom forced-followup(dialogue)",
            "NegatedAtom forced-followup(dialogue-change_option)",
            "NegatedAtom have-location(dst)",
            "Atom have-location(src)",
            "Atom have-travel_dates(dates)",
            "NegatedAtom ok-travel()",
        ],
        "0x98d8508": [
            "NegatedAtom forced-followup(system)",
            "NegatedAtom maybe-have-location(src)",
            "Atom forced-followup(dialogue)",
            "Atom followup-reason(err-bad_location)",
            "NegatedAtom forced-followup(dialogue-change_option)",
            "NegatedAtom have-location(dst)",
            "Atom have-location(src)",
            "Atom have-travel_dates(dates)",
            "NegatedAtom ok-travel()",
        ],
        "0x98ea6c0": [
            "NegatedAtom forced-followup(system)",
            "NegatedAtom maybe-have-location(src)",
            "Atom followup-reason(err-bad_dates_for_travel)",
            "NegatedAtom forced-followup(dialogue)",
            "Atom forced-followup(dialogue-change_option)",
            "Atom have-location(dst)",
            "Atom have-location(src)",
            "Atom have-travel_dates(dates)",
        ],
        "0x98fc758": [
            "NegatedAtom forced-followup(system)",
            "Atom maybe-have-location(src)",
            "NegatedAtom forced-followup(dialogue)",
            "NegatedAtom forced-followup(dialogue-change_option)",
            "Atom have-location(dst)",
            "NegatedAtom have-location(src)",
            "NegatedAtom have-travel_dates(dates)",
            "NegatedAtom ok-travel()",
        ],
        "0x98fc678": [
            "NegatedAtom forced-followup(system)",
            "Atom maybe-have-location(src)",
            "NegatedAtom forced-followup(dialogue)",
            "NegatedAtom forced-followup(dialogue-change_option)",
            "NegatedAtom have-location(dst)",
            "NegatedAtom have-location(src)",
            "NegatedAtom have-travel_dates(dates)",
            "NegatedAtom ok-travel()",
        ],
        "0x98fd160": [
            "Atom forced-followup(system)",
            "Atom followup-reason(need-assess_initial_data)",
            "NegatedAtom maybe-have-location(src)",
            "NegatedAtom forced-followup(dialogue)",
            "NegatedAtom forced-followup(dialogue-change_option)",
            "NegatedAtom have-location(src)",
            "NegatedAtom ok-travel()",
        ],
        "0x990b128": [
            "NegatedAtom forced-followup(system)",
            "NegatedAtom maybe-have-location(src)",
            "Atom followup-reason(msg-affirm)",
            "Atom forced-followup(dialogue)",
            "NegatedAtom forced-followup(dialogue-change_option)",
            "Atom have-location(dst)",
            "Atom have-location(src)",
            "NegatedAtom have-travel_dates(dates)",
            "NegatedAtom ok-travel()",
        ],
        "0x9904f70": [
            "NegatedAtom forced-followup(system)",
            "Atom maybe-have-location(src)",
            "Atom forced-followup(dialogue)",
            "Atom followup-reason(err-bad_location)",
            "NegatedAtom forced-followup(dialogue-change_option)",
            "NegatedAtom have-location(dst)",
            "NegatedAtom have-location(src)",
            "NegatedAtom have-travel_dates(dates)",
            "NegatedAtom ok-travel()",
        ],
        "0x99117d0": [
            "NegatedAtom forced-followup(system)",
            "Atom maybe-have-location(src)",
            "NegatedAtom forced-followup(dialogue)",
            "NegatedAtom forced-followup(dialogue-change_option)",
            "Atom have-location(dst)",
            "NegatedAtom have-location(src)",
            "Atom have-travel_dates(dates)",
            "NegatedAtom ok-travel()",
        ],
        "0x9905388": [
            "NegatedAtom forced-followup(system)",
            "Atom maybe-have-location(src)",
            "NegatedAtom forced-followup(dialogue)",
            "NegatedAtom forced-followup(dialogue-change_option)",
            "NegatedAtom have-location(dst)",
            "NegatedAtom have-location(src)",
            "Atom have-travel_dates(dates)",
            "NegatedAtom ok-travel()",
        ],
        "0x9911db0": [
            "NegatedAtom forced-followup(system)",
            "NegatedAtom maybe-have-location(src)",
            "Atom followup-reason(msg-affirm)",
            "Atom forced-followup(dialogue)",
            "NegatedAtom forced-followup(dialogue-change_option)",
            "Atom have-location(dst)",
            "Atom have-location(src)",
            "Atom have-travel_dates(dates)",
            "NegatedAtom ok-travel()",
        ],
        "0x99168c0": [
            "NegatedAtom forced-followup(system)",
            "Atom maybe-have-location(src)",
            "Atom forced-followup(dialogue)",
            "Atom followup-reason(err-bad_location)",
            "NegatedAtom forced-followup(dialogue-change_option)",
            "NegatedAtom have-location(dst)",
            "NegatedAtom have-location(src)",
            "Atom have-travel_dates(dates)",
            "NegatedAtom ok-travel()",
        ],
    },
}

action_mapping = {
    "---": "GOAL ACHIEVED",
    "system-book_trip ": "(system) <book-trip>",
    "dialogue-followup warn-no_weather": "(dial) Hovor: It looks like the weather can't be found at the moment. Proceeding anyways.",
    "dialogue-ask_location src": "(dial) Hovor: Where will you be traveling from?",
    "dialogue-ask_location dst": "(dial) Hovor: Where do you want to go to?",
    "dialogue-ask-to-change err-bad_weather": "(dial) Hovor: The weather will be bad. Is there any part of the trip you'd like to change?",
    "web-lookup_weather dst": "(web) <lookup-weather for dst>",
    "web-lookup_travel ": "(web) <lookup-travel-dates>",
    "dialogue-ask_dates dates": "(dial) Hovor: What dates would you like to travel?",
    "dialogue-followup err-bad_dates": "(dial) Hovor: Sorry, but I can't recognize what those dates are.",
    "dialogue-followup err-bad_location": "(dial) Hovor: That doesn't seem to be a valid location.",
    "dialogue-ask-to-change err-bad_dates_for_travel": "(dial) Hovor: Sorry, but those dates aren't good for the travel you're hoping for. Is there any part of the trip you'd like to change?",
    "dialogue-confirm_location src": "(dial) Hovor: Is it <src> that you will be traveling from?",
    "system-assess_initial_data ": "(dial) Hovor: Hello, what ski trip would you like?",
    "dialogue-followup msg-affirm": "(dial) Hovor: Got it!"
}

intent_info_mapping = {
    "system-assess_initial_data ": OrderedDict([
        ("intent1", "<init-setting-1>"),
        ("intent2", "<init-setting-2>"),
        ("intent3", "<init-setting-3>"),
        ("intent4", "<init-setting-4>"),
        ("intent5", "<init-setting-5>"),
        ("intent6", "<init-setting-6>"),
        ("intent7", "<init-setting-7>"),
        ("intent8", "<init-setting-8>"),
        ("intent9", "<init-setting-9>"),
        ("intent10", "<init-setting-10>"),
        ("intent11", "<init-setting-11>"),
        ("intent12", "<init-setting-12>"),
    ]),
    "dialogue-ask_dates dates": OrderedDict([
        ("intent1", "<good response> Ernesto: From Feb 21 - 27"),
        ("intent2", "<bad response> Ernesto: My spoon is too big!"),
    ]),
    "dialogue-followup err-bad_location": OrderedDict([
        ("intent1", "<single outcome>"),
    ]),
    "dialogue-confirm_location src": OrderedDict([
        ("intent1", "<positive response> Ernesto: Yep!"),
        ("intent2", "<negative response> Ernesto: No way!"),
        ("intent3", "<negative plus info> Ernesto: No, it will be New York."),
        ("intent4", "<bad response> Ernesto: I like butterflies."),
    ]),
    "dialogue-followup warn-no_weather": OrderedDict([
        ("intent1", "<single outcome>"),
    ]),
    "dialogue-followup err-bad_dates": OrderedDict([
        ("intent1", "<single outcome>"),
    ]),
    "dialogue-ask-to-change err-bad_weather": OrderedDict([
        ("intent1", "<change-setting-1> Ernesto: No"),
        ("intent2", "<change-setting-2> Ernesto: Yes"),
        ("intent3", "<change-setting-3>"),
        ("intent4", "<change-setting-4>"),
        ("intent5", "<change-setting-5>"),
        ("intent6", "<change-setting-6>"),
        ("intent7", "<change-setting-7>"),
        ("intent8", "<change-setting-8>"),
    ]),
    "web-lookup_weather dst": OrderedDict([
        ("intent1", "<good weather>"),
        ("intent2", "<bad weather>"),
        ("intent3", "<service down>"),
    ]),
    "dialogue-ask_location src": OrderedDict([
        ("intent1", "<good response> Ernesto: I'll be flying from Boston."),
        ("intent2", "<bad response> Ernesto: Purple is a fun colour."),
    ]),
    "dialogue-ask_location dst": OrderedDict([
        ("intent1", "<good response> Ernesto: I want to go to Whistler."),
        ("intent2", "<bad response> Ernesto: Where is my hat?"),
    ]),
    "dialogue-ask-to-change err-bad_dates_for_travel": OrderedDict([
        ("intent1", "<change-setting-1>"),
        ("intent2", "<change-setting-2> Ernesto: Yes"),
        ("intent3", "<change-setting-3>"),
        ("intent4", "<change-setting-4> Ernesto: No"),
        ("intent5", "<change-setting-5>"),
        ("intent6", "<change-setting-6>"),
        ("intent7", "<change-setting-7>"),
        ("intent8", "<change-setting-8>"),
    ]),
    "web-lookup_travel ": OrderedDict([
        ("intent1", "<good travel>"),
        ("intent2", "<bad dates for travel>"),
    ]),
    "system-book_trip ": OrderedDict([
        ("intent1", "<single outcome>"),
    ]),
    "dialogue-followup msg-affirm": OrderedDict([
        ("intent1", "<single outcome>"),
    ]),
}

context_entity_info_mapping = {
    "system-assess_initial_data ": [
        "I will travel from $src to $dst on $dates",
        "skiing in $dst",
        "skiing at $dst",
        "I want ski from $dates-from to $dates-to"
        "I will travel from $src to $dst.",
        "I will fly from $src.",
        "I will fly to $dst.",
        "I would like to go skiing between $dates",
    ],
}


def get_scope(name):
    if '---' == name:
        return 'system'
    return name.split('-')[0]


def get_domain():
    return {
        "types": {
            "location": "sys-location",
            "travel_dates": "sys-date_range"
        },
        "entities": {
            "dst": "location",
            "src": "location",
            "dates": "travel_dates"
        },
        "entity_configs": {
            "dst":{},
            "src": {},
            "dates": {},
        }
    }

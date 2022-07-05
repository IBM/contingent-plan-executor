from time import sleep
import jsonpickle
from environment import initialize_local_environment
from hovor.configuration.json_configuration_provider import JsonConfigurationProvider
from hovor.core import run_interaction
from setup_hovor_rasa import setup_hovor_rasa
import subprocess
import requests
from requests.exceptions import ConnectionError

import json

import requests

# city="Kingston"
# url = "https://weatherbit-v1-mashape.p.rapidapi.com/forecast/daily"

# querystring = {"city":city, "country": "Canada"}

# headers = {
# 	"X-RapidAPI-Key": "b2c27ee596mshd8717ee1c0eba27p1c6ff4jsn1467f4601dfe",
# 	"X-RapidAPI-Host": "weatherbit-v1-mashape.p.rapidapi.com"
# }

# response = requests.request("GET", url, headers=headers, params=querystring)

# print(response.text)

# url = "https://hotels-com-provider.p.rapidapi.com/v1/hotels/search"

# # querystring = {"checkin_date":"2022-08-26","checkout_date":"2022-09-27","sort_order":"STAR_RATING_HIGHEST_FIRST","destination_id":"549499","adults_number":"1","locale":"en_US","currency":"USD","children_ages":"4,0,15","price_min":"10","star_rating_ids":"3,4,5","accommodation_ids":"20,8,15,5,1","price_max":"500","page_number":"1","theme_ids":"14,27,25","amenity_ids":"527,2063","guest_rating_min":"4"}
# querystring = {"checkin_date":"2022-08-26","checkout_date":"2022-09-27","sort_order":"STAR_RATING_HIGHEST_FIRST","destination_id":"549499","adults_number":"1","locale":"en_US","currency":"USD","children_ages":"4,0,15","price_min":"10","star_rating_ids":"3,4,5","price_max":"500",}

# headers = {
# 	"X-RapidAPI-Key": "b2c27ee596mshd8717ee1c0eba27p1c6ff4jsn1467f4601dfe",
# 	"X-RapidAPI-Host": "hotels-com-provider.p.rapidapi.com"
# }

# response = requests.request("GET", url, headers=headers, params=querystring)

# print(response.text)

initialize_local_environment()

setup_hovor_rasa("pizza", train=False)
subprocess.Popen("./rasa_setup.sh", shell=True)

configuration_provider = JsonConfigurationProvider("./pizza/pizza")

# configuration_provider = JsonConfigurationProvider("./local_data/gold_standard_data/gold")

# test on recoded provider
json = jsonpickle.encode(configuration_provider)
configuration_provider = jsonpickle.decode(json)
configuration_provider.check_all_action_builders()

while True:
    try:
        requests.post('http://localhost:5005/model/parse', json={"text": ""})
    except ConnectionError:
        sleep(0.1)
    else:
        break
run_interaction(configuration_provider)

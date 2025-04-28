import json
import os

from langchain.agents import tool

cur_dir = os.path.dirname(__file__)

file_path = os.path.join(cur_dir, '..', 'data/restaurants.json')


@tool
def get_available_cities():
	"""Use this to get a list of cities for which pizza delivery is available."""
	f = open(file_path)
	data = json.load(f)
	cities: list[str] = []
	for el in data:
		cities.append(el['city'])
	return cities

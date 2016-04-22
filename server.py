"""
# https://github.com/swistakm/python-gmaps

sudo pip install python-gmaps
python server.py

example: 
http://127.0.0.1:5000/?from=%22719%20washington%20ave%20albany%20ca%22&to=%221250%2053rd%20Street,%20Suite%201.%20Emeryville,%20CA%2094608%22
"""
import json
from gmaps import Directions
api = Directions()
from gmaps import Geocoding
geoApi = Geocoding()

def getStepDict(duration, price, start_coord, end_coord, mode):
	myDict = {}
	myDict['duration'] = duration
	myDict['price'] = price
	myDict['mode'] = mode
	start_location = geoApi.reverse(start_coord['lat'], start_coord['lng'])[0]['formatted_address']
	end_location = geoApi.reverse(end_coord['lat'], end_coord['lng'])[0]['formatted_address']
	myDict['start_location'] = start_location
	myDict['end_location'] = end_location
	myDict['start_lat'] = start_coord['lat']
	myDict['start_lng'] = start_coord['lng']
	myDict['end_lat'] = end_coord['lat']
	myDict['end_lng'] = end_coord['lng']
	return myDict

def getUber(start_location, end_location):
	uberDir = api.directions(str(start_location['lat']) + " " + str(start_location['lng']), str(end_location['lat']) + " " + str(end_location['lng']), mode="driving")[0]['legs'][0]
	return uberDir['duration']['value'], uberDir['duration']['value'] * 0.5 / 60 + 3.2

def stepsChoice(step):
	uberDict = None
	if step['travel_mode'] == "WALKING" and step['duration']['value'] >= 600: # this means that we need to uber
		duration, price = getUber(step['start_location'], step['end_location'])
		start_coord = step['start_location']
		end_coord = step['end_location']
		uberDict = getStepDict(duration, price, start_coord, end_coord, "uber")
	mainDictList = None
	if step['travel_mode'] == "TRANSIT":
		mainDictList = getStepDict(step['duration']['value'], 3.2, step['start_location'], step['end_location'], "transit")
	elif step['travel_mode'] == "WALKING":
		mainDictList = getStepDict(step['duration']['value'], 0, step['start_location'], step['end_location'], "walking")
	return mainDictList, uberDict

# return overall duration, $
def routeStats(stepList):
	duration = 0
	cost = 0
	for step in stepList:
		duration += step['duration']
		cost += step['price']
	return duration, cost
	
def travelPlans(steps):
	stepLists = [[]]
	# this constructs 2^ len(step) trees
	for step in steps:
		main, uber = stepsChoice(step)
		list_to_add = []
		for stepList in stepLists:
			uber_stepList = list(stepList) + [uber]
			main_stepList = stepList + [main]
			list_to_add += [uber_stepList]
			list_to_add += [main_stepList]
		stepLists = list_to_add
	# prune step trees that have nones
	finalRouteList = []
	for stepList in stepLists:
		if None in stepList:
			continue
		finalRoute = {}
		duration, cost = routeStats(stepList) # aggregate the duration and cost
		finalRoute['steps'] = stepList
		finalRoute['duration'] = duration
		finalRoute['cost'] = cost
		finalRouteList += [finalRoute]
	return finalRouteList

def getPlan(start, end):
	direction = api.directions(start, end, mode="transit")[0]['legs'][0] # grabs basic route stuff
	start_loc = direction['start_location']
	end_loc = direction['end_location']
	steps = direction['steps']
	return json.dumps(travelPlans(steps))

from flask import Flask
from flask import request
app = Flask(__name__)

@app.route('/')
def planz():
	start = request.args.get('from')
	end = request.args.get('to')
	return getPlan(start, end)
	# return getPlan("719 washington ave albany ca", "1250 53rd Street, Suite 1. Emeryville, CA 94608")

if __name__ == '__main__':
    app.run()


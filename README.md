======
Portal
======

### Overview

Portal combines public transit and Uber to create routes that are both time and cost-efficient. We wrote the server in Python as it is easy to develop and understand. We use Flask to do routing and HTTP request/response an Google Maps for directions and route information. To run the server, you will need to register for a free Google Maps Web Service API key and enable both Geocoding and Directions in the Google API Console.

### Setup

1. Install node and npm
2. Clone the repo and `cd` into it.
3. Run `npm install`
4. Create a new Python virtualenv.
5. Run `pip install -r requirements.txt`.
6. Get a Google Maps Web Service API key and a Google Maps JavaScript API key from the Google developers' console.
7. Create a new file called `run.sh` and add this line to it
    `GOOGLE_MAPS_SERVER_API_KEY='<WEB SERVICE KEY>' GOOGLE_MAPS_CLIENT_API_KEY='<JAVASCRIPT KEY>' python server.py`
8. Make `run.sh` executable by running `chmod +x run.sh`.
9. Begin watching for front-end React changes by running `npm run watch`
10. Start the server by running `./run.sh`.
11. Visit localhost:8080 in your browser.

### API

`GET /api/v1/route`

**Parameters**

        from: <Address, place name, or coordinate of origin>
        to: <Address, place name, or coordinate of destination>
        
**Response**

Returns an array of routes that combine public transit, walking, and Uber

    [
        "duration": <duration of route in seconds>,
        "start_time": <start time of route in seconds since 1970>,
        "cost": <cost of route in dollars>
        "steps": [
            {
                "description": <human readable instruction>,
                "start_time": <start time of step in seconds since 1970>,
                "departure_time": <actual departure time of public transit vehicle same as start_time if uber of walking>,
                "cost": <cost for this step>,
                "polyline": <array of Google Map polyline strings of this step>,
                "start_lat": <starting latitude of step as a float>,
                "start_lng": <starting longitude of step as a float>,
                "end_lat": <ending latitude of step as a float>,
                "end_lng": <ending longitude of step as a float>,
                "mode": <either 'uber', 'walking', or 'transit'>
            }
            ...
        ],
        "modes": [<methods of transit used in the route, can be 'uber', 'walking', or 'transit']
    ]

### Route Computation

The server uses the following procedure to compute the routes.

1. Query Google Maps API for the public transit route between origin and destination.
2. Take the first result and extract all the steps into a list.
3. Hard-code all public transit fares at `2.5` for each step as an estimation instead of querying Google Maps API for all public transit steps. This saves computational time.
4. Pass the list into `get_all_plans`.
5. If the first step in the list passed into `get_all_plans` requires walking more than 5 minutes or has a distance / duration of less than 8.9 m/s (20 mph) then make a new route with that first step replaced with an Uber. Merge subsequent steps into this first step if they are either walking or they return True on `should_try_uber`. Query Google Maps API for new steps for the rest of the route to take into account Uber and driving time. Pass these new steps recursively into `get_all_plans`. Prepend this Uber step to the routes returned by the recursive call to `get_all_plans`.
6. Pass all steps except for the first step recursively into `get_all_plans`. Prepend the first step to the routes returned by the recursive call to `get_all_plans`.
7. The base case for `get_all_plans` is when there are no steps left.
8. Once we have all routes that reasonably combine Uber and public transit we take each route and, merge consecutive Uber steps into a single Uber step. We also merge walking steps into consecutive Uber steps and vice versa so we have a more reasonable route.
10. Duplicate routes that have the same duration and cost are removed
11. The server finds sorts and finds by most cost-efficient and most time-efficient routes. It selects the top 3 routes from each category and returns 6 final routes. The actual public transit costs for each step are found by querying the Google Maps API for each of the final routes.


### Frontend

Portal Web is written with React and ES6 and uses Node to both transpile code into browser-supported Javascript and also to serve the static files. Styling is written in SCSS to be concise.

**Directory Structure**

`bundles/` Contains the entry-point Javascript file

`components/` Contains all React components

`scss/` Contains style files

`static/` Contains static resources, for example HTML and images

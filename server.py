from os import environ
from json import dumps
from time import mktime
from datetime import datetime, timedelta
from threading import Thread

from flask import Flask, Response, current_app, make_response, render_template, request, send_from_directory, \
    send_file
from flask.ext.heroku import Heroku

from googlemaps import client
from googlemaps.directions import directions
from googlemaps.geocoding import reverse_geocode

from functools import update_wrapper


def crossdomain(origin=None, methods=None, headers=None,
                max_age=21600, attach_to_all=True,
                automatic_options=True):
    if methods is not None:
        methods = ', '.join(sorted(x.upper() for x in methods))
    if headers is not None and not isinstance(headers, basestring):
        headers = ', '.join(x.upper() for x in headers)
    if not isinstance(origin, basestring):
        origin = ', '.join(origin)
    if isinstance(max_age, timedelta):
        max_age = max_age.total_seconds()

    def get_methods():
        if methods is not None:
            return methods

        options_resp = current_app.make_default_options_response()
        return options_resp.headers['allow']

    def decorator(f):
        def wrapped_function(*args, **kwargs):
            if automatic_options and request.method == 'OPTIONS':
                resp = current_app.make_default_options_response()
            else:
                resp = make_response(f(*args, **kwargs))
            if not attach_to_all and request.method != 'OPTIONS':
                return resp

            h = resp.headers
            h['Access-Control-Allow-Origin'] = origin
            h['Access-Control-Allow-Methods'] = get_methods()
            h['Access-Control-Max-Age'] = str(max_age)
            h['Access-Control-Allow-Credentials'] = 'true'
            h['Access-Control-Allow-Headers'] = \
                "Origin, X-Requested-With, Content-Type, Accept, Authorization"
            if headers is not None:
                h['Access-Control-Allow-Headers'] = headers
            return resp

        f.provide_automatic_options = False
        return update_wrapper(wrapped_function, f)
    return decorator


api = client.Client(key=environ.get('GOOGLE_MAPS_SERVER_API_KEY'))


# Function to abstract reversing a location
def place_from_location_string(location_string):
    """Returns a human-readable place name given a string of coordinates."""
    location = [float(component) for component in location_string.split(' ')]
    return reverse_geocode(api, location)[0]['formatted_address']


# Function to abstract getting directions
def google_maps_directions(start, end, **kwargs):
    """Returns directions from Google Maps."""
    return directions(api, start, end, **kwargs)


# Gets the current time in UTC
def get_current_time():
    """Returns time in UTC."""
    return int(mktime(datetime.now().timetuple()))


class Mode:
    """Represents different modes of transportation."""
    UBER = 'uber'
    TRANSIT = 'transit'
    WALKING = 'walking'
    DRIVING = 'driving'
    NONE = 'none'

    def __init__(self):
        raise Exception("This class cannot be instantiated")


class Step:
    """Represents a single step in a route."""
    polyline = []
    duration = 0
    cost = 0
    mode = Mode.NONE
    start_location = ""
    end_location = ""
    description = ""
    start_time = 0
    departure_time = 0
    distance = 0

    def __init__(self, other_step=None):
        if not other_step:
            return
        self.polyline = other_step.polyline
        self.duration = other_step.duration
        self.cost = other_step.cost
        self.mode = other_step.mode
        self.start_location = other_step.start_location
        self.end_location = other_step.end_location
        self.description = other_step.description
        self.start_time = other_step.start_time
        self.departure_time = other_step.departure_time
        self.distance = other_step.distance

    def to_dictionary(self):
        """Returns a dictionary representation of the step."""
        return {
            'polyline': self.polyline,
            'duration': self.duration,
            'cost': self.cost,
            'mode': self.mode,
            'start_lat': float(self.start_location.split(' ')[0]),
            'start_lng': float(self.start_location.split(' ')[1]),
            'end_lat': float(self.end_location.split(' ')[0]),
            'end_lng': float(self.end_location.split(' ')[1]),
            'description': self.description,
            'start_time': self.start_time,
            'departure_time': self.departure_time
        }

    @classmethod
    def from_google_maps_step(cls, absolute_start_time, google_maps_step):
        """Converts a dictionary returned by Google Maps public transit directions to a step."""
        step = Step()
        step.polyline = [google_maps_step['polyline']['points']]
        step.start_location = cls.location_string_from_google_maps_location(google_maps_step['start_location'])
        step.end_location = cls.location_string_from_google_maps_location(google_maps_step['end_location'])
        step.start_time = absolute_start_time
        if 'transit_details' in google_maps_step:
            step_start_time = google_maps_step['transit_details']['departure_time']['value']
            step.departure_time = step_start_time
            step.duration = google_maps_step['duration']['value'] + (step_start_time - absolute_start_time)

            # Placeholder cost for public transit, we will recompute it only for optimal routes
            # This estimation saves time
            step.cost = 2.5
        else:
            step.departure_time = step.start_time
            step.duration = google_maps_step['duration']['value']
            step.cost = 0
        step.distance = google_maps_step['distance']['value']
        step.mode = google_maps_step['travel_mode'].lower()
        step.description = google_maps_step['html_instructions']
        return step

    @classmethod
    def from_google_maps_driving_directions(cls, absolute_start_time, driving_directions):
        """Converts a dictionary returned by Google Maps driving directions to an Uber step."""
        step = Step()
        step.start_time = absolute_start_time
        step.start_location = cls.location_string_from_google_maps_location(driving_directions['start_location'])
        step.end_location = cls.location_string_from_google_maps_location(driving_directions['end_location'])
        step.distance = driving_directions['distance']['value']
        step.duration = driving_directions['duration']['value']
        step.polyline = [direction['polyline']['points'] for direction in driving_directions['steps']]
        step.departure_time = step.start_time
        step.mode = Mode.UBER
        return step

    @classmethod
    def list_from_google_maps_steps(cls, absolute_start_time, google_maps_steps_list):
        """Converts a list of Google Maps transit directions steps into a list of steps."""
        steps_list = []
        for google_maps_step in google_maps_steps_list:
            step = Step.from_google_maps_step(absolute_start_time, google_maps_step)
            steps_list.append(step)
            absolute_start_time += step.duration
        return steps_list

    @classmethod
    def public_transit_fare(cls, start_time, from_location, to_location):
        """Returns the public transit fare between two locations."""
        public_transit_directions = google_maps_directions(from_location, to_location, mode=Mode.TRANSIT,
                                                           departure_time=start_time)[0]
        if 'fare' in public_transit_directions:
            return public_transit_directions['fare']['value']
        else:
            return 0

    @classmethod
    def location_string_from_google_maps_location(cls, location):
        """Converts a location object into a string."""
        return str(location['lat']) + ' ' + str(location['lng'])

    def should_try_uber(self):
        """Returns if Uber is feasible for that step."""
        # If walking takes more than 5 minutes, or public transit's average speed is less than 8.9 m/s.
        # it's a good indication to replace the step with Uber for that segment
        if self.mode == Mode.WALKING and self.duration >= 600:
            return True
        if self.mode == Mode.TRANSIT and (self.duration / self.distance) < 8.9:
            return True
        return False


class Route:
    """Represents the full route."""
    start_time = 0
    cost = 0
    modes = set()
    duration = 0
    steps = []

    def __init__(self):
        pass

    def recalculate_route_statistics(self):
        """Recalculates Uber costs and recomputes the duration and cost for the full route."""

        # Parallelize uber computation
        class UberComputationThread(Thread):
            def __init__(self, uber_step):
                Thread.__init__(self)
                self.step = uber_step

            def run(self):
                consolidated_uber_directions = google_maps_directions(self.step.start_location, self.step.end_location,
                                                                      mode=Mode.DRIVING)[0]['legs'][0]
                self.step.duration = consolidated_uber_directions['duration']['value']
                self.step.polyline = [direction['polyline']['points'] for
                                      direction in consolidated_uber_directions['steps']]
                self.step.description = 'Uber to ' + place_from_location_string(self.step.end_location)
                self.step.cost = calculate_uber_cost(step.duration, consolidated_uber_directions['distance']['value'])

        self.cost = 0
        threads = []
        for step in self.steps:
            if step.mode == Mode.UBER:
                threads.append(UberComputationThread(step))
            else:
                self.cost += step.cost
                self.duration += step.duration
        for thread in threads:
            thread.start()
        for thread in threads:
            thread.join()
        for thread in threads:
            self.cost += thread.step.cost
        if len(self.steps) > 0:
            last_step = self.steps[-1]
            self.duration = (last_step.start_time + last_step.duration) - self.steps[0].start_time
        # End Parallelization

        if len(self.steps) > 0:
            self.start_time = self.steps[0].start_time

    @classmethod
    def from_steps(cls, steps):
        """Creates a route from a list of steps."""
        route = Route()
        route.cost = 0
        route.steps = []
        route.modes = set()
        for step in steps:
            route.modes.add(step.mode)

            # If there are consecutive Uber steps, merge them together.
            if len(route.steps) > 0 and route.steps[-1].mode == Mode.UBER and \
                    (step.mode == Mode.UBER or step.mode == Mode.WALKING):
                route.steps[-1].end_location = step.end_location
                continue
            if len(route.steps) > 0 and route.steps[-1].mode == Mode.WALKING and \
                    (step.mode == Mode.UBER):
                route.steps[-1].end_location = step.end_location
                route.steps[-1].mode = Mode.UBER
                continue
            route.steps.append(Step(step))
        route.recalculate_route_statistics()
        return route

    @classmethod
    def remove_duplicates(cls, routes):
        result = []
        duration_cost_set = set()
        for route in routes:
            if (route.duration, route.cost) in duration_cost_set:
                continue
            duration_cost_set.add((route.duration, route.cost))
            result.append(route)
        return result

    def to_dictionary(self):
        """Returns a dictionary representation of the route."""
        return {
            'start_time': self.start_time,
            'cost': self.cost,
            'modes': list(self.modes),
            'duration': self.duration,
            'steps': [step.to_dictionary() for step in self.steps]
        }

    def recalculate_public_transit_costs(self):
        """Recalculates public transit costs for each step"""

        # Parallelize public transit fare computation
        class PublicTransitComputationThread(Thread):
            def __init__(self, public_transit_step):
                Thread.__init__(self)
                self.step = public_transit_step
                self.cost = 0

            def run(self):
                self.step.cost = Step.public_transit_fare(self.step.start_time,
                                                          self.step.start_location, self.step.end_location)

        self.cost = 0
        threads = []
        for step in self.steps:
            if step.mode == Mode.TRANSIT:
                threads.append(PublicTransitComputationThread(step))
            else:
                self.cost += step.cost
        for thread in threads:
            thread.start()
        for thread in threads:
            thread.join()
        for thread in threads:
            self.cost += thread.step.cost
        # End parallelization


def calculate_uber_cost(duration, distance):
    """Returns the Uber cost given a duration and distance"""
    meters_in_mile = 1609.34
    seconds_in_minute = 60.0

    base_fare = 2.00
    per_minute_cost_in_dollars = 0.22
    per_mile_cost_in_dollars = 1.15
    booking_fee = 1.55
    minimum_fare = 6.55

    miles = distance / meters_in_mile
    minutes = duration / seconds_in_minute
    cost = base_fare + (per_minute_cost_in_dollars * minutes) + (per_mile_cost_in_dollars * miles) + booking_fee
    return max(cost, minimum_fare)


def replace_first_step_with_uber(steps):
    """Replaces the first step with Uber and returns the new first step and the new public transit directions for
    the rest of the route"""
    first_step = steps[0]
    final_destination = steps[-1].end_location
    uber_end_location = first_step.end_location

    # If the next steps are walking, or is Uber feasible, add it to the Uber step
    for step in steps[1:]:
        if step.mode != Mode.WALKING or step.should_try_uber():
            break
        uber_end_location = step.end_location

    uber_directions = google_maps_directions(first_step.start_location,
                                             uber_end_location, mode=Mode.DRIVING)[0]['legs'][0]
    new_first_step = Step.from_google_maps_driving_directions(first_step.start_time, uber_directions)

    new_end_time = first_step.start_time + new_first_step.duration

    if uber_end_location != final_destination:
        public_transit_direction_steps = google_maps_directions(uber_end_location, final_destination,
                                                                departure_time=new_end_time,
                                                                mode=Mode.TRANSIT)[0]['legs'][0]['steps']
    else:
        public_transit_direction_steps = []
    return new_first_step, Step.list_from_google_maps_steps(new_end_time, public_transit_direction_steps)


def prepend_step_to_plans(step, plans):
    """Returns a list of plans with the step prepended to each plan"""
    complete_plans = []
    for partial_plan in plans:
        complete_plan = [step]
        complete_plan.extend(partial_plan)
        complete_plans.append(complete_plan)
    return complete_plans


def get_all_plans(steps):
    """Finds all reasonable combinations with Uber and public transit plans given a list of steps returned
    by Google Maps's public transit directions"""
    if len(steps) == 0:
        return [[]]
    all_plans = []
    first_step = steps[0]
    if first_step.should_try_uber():
        new_first_step, remaining_public_transit_steps = replace_first_step_with_uber(steps)
        all_plans.extend(prepend_step_to_plans(new_first_step, get_all_plans(remaining_public_transit_steps)))
    all_plans.extend(prepend_step_to_plans(first_step, get_all_plans(steps[1:])))
    return all_plans


def select_optimal_routes(all_routes):
    """Filter all possible routes and return only the optimal ones"""
    optimal_routes = set()
    optimal_routes_by_duration = sorted(all_routes, key=lambda individual_route: individual_route.duration)[:3]
    optimal_routes_by_cost = sorted(all_routes, key=lambda individual_route: individual_route.cost)[:3]
    optimal_routes.update(optimal_routes_by_duration)
    optimal_routes.update(optimal_routes_by_cost)

    # Public transit fares require calls to Google Maps API which is slow
    # Recomputing it only for the optimal routes saves a lot of time.

    # Parallelize public transit fare computation
    class PublicTransitFareComputationThread(Thread):
        def __init__(self, public_transit_route):
            Thread.__init__(self)
            self.route = public_transit_route

        def run(self):
            self.route.recalculate_public_transit_costs()
    threads = []
    for route in optimal_routes:
        threads.append(PublicTransitFareComputationThread(route))
    for thread in threads:
        thread.start()
    for thread in threads:
        thread.join()
    # End parellization

    return list(optimal_routes)

app = Flask(__name__)
heroku = Heroku(app)


@app.route('/')
def index():
    return render_template('index.html', client_api_key=environ.get('GOOGLE_MAPS_CLIENT_API_KEY'))

@app.route('/favicon.ico')
def send_favicon():
    return send_file('static/img/favicon.ico')

@app.route('/css/<path:path>')
def send_css(path):
    return send_from_directory('static/css', path)


@app.route('/js/<path:path>')
def send_js(path):
    return send_from_directory('static/js', path)


@app.route('/img/<path:path>')
def send_img(path):
    return send_from_directory('static/img', path)


@app.route('/api/v1/route', methods=['GET', 'OPTIONS'])
@crossdomain(origin='*')
def api_route():
    start = request.args.get('from')
    end = request.args.get('to')
    current_time = get_current_time()

    try:
        public_transit_directions = google_maps_directions(start, end,
                                                        mode=Mode.TRANSIT, departure_time=current_time)[0]['legs'][0]

        absolute_start_time = public_transit_directions['departure_time']['value']
        steps = Step.list_from_google_maps_steps(absolute_start_time, public_transit_directions['steps'])
        plans = get_all_plans(steps)

        # Parallelize route computation
        class RouteComputationThread(Thread):
            def __init__(self, route_steps):
                Thread.__init__(self)
                self.steps = route_steps
                self.route = None

            def run(self):
                self.route = Route.from_steps(self.steps)

        threads = []
        for plan in plans:
            threads.append(RouteComputationThread(plan))
        for thread in threads:
            thread.start()
        for thread in threads:
            thread.join()
        # End parallelization

        all_routes = Route.remove_duplicates([thread.route for thread in threads])
        optimal_routes = select_optimal_routes(all_routes)
        return Response(dumps([route.to_dictionary() for route in optimal_routes]), mimetype='application/json')
    except:
        return Response(dumps([]), mimetype='application/json')

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=8080, debug=True)

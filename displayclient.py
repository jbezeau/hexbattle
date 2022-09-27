import numpy
import requests
import board
import time

URL = 'http://localhost:5000'
# URL = 'http://hexbattle-env.eba-c7dstjkp.us-east-1.elasticbeanstalk.com'
DIMENSIONS_PATH = '/board/dimensions'
TERRAIN_PATH = '/board/terrain'
RESTART_PATH = '/board/reset'
TURN_PATH = '/player/turn'
VICTORY_PATH = '/player/victory'
ACTED_PATH = '/tokens/acted'
ACTIONS_PATH = '/token/actions'
POSITIONS_PATH = '/tokens/positions'
STATUS_PATH = '/tokens/status'


def init_board():
    # restart game whenever needed
    print(f'reset request')
    start = time.perf_counter()
    requests.get(URL+RESTART_PATH)
    end = time.perf_counter()
    duration = end-start
    print(f'duration {duration}')
    
    
def get_dimensions():
    print(f'board dimensions')
    start = time.perf_counter()
    response = requests.get(URL+DIMENSIONS_PATH)
    end = time.perf_counter()
    duration = end-start
    print(f'duration {duration}')

    dimensions = response.json()
    return dimensions


def get_terrain():
    print(f'terrain request')
    start = time.perf_counter()
    response = requests.get(URL+TERRAIN_PATH)
    end = time.perf_counter()
    duration = end - start
    print(f'duration {duration}')

    terrain_data = response.json()
    new_terrain = numpy.zeros((board.X_MAX, board.Y_MAX))
    for key in terrain_data:
        coordinates = board.make_coord_tuple(key)
        new_terrain[coordinates[board.COL], coordinates[board.ROW]] = terrain_data[key]
    return new_terrain


def get_turn():
    # find out which is active side
    print(f'turn request')
    start = time.perf_counter()
    response = requests.get(URL+TURN_PATH)
    end = time.perf_counter()
    duration = end - start
    print(f'duration {duration}')

    color = response.json()
    return color


def get_victory():
    color = None
    print(f'victory request')
    start = time.perf_counter()
    response = requests.get(URL+VICTORY_PATH)
    end = time.perf_counter()
    duration = end - start
    print(f'duration {duration}')

    if len(response.text) > len('\n'):
        color = response.json()
    return color


def post_turn(color):
    # end turn for color
    print(f'turn request')
    start = time.perf_counter()
    response = requests.post(URL+TURN_PATH, json={'side': color})
    end = time.perf_counter()
    duration = end - start
    print(f'duration {duration}')

    new_color = response.json()
    return new_color


def get_acted():
    print(f'acted request')
    start = time.perf_counter()
    response = requests.get(URL+ACTED_PATH)
    end = time.perf_counter()
    duration = end - start
    print(f'duration {duration}')

    new_acted = response.json()
    return new_acted


def get_positions():
    # map coordinates and token keys
    print(f'positions request')
    start = time.perf_counter()
    response = requests.get(URL+POSITIONS_PATH)
    end = time.perf_counter()
    duration = end - start
    print(f'duration {duration}')

    position_data = response.json()
    new_positions = numpy.full([board.X_MAX, board.Y_MAX], '', dtype='S3')
    for key in position_data:
        coordinates = board.make_coord_tuple(int(key))
        new_positions[coordinates[board.COL], coordinates[board.ROW]] = position_data[key]
    return new_positions


def post_position(frm, to):
    coordinates = {board.make_coord_num(frm): board.make_coord_num(to)}
    print(f'positions request')
    start = time.perf_counter()
    response = requests.post(URL+POSITIONS_PATH, json=coordinates)
    end = time.perf_counter()
    duration = end - start
    print(f'duration {duration}')

    position_data = response.json()
    new_positions = numpy.full([board.X_MAX, board.Y_MAX], '', dtype='S3')
    for key in position_data:
        position = board.make_coord_tuple(int(key))
        new_positions[position[board.COL], position[board.ROW]] = position_data[key]
    return new_positions


def get_actions(frm):
    frm_num = board.make_coord_num(frm)
    print(f'actions request')
    start = time.perf_counter()
    response = requests.post(URL+ACTIONS_PATH, json={'hex': frm_num})
    end = time.perf_counter()
    duration = end - start

    print(f'duration {duration}')
    action_list = response.json()
    return action_list


def get_units():
    # token keys and attributes
    print(f'status request')
    start = time.perf_counter()
    response = requests.get(URL+STATUS_PATH)
    end = time.perf_counter()
    duration = end - start
    print(f'duration {duration}')

    new_units = response.json()
    return new_units

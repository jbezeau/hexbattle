import numpy
import requests
import board
import time

#URL = 'http://localhost:5000'
URL = 'http://hexbattle-env.eba-c7dstjkp.us-east-1.elasticbeanstalk.com'
DIMENSIONS_PATH = '/board/dimensions'
TERRAIN_PATH = '/board/terrain'
TURN_PATH = '/turn'
ACTED_PATH = '/turn/acted'
ACTIONS_PATH = '/actions'
POSITIONS_PATH = '/positions'
STATUS_PATH = '/status'
RESTART_PATH = '/board/reset'
VICTORY_PATH = '/victory'


def init_board():
    # restart game whenever needed
    print(f'reset request')
    start = time.time()
    requests.get(URL+RESTART_PATH)
    end = time.time()
    duration = end-start
    print(f'duration {duration}')


def get_terrain():
    print(f'terrain request')
    start = time.time()
    response = requests.get(URL+TERRAIN_PATH)
    end = time.time()
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
    start = time.time()
    response = requests.get(URL+TURN_PATH)
    end = time.time()
    duration = end - start
    print(f'duration {duration}')

    color = response.json()
    return color


def get_victory():
    color = None
    print(f'victory request')
    start = time.time()
    response = requests.get(URL+VICTORY_PATH)
    end = time.time()
    duration = end - start
    print(f'duration {duration}')

    if len(response.text) > len('\n'):
        color = response.json()
    return color


def post_turn(color):
    # end turn for color
    print(f'turn request')
    start = time.time()
    response = requests.post(URL+TURN_PATH, json={'side': color})
    end = time.time()
    duration = end - start
    print(f'duration {duration}')

    new_color = response.json()
    return new_color


def get_acted():
    print(f'acted request')
    start = time.time()
    response = requests.get(URL+ACTED_PATH)
    end = time.time()
    duration = end - start
    print(f'duration {duration}')

    new_acted = response.json()
    return new_acted


def get_positions():
    # map coordinates and token keys
    print(f'positions request')
    start = time.time()
    response = requests.get(URL+POSITIONS_PATH)
    end = time.time()
    duration = end - start
    print(f'duration {duration}')

    position_data = response.json()
    new_positions = numpy.full([board.X_MAX, board.Y_MAX], '', dtype='S3')
    for key in position_data:
        coordinates = board.make_coord_tuple(int(key))
        new_positions[coordinates[board.COL], coordinates[board.ROW]] = position_data[key]
    return new_positions


def post_position(frm, to):
    coordinates = {'Start': board.make_coord_num(frm), 'End': board.make_coord_num(to)}
    coord_list = [coordinates]
    print(f'positions request')
    start = time.time()
    response = requests.post(URL+POSITIONS_PATH, json={'hexes': coord_list})
    end = time.time()
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
    start = time.time()
    response = requests.post(URL+ACTIONS_PATH, json={'hex': frm_num})
    end = time.time()
    duration = end - start

    print(f'duration {duration}')
    action_list = response.json()
    return action_list


def get_units():
    # token keys and attributes
    print(f'status request')
    start = time.time()
    response = requests.get(URL+STATUS_PATH)
    end = time.time()
    duration = end - start
    print(f'duration {duration}')

    new_units = response.json()
    return new_units


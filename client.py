import numpy
import requests
import board

URL = 'http://localhost:5000'
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
    requests.get(URL+RESTART_PATH)


def get_terrain():
    response = requests.get(URL+TERRAIN_PATH)
    terrain_data = response.json()
    new_terrain = numpy.zeros((board.X_MAX, board.Y_MAX))
    for key in terrain_data:
        coordinates = board.make_coord_tuple(key)
        new_terrain[coordinates[board.COL], coordinates[board.ROW]] = terrain_data[key]
    return new_terrain


def get_turn():
    # find out which is active side
    response = requests.get(URL+TURN_PATH)
    color = response.json()
    return color


def get_victory():
    color = None
    response = requests.get(URL+VICTORY_PATH)
    if len(response.text) > len('\n'):
        color = response.json()
    return color


def post_turn(color):
    # end turn for color
    response = requests.post(URL+TURN_PATH, json={'side': color})
    new_color = response.json()
    return new_color


def get_acted():
    response = requests.get(URL+ACTED_PATH)
    new_acted = response.json()
    return new_acted


def get_positions():
    # map coordinates and token keys
    response = requests.get(URL+POSITIONS_PATH)
    position_data = response.json()
    new_positions = numpy.full([board.X_MAX, board.Y_MAX], '', dtype='S3')
    for key in position_data:
        coordinates = board.make_coord_tuple(int(key))
        new_positions[coordinates[board.COL], coordinates[board.ROW]] = position_data[key]
    return new_positions


def post_position(frm, to):
    coordinates = {'Start': board.make_coord_num(frm), 'End': board.make_coord_num(to)}
    coord_list = [coordinates]
    response = requests.post(URL+POSITIONS_PATH, json={'hexes': coord_list})
    position_data = response.json()
    new_positions = numpy.full([board.X_MAX, board.Y_MAX], '', dtype='S3')
    for key in position_data:
        position = board.make_coord_tuple(int(key))
        new_positions[position[board.COL], position[board.ROW]] = position_data[key]
    return new_positions


def get_actions(frm):
    frm_num = board.make_coord_num(frm)
    response = requests.post(URL+ACTIONS_PATH, json={'hex': frm_num})
    action_list = response.json()
    return action_list


def get_units():
    # token keys and attributes
    response = requests.get(URL+STATUS_PATH)
    new_units = response.json()
    return new_units


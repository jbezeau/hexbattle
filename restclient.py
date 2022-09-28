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

SAVE_TERRAIN_PATH = '/edit/terrain'
SAVE_POSITIONS_PATH = '/edit/positions'
SAVE_STATUS_PATH = '/edit/status'
SAVE_COMMIT = '/edit/save'


def _fill_terrain(terrain_data):
    new_terrain = numpy.zeros((board.X_MAX, board.Y_MAX))
    for key in terrain_data:
        coordinates = board.make_coord_tuple(int(key))
        new_terrain[coordinates[board.COL], coordinates[board.ROW]] = terrain_data[key]
    return new_terrain


def _fill_positions(position_data):
    new_positions = numpy.full([board.X_MAX, board.Y_MAX], '', dtype='S3')
    for key in position_data:
        coordinates = board.make_coord_tuple(int(key))
        unit_id = position_data[key].encode('UTF-8')
        new_positions[coordinates[board.COL], coordinates[board.ROW]] = unit_id
    return new_positions


def _get(path):
    print(path)
    start = time.perf_counter()
    response = requests.get(URL+path)
    duration = time.perf_counter() - start
    print(f'duration {duration}')
    return response.json()


def _post(path, data):
    print(path)
    start = time.perf_counter()
    response = requests.post(URL+path, json=data)
    duration = time.perf_counter() - start
    print(f'duration {duration}')
    return response.json()


def init_board():
    _get(RESTART_PATH)
    
    
def get_dimensions():
    return _get(DIMENSIONS_PATH)


def get_terrain():
    terrain_data = _get(TERRAIN_PATH)
    return _fill_terrain(terrain_data)


def get_turn():
    return _get(TURN_PATH)


def get_victory():
    color = None
    win = _get(VICTORY_PATH)
    if win != 'None':
        color = win
    return color


def post_turn(color):
    return _post(TURN_PATH, color)


def get_acted():
    new_acted = _get(ACTED_PATH)
    return new_acted


def get_positions():
    # map coordinates and token keys
    position_data = _get(POSITIONS_PATH)
    return _fill_positions(position_data)


def post_position(frm, to):
    coordinates = {board.make_coord_num(frm): board.make_coord_num(to)}
    position_data = _post(POSITIONS_PATH, coordinates)
    return _fill_positions(position_data)


def get_actions(frm):
    frm_num = board.make_coord_num(frm)
    action_list = _post(ACTIONS_PATH, {'hex': frm_num})
    return action_list


def get_units():
    # token keys and attributes
    return _get(STATUS_PATH)


def save_terrain(terrain):
    data = {}
    for x in range(board.X_MAX):
        for y in range(board.Y_MAX):
            if terrain[x, y] != 0:
                hex_id = board.make_coord_num((x, y))
                data[hex_id] = terrain[x, y]
    terrain_data = _post(SAVE_TERRAIN_PATH, data)
    return _fill_terrain(terrain_data)


def save_positions(positions):
    data = {}
    for x in range(board.X_MAX):
        for y in range(board.Y_MAX):
            if positions[x, y] != b'':
                hex_id = board.make_coord_num((x, y))
                data[hex_id] = positions[x, y].decode('UTF-8')
    position_data = _post(SAVE_POSITIONS_PATH, data)
    return _fill_positions(position_data)


def save_status(status):
    return _post(SAVE_STATUS_PATH, status)


def save_commit():
    return _get(SAVE_COMMIT)

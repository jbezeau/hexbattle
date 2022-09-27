import numpy
import requests
import board
import time

URL = 'http://localhost:5000'
# URL = 'http://hexbattle-env.eba-c7dstjkp.us-east-1.elasticbeanstalk.com'
DIMENSIONS_PATH = '/board/dimensions'
TERRAIN_PATH = '/board/terrain'
RESTART_PATH = '/board/reset'
POSITIONS_PATH = '/tokens/positions'
STATUS_PATH = '/tokens/status'
SAVE_TERRAIN_PATH = '/edit/terrain'
SAVE_POSITIONS_PATH = '/edit/positions'
SAVE_STATUS_PATH = '/edit/status'


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


def save_terrain(new_terrain):
    out = {}
    for x in board.X_MAX:
        for y in board.Y_MAX:
            if new_terrain[x, y] != 0:
                hex_id = board.make_coord_num((x, y))
                out[hex_id] = new_terrain[x, y]
    response = requests.get(URL+SAVE_TERRAIN_PATH, json=out)

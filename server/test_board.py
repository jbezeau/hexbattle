import board
import json
import numpy

b = board.Board()
for i in range(board.X_MAX):
    for j in range(board.Y_MAX):
        if board.check_pos([i, j]) is False:
            b.terrain[i, j] = -100

# check some coordinates
print("position test: False")
print(board.check_pos((-1, -1)))
print(board.check_pos([6, 6]))
print(board.check_pos([-1, 2]))
print(board.check_pos([4, 6]))
print(board.check_pos([4, 5]))

print("position test: True")
print(board.check_pos([0, 0]))
print(board.check_pos([1, 1]))
print(board.check_pos([5, 5]))

# check some moves
print("movement test: False")
print(b.check_1move([1, 1], [-1, -1]))
print(b.check_1move([-1, -1], [1, 1]))
print(b.check_1move([5, 5], [6, 6]))
print(b.check_1move([6, 6], [5, 5]))
print(b.check_1move([3, 1], [5, 1]))
print(b.check_1move([5, 1], [3, 1]))
print(b.check_1move([2, 2], [2, -1]))
print(b.check_1move([2, 4], [2, 6]))
print(b.check_1move([2, 2], [4, 4]))
print(b.check_1move([5, 5], [6, 6]))
print(b.check_1move([6, 6], [5, 5]))

print("movement test: True")
print(b.check_1move([1, 1], [2, 2]))
print(b.check_1move([3, 3], [2, 2]))
print(b.check_1move([3, 3], [3, 5]))
print(b.check_1move([3, 3], [3, 1]))

# check distances
print("distance test: Numeric")
dist = board.get_distance([1, 1], [5, 5])
rslt = dist == 8
print(f'Distance {dist} test pass {rslt}')
dist = board.get_distance([1, 1], [5, 1])
rslt = dist == 8
print(f'Distance {dist} test pass {rslt}')
dist = board.get_distance([1, 1], [4, 2])
rslt = dist == 6
print(f'Distance {dist} test pass {rslt}')
dist = board.get_distance([1, 1], [1, 5])
rslt = dist == 4
print(f'Distance {dist} test pass {rslt}')

print('Terrain test: False')
# set boundaries
b.terrain[1, 3] = 1
b.terrain[3, 1] = 1
print(f'Terrain clear [3,1] {b.check_clear([3, 1])}')
print(f'Terrain clear [1,3] {b.check_clear([1, 3])}')
print('Terrain test: True')
print(f'Terrain clear [3,3] {b.check_clear([3, 3])}')

print('Path test: List')
p = b.get_path([1, 1], [5, 1])
print(f'Path from 1,1 to 5,1 {p}')
p = b.get_path([1, 1], [1, 5])
print(f'Path from 1,1 to 1,5 {p}')
p = b.get_path([-1, -1], [3, 3])
print(f'Path from invalid tile {p}')
p = b.get_path([1, 1], [3, 4])
print(f'Path to invalid tile {p}')

print('Block [2,2] and find path to [3,3]')
b.terrain[2, 2] = 1
p = b.get_path([1, 1], [5, 1])
print(f'Path around obstacle {p}')
p = b.get_path([2, 2], [3, 3])
print(f'Path from blocked tile {p}')
p = b.get_path([1, 1], [2, 2])
print(f'Path to blocked tile {p}')

print('test various actions')
b.positions[2, 4] = b'R1'
b.positions[4, 4] = b'B1'
b.positions[4, 2] = b'BT1'
print(f'Initial HP totals {b.color_totals()}')
print(f'Check Red turn {b.turn} (Red)')
print(f'Attack at range 2 for soldier {b.resolve_action((2, 4), (4, 4))} (True)')
print(f'Check 1 HP {b.tokens.get(b"B1")}')
print(f'Try repeating same action {b.resolve_action((2, 4), (4, 4))} (False)')
b.finish_turn()
print(f'Move blue soldier towards red soldier {b.resolve_action((4, 4), (3, 5))} (True)')
print(f'Move tank to [1, 5] {b.check_action((4, 2), (1, 5))} (True)')
b.finish_turn()
print(f'Move red soldier to capture blue soldier {b.resolve_action((2, 4), (3, 5))} (True)')
print(f'Check blue soldier {b.tokens.get(b"B1")}')
b.finish_turn()
print(f'Shoot red soldier with blue tank {b.resolve_action((1, 5), (3, 5))}')
print(f'Check red soldier {b.tokens.get(b"R1")}')
b.finish_turn()
print(f'Check victory {b.victory}')

# exercise database stuff
config_id = b.save_config()
print(f'Saved board as config {config_id}')
b.reset()
b.delete_config()

config_json, weights = b.load_model('1')
print(f'Load config {config_json}')
config = json.loads(config_json).get('config')
for layer in config.get('layers'):
    print(layer.get('config').get('name'))
print(f'Load weights {len(weights)}')
for w in weights:
    print(w.shape)
print(weights[0][0:, 0])
print(weights[1][0])
print(weights[2][0, 0:])

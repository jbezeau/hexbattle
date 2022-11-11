import numpy
import keras as k

import board

# channels for board data
INP_TERRAIN = 0
INP_COLOR = 1
INP_HEALTH = 2
INP_MOVE = 3
INP_SHOOT = 4
INP_CHANNELS = 5
LAYER_SIZE = board.X_MAX*board.Y_MAX

# todo: split model... one for token selection, one for destination selection


def generate_model(model_json=None):
    if model_json:
        m = k.models.model_from_json(model_json)
    else:
        m = k.models.Sequential()
        m.add(k.layers.Input(shape=(INP_CHANNELS, board.X_MAX, board.Y_MAX//2)))
        m.add(k.layers.Flatten())
        m.add(k.layers.Dense(units=LAYER_SIZE, activation='relu'))
        m.add(k.layers.Dense(units=LAYER_SIZE//2, activation='sigmoid'))

    m.compile(loss='mse', metrics='accuracy')
    return m


def generate_input(b):
    # board only uses half of its array to make adjacent hex coordinates consistent: (x+-1, y+-1) and (x, y+-2)
    # to minimize input layer size we can compress by a factor of 2 on Y axis
    input_cube = numpy.zeros((INP_CHANNELS, board.X_MAX, board.Y_MAX//2))
    token_pos = []
    flag_pos = None
    for i in range(board.X_MAX):
        for j in range(board.Y_MAX):
            if i % 2 == j % 2:
                # we want to encode features of the board and tokens into channels on a 2D array
                # terrain, acting/finished/opponent {-1, 0, +1}, hp, move, shoot
                input_cube[INP_TERRAIN, i, j//2] = b.terrain[i, j]
                token_chars = b.positions[i, j]
                token = b.tokens.get(token_chars)
                if token is not None and b.acted.count(token_chars) == 0:
                    if token.get(board.SIDE) == b.turn and token.get(board.HP) > 0:
                        # only mark playable units, so weed out flags and dead units
                        token_pos.append((i, j))
                    else:
                        # mark enemy positions
                        input_cube[INP_COLOR, i, j//2] = 1
                        if token.get(board.TYPE) == board.FLAG:
                            # for setting action expectations later
                            flag_pos = (i, j)
                    input_cube[INP_HEALTH, i, j//2] = token.get(board.HP)
                    input_cube[INP_MOVE, i, j//2] = token.get(board.MV)
                    input_cube[INP_SHOOT, i, j//2] = token.get(board.RNG)

    # leave reshaping expect_cube for later
    return input_cube.reshape(1, INP_CHANNELS, board.X_MAX, board.Y_MAX//2), token_pos, flag_pos


def generate_execute_expectation(b, selection):
    # positive values on legal tiles for actions
    # caller must ensure selection result in token value
    # selection co-ordinates are game board correct
    expect_cube = numpy.zeros((board.X_MAX, board.Y_MAX//2))
    x, y = selection

    token_chars = b.positions[x, y]
    token = b.tokens.get(token_chars)
    print(f'selected {token_chars}: {token}')

    min_x = max(0, x-token[board.RNG])
    max_x = min(board.X_MAX, x+token[board.RNG])
    min_y = max(0, y-token[board.RNG])
    max_y = min(board.Y_MAX, y+token[board.RNG])

    # check every tile within shooting range for viability
    for i in range(min_x, max_x):
        for j in range(min_y, max_y):
            if expect_cube[i, j//2] == 0 and b.check_action((x, y), (i, j)):
                expect_cube[i, j//2] = 1

    # reshape when passing to train_on_batch
    return expect_cube


def make_coordinate(xp, yp):
    # reverse the coordinate flattening we did in generate_input
    # double the y-prime value, and add 1 if the x position is odd
    return xp, yp * 2 + xp % 2


def interpret_output(p):
    # only need one interpret function for both models' output
    # both use same shape and highest output is coordinate selection
    conf = 0
    pick = []

    # save coordinates for the highest output we've seen so far
    for i in range(board.X_MAX):
        for j in range(board.Y_MAX//2):
            if p[i, j] > conf:
                conf = p[i, j]
                pick.append(make_coordinate(i, j))

    # return selected coordinates
    return pick.pop()


if __name__ == '__main__':
    game_board = board.Board()
    model_data = None
    total_attempts = 0

    print(f'Available player models: {game_board.list_models()}')
    model_id = input('Enter model number to load [ENTER for new model]:')
    if len(model_id) > 0:
        model_data = game_board.load_model(model_id)
    execute_model = generate_model(model_data)

    print(f'Available configurations: {game_board.list_configs()}')
    config_id = input('Enter configuration number [ENTER for none]:')
    if len(config_id) > 0:
        game_board.load_config(config_id)
        game_board.create_session(f'learningplayer {model_id}')

    # master play condition
    while game_board.victory is None:
        print(game_board.turn)
        input_data, token_list, opp_flag = generate_input(game_board)

        if len(token_list) == 0:
            # couldn't find a playable unit
            game_board.finish_turn()
            continue

        frm = token_list.pop()
        select_x, select_y = frm

        # remember we're on batch item 0 when marking our active token
        input_data[0, INP_COLOR, select_x, select_y//2] = -1
        execute_expected = generate_execute_expectation(game_board, frm)
        print(execute_expected)

        # now trap the network in here until it puts the piece down on a legal tile
        execute_loop = True
        step_attempts = 0
        while execute_loop:
            step_attempts += 1
            # replace input player tokens with token selection
            execute_prediction = execute_model.predict(input_data)
            execute_metrics = execute_model.train_on_batch(input_data, execute_expected.reshape(1, board.X_MAX * board.Y_MAX//2))
            to = interpret_output(execute_prediction.reshape(board.X_MAX, board.Y_MAX//2))
            if to is not None and game_board.resolve_action(frm, to):
                execute_loop = False
                print(f'move {to} in {step_attempts} tries')
        total_attempts += step_attempts
    print(f'Game won by {game_board.victory} after total {total_attempts} attempts')

    save = input(f'Save model {model_id}? [y/N]: ')
    if save[0] == 'y' or save[0] == 'Y':
        game_board.save_model(execute_model.to_json(), model_id)

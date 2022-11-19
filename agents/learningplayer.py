import numpy
import keras as k

from server import board

# channels for board data
INP_TERRAIN = 0
INP_COLOR = 1
INP_HEALTH = 2
INP_MOVE = 3
INP_SHOOT = 4
INP_CHANNELS = 5
LAYER_SIZE = board.X_MAX * board.Y_MAX // 2


# LearningPlayer class holds on to model instance
class LearningPlayer:
    def __init__(self, model_id=None):
        # None model_id will load the latest model
        self.m = None
        self.all_inputs = None
        self.all_rewards = None
        self.history_length = 0
        self.model_id = model_id

    def new_model(self, b):
        self.m = generate_model()
        self.model_id = b.save_model(self.m, b)

    def play_token(self, b, train=False, flip=None):
        # todo set up so we have explicit load model and init from application
        if self.m is None:
            if self.model_id is None:
                # auto-init to latest model
                models = b.list_models()
                if models is not None:
                    model_row = models.pop()
                    self.model_id = model_row[0]
            if self.model_id is not None:
                data, weights = b.load_model(self.model_id)
            self.m = generate_model(data, weights)

        # play token and record what we did
        state, move = move_token(b, self.m, train, flip)

        if state is None:
            # we ended our turn instead of moving a token
            # so reverse reward weights for training
            # every token Red moves rewards Red / punishes Blue, and vice-versa
            if self.all_rewards is not None:
                self.all_rewards = numpy.multiply(self.all_rewards, -1)

            # automatically save model on victory
            if b.victory is not None:
                save_model(self.m, b, self.model_id)
            return 0
        else:
            # we moved a token so remember the starting state
            # create an expectation map marking the spot we moved to
            self.history_length += 1
            to_x = move[board.COL]
            to_y = move[board.ROW] // 2
            if state[0, INP_COLOR, to_x, to_y] == 1:
                # reward for attacking an opponent token
                reward_value = 0.5
            else:
                # reward for moving to empty tile
                reward_value = 0.25
            state_reward = numpy.zeros((board.X_MAX, board.Y_MAX // 2))
            state_reward[to_x, to_y] = reward_value
            if self.all_inputs is None:
                self.all_inputs = state
                self.all_rewards = state_reward
            else:
                self.all_inputs = numpy.append(self.all_inputs, state)
                self.all_rewards = numpy.append(self.all_rewards, state_reward)
            # reshape total history for input layer
            train_inputs = self.all_inputs.reshape((self.history_length, INP_CHANNELS, board.X_MAX, board.Y_MAX // 2))
            # add 0.5 to total rewards so training values are 0 or 1, and reshape for output layer
            train_rewards = numpy.add(self.all_rewards, 0.5).reshape(self.history_length, LAYER_SIZE)
            self.m.fit(train_inputs, train_rewards, verbose=0)
            return 1


def generate_model(data=None, weights=None):
    if data:
        m = k.models.model_from_json(data)
    else:
        m = k.models.Sequential()
        m.add(k.layers.Input(shape=(INP_CHANNELS, board.X_MAX, board.Y_MAX // 2)))
        m.add(k.layers.Flatten())
        m.add(k.layers.Dense(units=LAYER_SIZE*2, activation='relu'))
        m.add(k.layers.Dense(units=LAYER_SIZE, activation='sigmoid'))

    if weights:
        m.set_weights(weights)

    m.compile(loss='mse', metrics='accuracy')
    return m


def save_model(m, b, model_id=None):
    # None model_id to save on new row
    return b.save_model(m.to_json(), m.get_weights(), model_id)


def scan_board(b):
    # board only uses half of its array to make adjacent hex coordinates consistent: (x+-1, y+-1) and (x, y+-2)
    # to minimize input layer size we can compress by a factor of 2 on Y axis
    input_cube = numpy.zeros((INP_CHANNELS, board.X_MAX, board.Y_MAX // 2))
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
    return input_cube.reshape(1, INP_CHANNELS, board.X_MAX, board.Y_MAX // 2), token_pos, flag_pos


def generate_execute_expectation(b, selection, flag):
    # place positive values on legal tiles for actions
    # caller must ensure selection result in token value
    # selection co-ordinates are game board values
    expect_cube = numpy.zeros((board.X_MAX, board.Y_MAX // 2))
    x, y = selection
    total_value = 0

    token_chars = b.positions[x, y]
    token = b.tokens.get(token_chars)

    # shooting range is longer than movement range
    # selected token set has to exclude flags
    min_x = max(0, x - token[board.RNG])
    max_x = min(board.X_MAX, x + token[board.RNG])
    min_y = max(0, y - token[board.RNG])
    max_y = min(board.Y_MAX, y + token[board.RNG])

    # check every tile within shooting range for viability
    for i in range(min_x, max_x):
        for j in range(min_y, max_y):
            if b.check_move(selection, (i, j)):
                if token.get(board.TYPE) == board.SOLDIER:
                    # encourage soldiers to take the enemy flag
                    token_dist = board.get_distance(selection, flag)
                    tile_dist = board.get_distance((i, j), flag)
                    move_value = token_dist / (2 + tile_dist)
                    expect_cube[i, j//2] = move_value
                    total_value += move_value
                else:
                    move_value = 0.5
                    expect_cube[i, j//2] = move_value
                    total_value += move_value
            if b.check_shoot(selection, (i, j)):
                expect_cube[i, j//2] = 1
                total_value += 1

    if total_value == 0:
        # dump the game board to find out why we have a state with no valid moves
        print(f'Warning! No valid moves for token {token_chars}')
        print(b.positions)
        return None

    # reshape when passing to train_on_batch
    return expect_cube


def make_coordinate(xp, yp):
    # reverse the coordinate flattening we did in generate_input
    # double the y-prime value, and add 1 if the x position is odd
    return xp, yp * 2 + xp % 2


def interpret_output(p):
    # just ask numpy where the highest value is
    index = numpy.argmax(p)

    # and then parse out the obscure output format
    j = index % (board.Y_MAX // 2)
    i = index // (board.Y_MAX // 2)

    return make_coordinate(i, j)


def move_token(b, m, train=True, flip=None):
    # update token locations and status (HP)
    # input_data is our output for experience learning later
    input_data, token_list, opp_flag = scan_board(b)

    if len(token_list) == 0:
        # no tokens to move
        b.finish_turn()
        return None, None

    for frm in token_list:
        # sometimes tokens will be stuck behind friendly units so we have to skip them
        select_x, select_y = frm
        # remember we're on batch item 0 when marking our active token
        input_data[0, INP_COLOR, select_x, select_y // 2] = -1
        execute_expected = generate_execute_expectation(b, frm, opp_flag)
        if execute_expected is not None:
            break

    if execute_expected is None:
        # last playable token has no legal moves
        b.finish_turn()
        return None, None

    # now trap the network in here until it puts the piece down on a legal tile
    # use expectation as a mask for prediction, so that illegal moves are never considered
    execute_prediction = m.predict(input_data, verbose=0)
    execute_prediction = execute_prediction.reshape(board.X_MAX, board.Y_MAX // 2)
    masked_prediction = numpy.multiply(execute_prediction, execute_expected)
    to = interpret_output(masked_prediction)

    if train:
        # training uses the highest probability move and retrains on expectations if not legal
        if flip.count('X') > 0:
            input_data = numpy.flip(input_data, 2)
            execute_expected = numpy.flip(execute_expected, 0)
        if flip.count('Y') > 0:
            input_data = numpy.flip(input_data, 3)
            execute_expected = numpy.flip(execute_expected, 1)
        m.fit(input_data, execute_expected.reshape(1, LAYER_SIZE), verbose=0)

    token = b.positions[frm[board.COL], frm[board.ROW]]
    legal = b.resolve_action(frm, to)
    if legal:
        print(f'{token} {frm} to {to}')
        return input_data, to
    else:
        token = b.positions[frm[board.COL], frm[board.ROW]]
        print(f'ILLEGAL: {token} {frm} to {to}')
        return None, None


if __name__ == '__main__':
    numpy.set_printoptions(precision=2)
    game_board = board.Board()
    player = None
    total_attempts = 0

    print(f'Available player models: {game_board.list_models()}')
    model_input = input('Enter model number to load [ENTER for new model]:')
    player = LearningPlayer(model_input)
    if model_input is None:
        player.new_model(game_board)

    print(f'Available configurations: {game_board.list_configs()}')
    config_id = input('Enter configuration number [ENTER for none]:')
    if len(config_id) > 0:
        game_board.load_config(config_id)
        game_board.create_session(f'learningplayer {player.model_id}')

    flip_mode = input('Enter axis flip: X, Y, XY, [None]:')

    # master play condition
    total_moves = 0
    while game_board.victory is None:
        total_moves += player.play_token(game_board, True, flip_mode)
    print(f'Game won by {game_board.victory} after {total_moves} moves')

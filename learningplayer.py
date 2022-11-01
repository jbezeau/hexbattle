import numpy
import tensorflow
import keras

import board

FLAT_MAX = board.X_MAX * board.Y_MAX


def flatten_board(terrain, pos, tokens):
    flat_pos = numpy.zeros(FLAT_MAX * 7)
    for i in range(board.X_MAX):
        for j in range(board.Y_MAX):
            # we want to one-hot encode everything on the board into a single linear array
            # all of these inputs will be pretty sparse, seems necessary if we want to preserve unit type & team
            # first X*Y entries are terrain
            flat_i = i * board.X_MAX + j
            if terrain(i, j) != 0:
                flat_pos[flat_i] = 1

            if pos(i, j) != b'':
                token = tokens.get(pos(i, j))
                match token[board.TYPE]:
                    case board.SOLDIER:
                        # second X*Y are red soldiers
                        flat_j = 1
                    case board.TANK:
                        # fourth X*Y are red tanks
                        flat_j = 3
                    case board.FLAG:
                        # sixth X*Y are red flags
                        flat_j = 5
                if token[board.SIDE] == board.BLUE:
                    # third X*Y are blue soldiers
                    # fifth X*Y are blue tanks
                    # seventh X*Y are blue flags
                    flat_j += 1
                # flat_i represents where we are on the board, flat_j represents token group
                flat_pos[flat_i + FLAT_MAX * flat_j] = 1
    return flat_pos


if __name__ == '__main__':
    b = board.Board()
    configs = b.list_configs()
    b.load_config(configs[0])
    b.create_session('learningplayer')

    model = tensorflow.keras.models.Sequential()
    model.add(tensorflow.keras.layers.Input(shape=(board.X_MAX, board.Y_MAX, 7)))
    model.add(tensorflow.keras.layers.Dense(units=300, activation='relu'))
    model.add(tensorflow.keras.layers.Dense(units=300, activation='relu'))
    model.add(tensorflow.keras.layers.Dense(units=400, activation='sigmoid'))
    model.compile()

    input_data = flatten_board(b.terrain, b.positions, b.tokens)

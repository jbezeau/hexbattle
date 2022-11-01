import board


def play_turn(b):
    # these structures are going to contain coordinate:unit status
    # we'll use functions built for the REST API
    tokens = {}
    targets = {}
    
    # basis for movement actions
    flag = None

    print(f'Acting player {b.turn}')

    # scan the board positions to make lists with positions and status
    for i in range(board.X_MAX):
        for j in range(board.Y_MAX):
            if b.positions[i, j] != b'':
                token_status = b.tokens.get(b.positions[i, j])
                if token_status[board.SIDE] == b.turn:
                    # all our units in a list, minus the flag
                    if token_status[board.TYPE] != board.FLAG:
                        tokens[board.make_coord_num((i, j))] = token_status
                else:
                    if token_status[board.TYPE] == board.FLAG:
                        # enemy flag is necessary for movement
                        flag = (i, j)
                        print(f'Target flag: {token_status} at {flag}')
                    else:
                        # all the enemy in a list, minus the flag
                        targets[board.make_coord_num((i, j))] = token_status

    # go over the lists and see if any of our tokens can shoot an enemy
    # otherwise move towards the flag co-ordinates identified previously
    for tok in tokens:
        token_status = tokens.get(tok)
        token_coord = board.make_coord_tuple(int(tok))
        action_coord = None

        # check if you can shoot any enemy
        for tgt in targets:
            target_status = targets.get(tgt)
            target_coord = board.make_coord_tuple(int(tgt))
            dist = board.get_distance(token_coord, target_coord)
            if dist <= token_status[board.RNG] and target_status[board.TYPE] != board.FLAG:
                action_coord = target_coord

        # follow a path to the enemy flag, there is zero strategy to this logic
        if action_coord is None:
            path = b.get_path(board.make_coord_tuple(tok), flag)
            steps = min(len(path), token_status[board.MV])
            action_coord = path[steps-1]

        # do immediately, action_coord shouldn't be None but you never know
        if action_coord is not None:
            print(f'{token_coord} to {action_coord}')
            b.resolve_action(token_coord, action_coord)


if __name__ == '__main__':
    game_board = board.Board()
    print(f'Available configurations: {game_board.list_configs()}')
    config = input('Enter configuration number [None]:')
    if len(config) > 0:
        game_board.load_config(config)
        game_board.create_session('simpleplayer')
    while game_board.victory is None:
        play_turn(game_board)
        game_board.finish_turn()
    print(f'Winning player {game_board.victory}')

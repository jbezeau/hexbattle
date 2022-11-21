from flask import Flask, request
import json
import board
from agents import simpleplayer, learningplayer

application = Flask(__name__)
b = board.Board()
nn = learningplayer.LearningPlayer()


@application.route('/hexbattle')
def welcome_page():
    return 'Welcome!\n', 200


@application.route('/board/reset')
def reset():
    b.reset()
    return json.dumps('Reset')+'\n', 202


@application.route('/board/dimensions')
def get_dimensions():
    # functions that output aspects of the map will have sparse output
    # so we need one function to tell clients what the maximum map dimensions are
    return json.dumps([board.X_MAX, board.Y_MAX]) + '\n', 200


@application.route('/board/terrain')
def get_terrain():
    return b.output_terrain() + '\n', 200


@application.route('/player/turn', methods=['GET', 'POST'])
def end_turn():
    # post data {"side": "Red"} to end turn for Red
    # so an interface acting for Blue can't end Red's turn etc
    # obviously this is courtesy rather than security
    # TODO generate a one-time token the interface uses to validate /turn posts
    status = 200
    if request.method == 'POST':
        turn_txt = request.get_json()
        turn = json.loads(turn_txt)
        if turn.get('side') == b.turn:
            b.finish_turn()
            status = 201
    return json.dumps(b.turn)+'\n', status


@application.route('/simpleplayer/turn')
def simple_turn():
    status = 200
    simpleplayer.play_turn(b)
    b.finish_turn()
    return json.dumps(b.turn)+'\n', status


@application.route('/learningplayer/list')
def model_list():
    return json.dumps(b.list_models()), 200


@application.route('/learningplayer/init', methods=['POST'])
def learning_init():
    model_id = request.get_json()
    if nn.m is None:
        # set model_id if model hasn't been loaded
        nn.model_id = model_id
        status = 201
    else:
        status = 403
    return json.dumps(nn.model_id), status


@application.route('/learningplayer/turn')
def learning_turn():
    # AI moves just one token and ends turn if no more
    side = b.turn
    while side == b.turn and b.victory is None:
        nn.play_token(b)
    return json.dumps(b.turn)+'\n', 200


@application.route('/player/victory')
def get_victory():
    if b.victory is not None:
        out = json.dumps(b.victory)
    else:
        out = json.dumps('None')
    return out+'\n', 200


@application.route('/tokens/status')
def show_units():
    return b.output_units() + '\n', 200


@application.route('/tokens/acted')
def show_acted():
    # output list of units that have acted in the turn
    # convert unit key bytes to strings
    str_key_list = []
    for key in b.acted:
        str_key_list.append(key.decode("UTF-8"))
    return json.dumps(str_key_list)+'\n', 200


@application.route('/token/actions', methods=['POST'])
def show_valid_moves():
    # previously display would iterate over all positions, asking board if a move was valid
    # we shouldn't be so inefficient with REST requests so this handler does the iteration
    token = request.get_json()
    frm = board.make_coord_tuple(token['hex'])
    moves = []
    for x in range(board.X_MAX):
        for y in range(board.Y_MAX):
            to = (x, y)
            if b.check_action(frm, to):
                moves.append(board.make_coord_num(to))
    out = json.dumps(moves)
    return out+'\n', 200


@application.route('/tokens/positions', methods=['GET', 'POST'])
def update_positions():
    # player posts a list of {'token_xxyy':action_xxyy, ...}
    # we try to take all of those actions in order
    status = 200
    if request.method == 'POST':
        moves = request.get_json()
        for hex_key in moves:
            hex_num = int(hex_key)
            b.resolve_action(board.make_coord_tuple(hex_num), board.make_coord_tuple(moves[hex_key]))
        status = 201
    return b.output_positions() + '\n', status


@application.route('/edit/terrain', methods=['POST'])
def edit_terrain():
    # expect {'hex_num':elevation, ...}
    terrains = request.get_json()
    for hex_key in terrains:
        hex_num = int(hex_key)
        x, y = board.make_coord_tuple(hex_num)
        b.terrain[x, y] = terrains[hex_key]
    return b.output_terrain() + '\n', 201


@application.route('/edit/positions', methods=['POST'])
def edit_positions():
    # expect {'hex_num':unit_id}, ...}
    positions = request.get_json()
    for hex_key in positions:
        hex_num = int(hex_key)
        x, y = board.make_coord_tuple(hex_num)
        b.positions[x, y] = positions[hex_key]
    return b.output_positions() + '\n', 201


@application.route('/edit/status', methods=['POST'])
def edit_units():
    # expect {unit_id: {stat block}}
    # debate between adding / replacing units in default list, and replacing entire list
    # I like the thought of not having to re-specify the flags and tanks
    units = request.get_json()
    for token in units:
        b.tokens[token.encode('UTF-8')] = units[token]
    return b.output_units() + '\n', 201


@application.route('/edit/save')
def commit_edit():
    config_num = b.save_config()
    return json.dumps({'config': config_num})+'\n', 201


@application.route('/session/list', methods=['GET', 'POST'])
def session_list():
    player_id = None
    if request.method == 'POST':
        player_id = request.get_json()
    rows = b.list_sessions(player_id)
    return json.dumps(rows)+'\n', 200


@application.route('/session/join', methods=['POST'])
def session_join():
    # join a numbered session
    session_id = request.get_json()
    b.join_session(session_id)
    return json.dumps(True)+'\n', 201


@application.route('/session/create', methods=['POST'])
def session_create():
    # quick length limit on player ID, same as UI
    # strings have a built-in test for alphanumeric character content
    player_id = request.get_json()
    if player_id.isalnum():
        session_id = b.create_session(player_id[:50])
        return json.dumps(session_id)+'\n', 201
    else:
        return json.dumps(player_id), 403


@application.route('/board/list')
def config_list():
    rows = b.list_configs()
    return json.dumps(rows)+'\n', 200


@application.route('/board/load', methods=['POST'])
def config_load():
    config_id = request.get_json()
    new_config = b.load_config(config_id)
    return json.dumps(new_config)+'\n', 202


if __name__ == '__main__':
    application.run()


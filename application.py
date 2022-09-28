from flask import Flask, request
import json
import board

application = Flask(__name__)
b = board.Board()


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
    return json.dumps([board.X_MAX, board.Y_MAX])+'\n', 200


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
        post = request.get_json()
        if post["side"] == b.turn:
            b.finish_turn()
            status = 201
    return json.dumps(b.turn)+'\n', status


@application.route('/player/victory')
def get_victory():
    status = 200
    out = 'None'
    if b.victory is not None:
        out = json.dumps(b.victory)
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


if __name__ == '__main__':
    application.run()


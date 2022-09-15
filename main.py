from flask import Flask, request
import json
import board

app = Flask(__name__)
b = board.Board()


@app.route('/hexbattle')
def welcome_page():
    return 'Welcome!\n', 200


@app.route('/board/reset')
def reset():
    b.reset()
    return json.dumps('Reset')+'\n', 202


@app.route('/board/dimensions')
def get_dimensions():
    # functions that output aspects of the map will have sparse output
    # so we need one function to tell clients what the maximum map dimensions are
    return json.dumps([board.X_MAX, board.Y_MAX])+'\n', 200


@app.route('/board/terrain')
def get_terrain():
    pos = {}
    status = 200
    for x in range(board.X_MAX):
        for y in range(board.Y_MAX):
            elevation = b.terrain[x, y]
            if elevation != 0:
                pos[board.make_coord_num((x, y))] = elevation
    out = json.dumps(pos)
    return out+'\n', status


@app.route('/turn', methods=['GET', 'POST'])
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


@app.route('/victory')
def get_victory():
    status = 200
    out = ''
    if b.victory is not None:
        out = json.dumps(b.victory)
    return out+'\n', 200


@app.route('/status')
def show_units():
    # output the master unit list with current HP and so on
    # convert unit key bytes to strings so JSON can handle it
    str_key_dict = {}
    for key in b.tokens:
        str_key = key.decode("UTF-8")
        str_key_dict[str_key] = b.tokens[key]
    out = json.dumps(str_key_dict)
    return out+'\n', 200


@app.route('/turn/acted')
def show_acted():
    # output list of units that have acted in the turn
    # convert unit key bytes to strings
    str_key_list = []
    for key in b.acted:
        str_key_list.append(key.decode("UTF-8"))
    return json.dumps(str_key_list)+'\n', 200


@app.route('/actions', methods=['POST'])
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


@app.route('/positions', methods=['GET', 'POST'])
def update_positions():
    # player posts a list of [{Start:xxyy, End:xxyy},{...}]
    # we try to take all of those actions in order
    status = 200
    if request.method == 'POST':
        moves = request.get_json()
        for move in moves['hexes']:
            start = move['Start']
            end = move['End']
            b.resolve_action(board.make_coord_tuple(start), board.make_coord_tuple(end))
        status = 201

    # return state of the board in the form [{xxyy: {unit_stats}},{...}]
    pos = {}
    for x in range(board.X_MAX):
        for y in range(board.Y_MAX):
            unit = b.positions[x, y]
            if unit != b'':
                val = unit.decode("UTF-8")
                # convert (x, y) coordinate to xxyy digits
                pos[board.make_coord_num((x, y))] = val
    out = json.dumps(pos)
    return out+'\n', status


if __name__ == '__main__':
    app.run(debug=True)


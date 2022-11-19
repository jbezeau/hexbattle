from server import dbconnect
import json
import numpy

# keep my column and row index references straight
COL = 0
ROW = 1

# forces on the board
RED = 'Red'
BLUE = 'Blue'

# token types
SOLDIER = 'S'
TANK = 'T'
FLAG = 'F'

# keys for token info
TYPE = 'Type'
SIDE = 'Side'
HP = 'HP'
MV = 'MP'
RNG = 'Range'
ATK = 'Attack'

# token templates
# copying a dict like a tank definition and adding an attribute for color is extra lines of code
# as it is these have to be set in unit list with .copy() to avoid corrupting original value
RED_SOLDIER = {TYPE: SOLDIER, HP: 2, MV: 1, ATK: 1, RNG: 2, SIDE: RED}
BLUE_SOLDIER = {TYPE: SOLDIER, HP: 2, MV: 1, ATK: 1, RNG: 2, SIDE: BLUE}
RED_TANK = {TYPE: TANK, HP: 4, MV: 3, ATK: 2, RNG: 4, SIDE: RED}
BLUE_TANK = {TYPE: TANK, HP: 4, MV: 3, ATK: 2, RNG: 4, SIDE: BLUE}
RED_FLAG = {TYPE: FLAG, HP: 0, MV: 0, ATK: 0, RNG: 0, SIDE: RED}
BLUE_FLAG = {TYPE: FLAG, HP: 0, MV: 0, ATK: 0, RNG: 0, SIDE: BLUE}

# board dimensions, these should not vary from map to map for consistent NNET input layer
X_MAX = 11
Y_MAX = 16
TURNS = [RED, BLUE]


class Board:
    def __init__(self, config=0):
        self.terrain = None
        self.positions = None
        self.tokens = {}
        self.turn = None
        self.acted = []
        self.turn_summary = []
        self.victory = None
        # time to connect to data
        # only the database connection knows about session_id
        self.config_id = config
        self.database = dbconnect.DBConnection()
        self.reset()

    def reset(self):
        # use 1 array for each token type, effectively a one-hot encoding of tokens
        # initialize co-ords [0,0] to [X_MAX,Y_MAX]
        if not self.load_config(self.config_id):
            self.terrain = numpy.zeros([X_MAX, Y_MAX])
            self.positions = numpy.full([X_MAX, Y_MAX], '', dtype='S3')
            self.positions[1, 3] = 'RF1'
            self.positions[2, 4] = 'RT1'
            self.positions[3, 5] = 'R1'
            self.positions[3, 3] = 'R2'
            self.positions[2, 6] = 'R3'
            self.positions[9, 13] = 'BF1'
            self.positions[8, 12] = 'BT1'
            self.positions[7, 11] = 'B1'
            self.positions[8, 10] = 'B2'
            self.positions[7, 13] = 'B3'

            self.tokens[b'RF1'] = RED_FLAG.copy()
            self.tokens[b'R1'] = RED_SOLDIER.copy()
            self.tokens[b'R2'] = RED_SOLDIER.copy()
            self.tokens[b'R3'] = RED_SOLDIER.copy()
            self.tokens[b'RT1'] = RED_TANK.copy()
            self.tokens[b'BF1'] = BLUE_FLAG.copy()
            self.tokens[b'B1'] = BLUE_SOLDIER.copy()
            self.tokens[b'B2'] = BLUE_SOLDIER.copy()
            self.tokens[b'B3'] = BLUE_SOLDIER.copy()
            self.tokens[b'BT1'] = BLUE_TANK.copy()
        self.turn = TURNS[0]
        while len(self.acted) > 0:
            self.acted.pop(0)
        while len(self.turn_summary) > 0:
            self.turn_summary.pop(0)
        self.turn_summary
        self.victory = None

    # todo fix the mess I made by building a facade for self.database in board
    # unfortunately there are a couple of database methods that do a lot of internal state
    # and then a whole bunch where we just pass through and back
    # I don't want to split the calls between Board( ) and Board( ).database even if that's cleaner code

    def save_config(self):
        # board config_id represents which saved state the game initializes to
        if self.database.enable:
            self.config_id = self.database.save_board(self.output_terrain(), self.output_positions(), self.output_units())
        return self.config_id

    def list_configs(self):
        # force attempt to connect with database connection
        if self.database.enable:
            return self.database.list_boards()
        else:
            return None

    def load_config(self, config_id):
        # get board configuration by number
        # apply those settings to the map and tokens
        load = False
        if self.database.enable:
            config = self.database.load_board(config_id)
            if config is not None:
                terrain_config = json.loads(config[0])
                position_config = json.loads(config[1])
                token_config = json.loads(config[2])
                for terrain_num, elevation in terrain_config.items():
                    terrain_coords = make_coord_tuple(int(terrain_num))
                    self.terrain[terrain_coords[COL], terrain_coords[ROW]] = int(elevation)
                for position_num, token_id in position_config.items():
                    position_coords = make_coord_tuple(int(position_num))
                    self.positions[position_coords[COL], position_coords[ROW]] = token_id.encode('UTF-8')
                for token_id, token_stats in token_config.items():
                    self.tokens[token_id.encode("UTF-8")] = token_stats
                load = True
                self.config_id = config_id
        return load

    def delete_config(self):
        if self.database.enable:
            self.database.delete_board(self.config_id)

    def list_sessions(self, player_id):
        if self.database.enable:
            return self.database.list_sessions(player_id)
        else:
            return None

    def join_session(self, session_id):
        # only the db connection knows session_id values
        if self.database.enable:
            self.config_id = self.database.join_session(session_id)
            self.load_config(self.config_id)

    def create_session(self, player_id):
        # inserts session record and sets session_id value in the db connection
        # we've already loaded the related ID
        if self.database.enable:
            return self.database.create_session(self.config_id, player_id)

    def save_model(self, config_json, model_weights, model_id=None):
        if self.database.enable:
            # weird that keras will dump model configuration directly to JSON
            # but weights are just kicked out as a list of numpy arrays and I have to handle them
            weight_list = []
            for layer_weights in model_weights:
                # don't know why I have to dumps each list
                weight_list.append(json.dumps(layer_weights.tolist()))
            json_weights = json.dumps(weight_list)
            return self.database.save_model(config_json, json_weights, model_id)

    def list_models(self):
        if self.database.enable:
            return self.database.list_models()
        else:
            return None

    def load_model(self, model_id):
        # jump through all the serialization hoops here
        if self.database.enable:
            model_rows = self.database.load_model(model_id)
            model_config = model_rows[0]
            model_weights = None
            if model_rows[1] is not None:
                weight_list = json.loads(model_rows[1])
                model_weights = []
                for w in weight_list:
                    w_array = numpy.array(json.loads(w))
                    model_weights.append(w_array)
            return model_config, model_weights
        else:
            return None, None

    def finish_turn(self):
        # don't pass turn if game has been won
        if self.victory is None:
            # put any non-zero HP value in a map for each opponent
            # we only iterate the token list once this way
            totals = self.color_totals()

            # quick check for mutual destruction
            eliminated = list(totals.values()).count(0)
            if eliminated == len(TURNS):
                self.victory = 'Draw'
                self.turn = None
                return self.turn

            # turn goes to the next side in rotation with surviving units
            # we've already caught the no-exit case for this while loop
            next_turn = self.turn
            hp = 0
            while hp == 0:
                # modulate over index positions for players in game
                next_turn = next_color(next_turn)
                # see if they have any survivors
                hp = totals.get(next_turn)

            # if only one side has survivors, they win
            # otherwise, pass turn to next side with units to play
            if self.turn == next_turn:
                self.victory = self.turn
                if self.database.enable:
                    self.database.close_session()
            else:
                self.turn = next_turn
                if self.database.enable:
                    self.database.post_turn(self.output_turn_actions(), self.output_positions(), self.output_units())

            self.acted = []
            return self.turn
        return None

    def color_totals(self):
        # assign tokens to lists for each side for easy counting
        # this will help for figuring out turn values in learningplayer
        color_totals = {}

        for color in TURNS:
            color_totals[color] = 0

        for key in self.tokens:
            unit = self.tokens[key]
            add = unit.get(HP)
            if add is not None:
                color_totals[unit.get(SIDE)] += add

        return color_totals

    def check_move(self, frm, to):
        # test to see if a move is legal
        frm_key = self.positions[frm[COL], frm[ROW]]
        frm_token = self.tokens.get(frm_key)
        to_key = self.positions[to[COL], to[ROW]]
        to_token = self.tokens.get(to_key)
        if frm_token is not None:
            path = self.get_path(frm, to)
            if path is None:
                return False
            check_dist = frm_token[MV] >= len(path)
            if to_token is None:
                return check_dist
            elif frm_token[TYPE] == SOLDIER:
                check_oppo = frm_token[SIDE] != to_token[SIDE]
                return check_dist and check_oppo
        return False

    def check_shoot(self, frm, to):
        # test to see if an attack is legal
        frm_key = self.positions[frm[COL], frm[ROW]]
        to_key = self.positions[to[COL], to[ROW]]
        frm_token = self.tokens.get(frm_key)
        to_token = self.tokens.get(to_key)
        if frm_token is not None and to_token is not None:
            check_range = 2 * frm_token[RNG] + 1 > get_distance(frm, to)
            check_oppo = frm_token[SIDE] != to_token[SIDE] and to_token[TYPE] != FLAG
            return check_range and check_oppo
        return False

    def check_action(self, frm, to):
        # test to see if a game input is some kind of legal action
        return self.check_move(frm, to) or self.check_shoot(frm, to)

    def resolve_action(self, frm, to):
        # execute on a game input
        frm_key = self.positions[frm[COL], frm[ROW]]
        frm_token = self.tokens.get(frm_key)

        to_key = self.positions[to[COL], to[ROW]]
        to_token = self.tokens.get(to_key)

        # choose a token
        if frm_token is None:
            return False

        # make sure frm token is on the acting player's side
        if self.turn != frm_token[SIDE]:
            return False

        # make sure frm token has not already acted
        if self.acted.count(frm_key) > 0:
            return False

        if self.check_move(frm, to):
            self.positions[frm[COL], frm[ROW]] = ''
            self.positions[to[COL], to[ROW]] = frm_key
            if frm_token[TYPE] == SOLDIER:
                # destroy the captured unit for purpose of counting playable tokens by HP
                if to_token is not None:
                    to_token[HP] = 0

                    # capturing flag converts all units for that side to their captor
                    if to_token[TYPE] == FLAG:
                        captured_side = to_token[SIDE]
                        for key in self.tokens:
                            unit = self.tokens[key]
                            if unit[SIDE] == captured_side:
                                unit[SIDE] = frm_token[SIDE]
            self.acted.append(frm_key)
            self.turn_summary.append([int(make_coord_num(frm)), int(make_coord_num(to))])
            return True

        if self.check_shoot(frm, to):
            to_token[HP] -= frm_token[ATK]
            if to_token[HP] <= 0:
                # eliminate overkill, we're prone to checking for exactly 0
                to_token[HP] = 0
                self.positions[to[COL], to[ROW]] = ''
            self.acted.append(frm_key)
            self.turn_summary.append([int(make_coord_num(frm)), int(make_coord_num(to))])
            return True

        return False

    def get_path(self, frm, to):
        # find and report the path frm->to
        # it's dijkstra time

        # check for invalid input
        if not self.check_clear(frm):
            return None
        if not self.check_clear(to):
            return None

        # we want to evaluate all paths frm->to
        # create another map, filling in the lowest score we've found to reach each hex in between
        # add terrain map just to illustrate impassible tiles as 100s
        costs = numpy.ones([X_MAX, Y_MAX]) * 99
        costs += self.terrain
        costs[frm[COL], frm[ROW]] = 0

        # recursive bit for depth-first traversal
        # trim initial position off of results
        # result will be None if no path was found
        path = self.path_step(costs, [frm], to, 0)
        # don't print costs, we can visualize moves now
        if path is not None:
            path.reverse()
            return path[1:]
        else:
            return None

    def path_step(self, costs, explore_list, to, old_length):
        # recursive part of get_path algo
        for explore in explore_list:
            # quickly detect exit conditions
            if explore == to:
                # found it
                costs[to[COL], to[ROW]] = old_length
                return [to]
            elif explore_list is None:
                return None
            elif len(explore_list) == 0:
                return None

            # set up iteration parameters
            length = old_length + 1
            current_dist = get_distance(explore, to)
            closer_list = []
            equal_list = []
            farther_list = []

            # add every hex around the current exploration point to the exploration list
            # those closer to the destination than the start point are given priority
            # because we step one hex at a time all steps are either closer by one, equal, or farther by one
            for i in [-1, +1]:
                for j in [-1, +1]:
                    new_explore = (explore[COL] + i, explore[ROW] + j)
                    if self.check_clear(new_explore):
                        new_dist = get_distance(new_explore, to)
                        if costs[new_explore[COL], new_explore[ROW]] > length:
                            costs[new_explore[COL], new_explore[ROW]] = length
                            if current_dist > new_dist:
                                closer_list.append(new_explore)
                            elif current_dist == new_dist:
                                equal_list.append(new_explore)
                            else:
                                farther_list.append(new_explore)
            for k in [-2, +2]:
                new_explore = (explore[COL], explore[ROW] + k)
                if self.check_clear(new_explore):
                    new_dist = get_distance(new_explore, to)
                    if costs[new_explore[COL], new_explore[ROW]] > length:
                        costs[new_explore[COL], new_explore[ROW]] = length
                        if current_dist > new_dist:
                            closer_list.append(new_explore)
                        elif current_dist == new_dist:
                            equal_list.append(new_explore)
                        else:
                            farther_list.append(new_explore)

            # sets of lists are specific to explore instance so this must be in the outer iteration
            path = self.path_step(costs, closer_list, to, length)
            if path is None:
                path = self.path_step(costs, equal_list, to, length)
            if path is None:
                path = self.path_step(costs, farther_list, to, length)
            if path is not None:
                path.append(explore)
                return path

    def check_1move(self, frm, to):
        # to simplify hexagon movement, we only use every second Y position
        # 1,3     3,3     5,3     ...
        #     2,2     4,1     ...
        # 1,1     3,1     5,1     ...
        # [X,Y] can move to [X,Y-2] [X,Y+2] [X-1,Y-1] [X-1][Y+1] [X+1,Y-1] [X+1,Y+1]
        # can not move [X-2,Y] or [X+2,Y]
        # not moving is a valid move

        valid_frm = self.check_clear(frm)
        valid_to = self.check_clear(to)
        valid_move = get_distance(frm, to) < 3

        return valid_frm and valid_to and valid_move

    def check_clear(self, coord):
        if check_pos(coord):
            return self.terrain[coord[COL], coord[ROW]] == 0
        return False

    # serialization for REST calls
    def output_terrain(self):
        # return state of the board in the form {xxyy: terrain elevation, ...}
        pos = {}
        for x in range(X_MAX):
            for y in range(Y_MAX):
                if x % 2 == y % 2:
                    elevation = self.terrain[x, y]
                    if elevation != 0:
                        pos[make_coord_num((x, y))] = elevation
        return json.dumps(pos)

    def output_positions(self):
        # return state of the board in the form {xxyy: unit_id,...}
        pos = {}
        for x in range(X_MAX):
            for y in range(Y_MAX):
                unit = self.positions[x, y]
                if unit != b'':
                    val = unit.decode("UTF-8")
                    # convert (x, y) coordinate to xxyy digits
                    pos[make_coord_num((x, y))] = val
        return json.dumps(pos)

    def output_units(self):
        # output the master unit list with current HP and so on
        # convert unit key bytes to strings so JSON can handle it
        str_key_dict = {}
        for key in self.tokens:
            str_key = key.decode("UTF-8")
            str_key_dict[str_key] = self.tokens[key]
        return json.dumps(str_key_dict)

    def output_turn_actions(self):
        # serialize which actions were taken in the player turn
        return json.dumps(self.turn_summary)


def make_coord_num(tpl):
    return tpl[COL]*100+tpl[ROW]


def make_coord_tuple(num):
    y = num % 100
    x = num//100
    return tuple([x, y])


def check_pos(coord):
    # is coordinate on the map?
    bounds = -1 < coord[COL] < X_MAX and -1 < coord[ROW] < Y_MAX

    # is coordinate part of hex system?
    parity = coord[COL] % 2 == coord[ROW] % 2

    return bounds and parity


def get_distance(frm, to):
    # remember that the distance between adjacent hexes is 2
    # hexes at X-2 and X+2 positions are reached in two steps (distance 4)
    # so for mostly-horizontal distances the distance is twice the travel on the X-axis
    x_dist = abs(to[COL] - frm[COL])
    y_dist = abs(to[ROW] - frm[ROW])
    return x_dist + max({x_dist, y_dist})


def next_color(color):
    # modulate over index positions for n players in game
    idx = (TURNS.index(color) + 1) % len(TURNS)
    return TURNS[idx]





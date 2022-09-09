import numpy

# keep my column and row index references straight
COL = 0
ROW = 1

# forces on the board
RED = 'Red'
BLUE = 'Blue'
OPPONENTS = [RED, BLUE]

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
RED_SOLDIER = {TYPE: SOLDIER, HP: 2, MV: 1, ATK: 1, RNG: 3, SIDE: RED}
BLUE_SOLDIER = {TYPE: SOLDIER, HP: 2, MV: 1, ATK: 1, RNG: 3, SIDE: BLUE}
RED_TANK = {TYPE: TANK, HP: 4, MV: 4, ATK: 2, RNG: 9, SIDE: RED}
BLUE_TANK = {TYPE: TANK, HP: 4, MV: 4, ATK: 2, RNG: 9, SIDE: BLUE}
RED_FLAG = {TYPE: FLAG, SIDE: RED}
BLUE_FLAG = {TYPE: FLAG, SIDE: BLUE}

# board dimensions
# 0,0 is bottom left
X_MAX = 6
Y_MAX = 6
TURNS = [RED, BLUE]


class Board:
    def __init__(self):
        # use 1 array for each token type, effectively a one-hot encoding of tokens
        # initialize co-ords [0,0] to [X_MAX,Y_MAX]
        self.terrain = numpy.zeros([X_MAX, Y_MAX])
        self.positions = numpy.full([X_MAX, Y_MAX], '', dtype='S3')
        self.tokens = {b'RF': RED_FLAG.copy(),
                       b'r1': RED_SOLDIER.copy(),
                       b'R1': RED_TANK.copy(),
                       b'BF': BLUE_FLAG.copy(),
                       b'b1': BLUE_SOLDIER.copy(),
                       b'B1': BLUE_TANK.copy()}
        self.turn = TURNS[0]
        self.acted = []

    def finish_turn(self):
        idx = (TURNS.index(self.turn)+1) % len(TURNS)
        self.turn = TURNS[idx]
        self.acted = []

    def check_action(self, frm, to):
        # update action array and return True if legal move
        # return False if illegal move
        frm_key = self.positions[frm[COL], frm[ROW]]
        print(f'initial tile {frm} id {frm_key}')
        frm_token = self.tokens.get(frm_key)
        print(f'acting unit {frm_token}')

        to_key = self.positions[to[COL], to[ROW]]
        print(f'destination tile {to} id {to_key}')
        to_token = self.tokens.get(to_key)
        if to_token is not None:
            print(f'destination token {to_token}')

        # choose a token
        if frm_token is None:
            print(f'No acting token at position {frm}')
            return False

        # make sure frm token is on the acting player's side
        if self.turn != frm_token[SIDE]:
            print(f'Acting side {self.turn} chose opposing token')
            return False

        # make sure frm token has not already acted
        if self.acted.count(frm_key) > 0:
            print(f'Acting side {self.turn} has already used token {frm_key} this turn')
            return False

        if frm_token[TYPE] == SOLDIER:
            # legal to move 1 space, any enemy in the target hex is destroyed
            if self.check_1move(frm, to) and (to_token is None or frm_token[SIDE] != to_token[SIDE]):
                self.positions[frm[COL], frm[ROW]] = ''
                self.positions[to[COL], to[ROW]] = frm_key

                # eliminate unit landed on by soldier
                if to_token is not None:
                    self.tokens.pop(to_key)
                self.acted.append(frm_key)
                print(f'soldier move')
                return True

            # legal to attack 2 spaces distance for 1 damage
            if get_distance(frm, to) < 5 and frm_token[SIDE] != to_token[SIDE]:
                # reduce target by 1 hp
                to_token[HP] -= frm_token[ATK]
                if to_token[HP] < 1:
                    self.tokens.pop(to_token)
                self.acted.append(frm_key)
                print(f'soldier attack')
                return True

        if frm_token[TYPE] == TANK:
            # legal to fire 4 spaces, get_distance counts each hex as 2
            if to_token is not None and frm_token[SIDE] != to_token[SIDE] and \
                    get_distance(frm, to) < frm_token[RNG]:
                # reduce target by 2 hp so 'bb' -> '' or 'RRRR' -> 'RR'
                to_token[HP] -= frm_token[ATK]
                if to_token[HP] < 1:
                    self.tokens.pop(to_key)
                self.acted.append(frm_key)
                print(f'tank attack')
                return True
            p = self.get_path(frm, to)
            print(f'tank path {p}')
            if len(p) < frm_token[MV]:
                # we could use steps in p to run over anything in the tank's path
                # but each player's turn is supposed to be non-sequential
                # it would matter if units moved before or after the tank
                self.positions[frm[COL], frm[ROW]] = ''
                self.positions[to[COL], to[ROW]] = frm_key
                self.acted.append(frm_key)
                print(f'tank move')
                return True
        return False

    def get_path(self, frm, to):
        # find and report the path frm->to
        # it's dijkstra time

        # check for invalid input
        if not self.check_clear(frm):
            print(f'Invalid start coordinate {frm}')
            return None
        if not self.check_clear(to):
            print(f'Invalid end coordinate {to}')
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
        print(costs)
        if path is not None:
            path.reverse()
        return path[1:]

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
            length = old_length+1
            current_dist = get_distance(explore, to)
            closer_list = []
            equal_list = []
            farther_list = []

            # add every hex around the current exploration point to the exploration list
            # those closer to the destination than the start point are given priority
            # because we step one hex at a time all steps are either closer by one, equal, or farther by one
            for i in [-1, +1]:
                for j in [-1, +1]:
                    new_explore = [explore[COL] + i, explore[ROW] + j]
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
                new_explore = [explore[COL], explore[ROW] + k]
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


def check_friendly_token(frm_token, to_token):
    red_v_red = check_red_token(frm_token) and check_red_token(to_token)
    blue_v_blue = check_blue_token(frm_token) and check_blue_token(to_token)
    return red_v_red or blue_v_blue


def check_enemy_token(frm_token, to_token):
    red_v_blue = check_red_token(frm_token) and check_blue_token(to_token)
    blue_v_red = check_blue_token(frm_token) and check_red_token(to_token)
    return red_v_blue or blue_v_red


def check_soldier_token(token):
    return token[0] == 'b' or token[0] == 'r'


def check_tank_token(token):
    return token[0] == 'B' or token[0] == 'R'


def check_red_token(token):
    return token[0] == 'r' or token[0] == 'R'


def check_blue_token(token):
    return token[0] == 'b' or token[0] == 'B'


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

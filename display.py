import pygame as pg
import board
import restclient

BG_COLOR = (64, 64, 64)
RED_COLOR = (170, 32, 32)
GREEN_COLOR = (32, 170, 32)
BLUE_COLOR = (32, 32, 170)
ORANGE_COLOR = (170, 85, 42)

SCALE = 8
ORIGIN = [64, 64]

SELECT = 'Select Unit'
CONFIRM = 'Confirm Order'
VICTORY = 'Victory'

END = 'End Turn'
RESTART = 'New Game'


# global state for display
pg.init()
screen = pg.display.set_mode((1280, 640), pg.SCALED)
pg.mouse.set_visible(True)

if pg.font:
    font = pg.font.Font(None, 64)
    small_font = pg.font.Font(None, 32)

background = pg.Surface(screen.get_size())
background = background.convert()
background.fill((64, 64, 64))

text_surface = pg.Surface(screen.get_size())
text_surface = text_surface.convert()
text_surface.fill((0, 0, 0))
text_surface.set_colorkey((0, 0, 0))

token_surface = pg.Surface(screen.get_size())
token_surface = token_surface.convert()
token_surface.fill((0, 0, 0))
token_surface.set_colorkey((0, 0, 0))

overlay_surface = pg.Surface(screen.get_size())
overlay_surface = overlay_surface.convert_alpha()
overlay_surface.fill((0, 0, 0, 0))


def clear():
    background.fill((64, 64, 64))
    token_surface.fill((0, 0, 0))
    text_surface.fill((0, 0, 0))
    overlay_surface.fill((0, 0, 0, 0))


def get_scaled_coordinates(coordinates):
    hx = 8 * coordinates[board.COL] * SCALE + ORIGIN[board.COL]
    hy = 4 * coordinates[board.ROW] * SCALE + ORIGIN[board.ROW]
    return [hx, hy]


def get_elevation_color(terrain, coordinates):
    elevation = terrain[coordinates[board.COL], coordinates[board.ROW]]
    greyscale = min(255, 32*elevation + 128)
    grey_tuple = (greyscale, greyscale, greyscale)
    return grey_tuple


def get_triangle(coordinates):
    pt = get_scaled_coordinates(coordinates)
    x = pt[board.COL]
    y = pt[board.ROW]
    return [(x, y-SCALE), (x+SCALE, y+SCALE), (x-SCALE, y+SCALE)]


def get_square(coordinates):
    pt = get_scaled_coordinates(coordinates)
    x = pt[board.COL]
    y = pt[board.ROW]
    return [(x+SCALE, y-SCALE), (x+SCALE, y+SCALE), (x-SCALE, y+SCALE), (x-SCALE, y-SCALE)]


def get_pentagon(coordinates):
    pt = get_scaled_coordinates(coordinates)
    x = pt[board.COL]
    y = pt[board.ROW]
    return [(x, y-SCALE), (x+SCALE, y-SCALE/4), (x+3*SCALE/4, y+SCALE), (x-3*SCALE/4, y+SCALE), (x-SCALE, y-SCALE/4)]


def get_hexagon(coordinates):
    pt = get_scaled_coordinates(coordinates)
    x = pt[board.COL]
    y = pt[board.ROW]
    return ((x-5*SCALE, y), (x-3*SCALE, y-4*SCALE), (x+3*SCALE, y-4*SCALE),
            (x+5*SCALE, y), (x+3*SCALE, y+4*SCALE), (x-3*SCALE, y+4*SCALE))


def draw_board(terrain):
    new_tiles = {}
    for x in range(board.X_MAX):
        for y in range(board.Y_MAX):
            if board.check_pos((x, y)):
                tile = pg.draw.polygon(background, get_elevation_color(terrain, (x, y)), get_hexagon((x, y)))
                pg.draw.polygon(background, BG_COLOR, get_hexagon((x, y)), 4)
                new_tiles[tuple(tile)] = (x, y)
    return new_tiles


def draw_state_text(win, state):
    text_surface.fill((0, 0, 0))
    if pg.font:
        if win == board.RED:
            text = font.render(VICTORY, True, RED_COLOR)
        elif win == board.BLUE:
            text = font.render(VICTORY, True, BLUE_COLOR)
        else:
            text = font.render(state, True, (32, 32, 32))
        text_pos = text.get_rect(centerx=3 * background.get_width() / 4, centery=background.get_height() / 4)
        text_surface.blit(text, text_pos)


def draw_tokens(positions, tokens, acted=[]):
    token_surface.fill((0, 0, 0))
    for x in range(board.X_MAX):
        for y in range(board.Y_MAX):
            if board.check_pos((x, y)):
                # array representation of token keys are byte data
                # have to convert now that REST calls are formatting token list keys as string
                token_key = positions[x, y]
                token_decode = token_key.decode('UTF-8')
                token = tokens.get(token_decode)
                color = ORANGE_COLOR
                shape = get_pentagon((x, y))
                if token is not None:
                    if acted.count(token_decode) > 0:
                        color = ORANGE_COLOR
                    elif token[board.SIDE] == board.RED:
                        color = RED_COLOR
                    elif token[board.SIDE] == board.BLUE:
                        color = BLUE_COLOR
                    if token[board.TYPE] == board.SOLDIER:
                        shape = get_triangle((x, y))
                    elif token[board.TYPE] == board.TANK:
                        shape = get_square((x, y))
                    # we're only remembering contact rects for the hexes of the map
                    # tokens are non-interactive so disregard return value
                    # add a green outline for token health
                    pg.draw.polygon(token_surface, color, shape)

                    # outline thickness to represent health
                    health = token.get(board.HP)
                    if health is not None and health > 0:
                        pg.draw.polygon(token_surface, GREEN_COLOR, shape, health)


def draw_overlay(coordinates):
    # fill the screen with a slight tint and punch hexagons in it corresponding to a unit's turn options
    overlay_surface.fill((0, 0, 0, 32))
    action_coordinates = restclient.get_actions(coordinates)
    for x in range(board.X_MAX):
        for y in range(board.Y_MAX):
            # use our newly refactored "can my token do something here" function
            if action_coordinates.count(board.make_coord_num((x, y))) > 0:
                pg.draw.polygon(overlay_surface, (0, 0, 0, 0), get_hexagon((x, y)))


def draw_to_screen():
    pg.display.flip()
    screen.blit(background, (0, 0))
    screen.blit(text_surface, (0, 0))
    screen.blit(token_surface, (0, 0))


def play_loop():
    clock = pg.time.Clock()
    pg.display.set_caption("hexbattle")
    token_tile = None
    action_tile = None
    win = None
    state = SELECT
    controls = {}

    # get all of our initial state
    terrain = restclient.get_terrain()
    positions = restclient.get_positions()
    tokens = restclient.get_units()
    acted = restclient.get_acted()
    turn = restclient.get_turn()

    tiles = draw_board(terrain)
    draw_state_text(win, state)
    draw_tokens(positions, tokens, acted)

    if pg.font:
        restart = small_font.render(RESTART, True, (32, 32, 32))
        restart_pos = restart.get_rect(centerx=3 * background.get_width() / 4, centery=64+(background.get_height() / 4))
        controls[tuple(restart_pos)] = RESTART
        background.blit(restart, restart_pos)

    running = True
    while running:
        if pg.font:
            end_turn_color = (32, 32, 32)
            if turn == board.RED:
                end_turn_color = RED_COLOR
            elif turn == board.BLUE:
                end_turn_color = BLUE_COLOR
            end_turn_text = font.render(END, True, end_turn_color)
            end_turn_pos = end_turn_text.get_rect(centerx=background.get_width() * 3 / 4,
                                                  centery=background.get_height() * 2 / 3)
            controls[tuple(end_turn_pos)] = END
            background.blit(end_turn_text, end_turn_pos)

        clock.tick(60)
        for event in pg.event.get():
            if event.type == pg.MOUSEBUTTONDOWN:
                tile_clicked = pg.Rect(pg.mouse.get_pos(), (1, 1)).collidedict(tiles)
                control_clicked = pg.Rect(pg.mouse.get_pos(), (1, 1)).collidedict(controls)
                if control_clicked is not None:
                    if control_clicked[1] == END:
                        state = SELECT
                        turn = restclient.post_turn(turn)
                        win = restclient.get_victory()
                        acted = restclient.get_acted()
                        draw_tokens(positions, tokens, acted)
                    elif control_clicked[1] == RESTART:
                        state = SELECT
                        draw_state_text(win, state)
                        restclient.init_board()
                        turn = restclient.get_turn()
                        positions = restclient.get_positions()
                        acted = restclient.get_acted()
                        tokens = restclient.get_units()
                        draw_tokens(positions, tokens, acted)
                if tile_clicked is None:
                    state = SELECT
                    token_tile = None
                    action_tile = None
                if token_tile is not None:
                    # this is where we confirm where the piece we've picked is supposed to go or attack
                    state = SELECT
                    action_tile = tile_clicked
                    token_xy = token_tile[1]
                    action_xy = action_tile[1]
                    # use the refactored "do the thing" method here
                    positions = restclient.post_position(list(token_xy), list(action_xy))
                    tokens = restclient.get_units()
                    acted = restclient.get_acted()
                    draw_tokens(positions, tokens, acted)
                    token_tile = None
                    action_tile = None
                    token_xy = None
                    action_xy = None
                else:
                    # this is where we pick up a piece
                    if tile_clicked is not None:
                        state = CONFIRM
                    token_tile = tile_clicked
                    if token_tile is not None:
                        token_xy = token_tile[1]
                        token_unit_key = positions[token_xy[board.COL], token_xy[board.ROW]]
                        token_unit = tokens.get(token_unit_key.decode('UTF-8'))
                        if token_unit is not None:
                            draw_overlay(token_xy)
                # every click

            # every event
            if event.type == pg.QUIT:
                running = False
            draw_state_text(win, state)

        # every frame
        draw_to_screen()
        if state == CONFIRM:
            screen.blit(overlay_surface, (0, 0))
    # exit game to session launcher
    clear()


if __name__ == '__main__':
    play_loop()
    pg.quit()

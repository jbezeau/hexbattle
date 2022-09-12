import pygame as pg
import pygame.display

import board

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


def get_scaled_coordinates(coordinates):
    hx = 8 * coordinates[board.COL] * SCALE + ORIGIN[board.COL]
    hy = 4 * coordinates[board.ROW] * SCALE + ORIGIN[board.ROW]
    return [hx, hy]


def get_elevation_color(coordinates):
    elevation = b.terrain[coordinates[board.COL], coordinates[board.ROW]]
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


def draw_board():
    new_tiles = {}
    for x in range(board.X_MAX):
        for y in range(board.Y_MAX):
            if board.check_pos((x, y)):
                tile = pg.draw.polygon(background, get_elevation_color((x, y)), get_hexagon((x, y)))
                pg.draw.polygon(background, BG_COLOR, get_hexagon((x, y)), 4)
                new_tiles[tuple(tile)] = (x, y)
    return new_tiles


def draw_state_text():
    text_surface.fill((0, 0, 0))
    if pg.font:
        text = font.render(state, True, (32, 32, 32))
        text_pos = text.get_rect(centerx=background.get_width() * 3 / 4, y=10)
        text_surface.blit(text, text_pos)


def draw_tokens():
    token_surface.fill((0, 0, 0))
    for x in range(board.X_MAX):
        for y in range(board.Y_MAX):
            if board.check_pos((x, y)):
                token_key = b.positions[x, y]
                token = b.tokens.get(token_key)
                health = 0
                color = ORANGE_COLOR
                shape = get_pentagon((x, y))
                if token is not None:
                    if b.acted.count(token_key) > 0:
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
    for x in range(board.X_MAX):
        for y in range(board.Y_MAX):
            # use our newly refactored "can my token do something here" function
            if b.check_action(coordinates, (x, y)):
                pg.draw.polygon(overlay_surface, (0, 0, 0, 0), get_hexagon((x, y)))


def init_board():
    new_b = board.Board()
    return new_b


if __name__ == '__main__':
    pg.init()
    screen = pg.display.set_mode((1280, 480), pg.SCALED)
    pg.display.set_caption("hexbattle")
    pg.mouse.set_visible(True)
    if pg.font:
        font = pg.font.Font(None, 64)
        smallfont = pg.font.Font(None, 32)

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

    token_tile = None
    action_tile = None
    state = SELECT
    draw_state_text()

    b = init_board()
    tiles = draw_board()
    controls = {}
    clock = pg.time.Clock()
    draw_tokens()
    screen.blit(token_surface, (0, 0))

    if pg.font:
        restart = smallfont.render(RESTART, True, (32, 32, 32))
        restart_pos = restart.get_rect(centerx=background.get_width() * 3 / 4, y=96)
        controls[tuple(restart_pos)] = RESTART
        background.blit(restart, restart_pos)

    running = True
    while running:
        if pg.font:
            end_turn_color = (32, 32, 32)
            if b.turn == board.RED:
                end_turn_color = RED_COLOR
            elif b.turn == board.BLUE:
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
                        draw_state_text()
                        b.finish_turn()
                        draw_tokens()
                    elif control_clicked[1] == RESTART:
                        state = SELECT
                        draw_state_text()
                        b = init_board()
                        draw_tokens()
                        screen.blit(token_surface, (0, 0))
                if tile_clicked is None:
                    state = SELECT
                    draw_state_text()
                    token_tile = None
                    action_tile = None
                if token_tile is not None:
                    # this is where we confirm where the piece we've picked is supposed to go or attack
                    state = SELECT
                    draw_state_text()
                    action_tile = tile_clicked
                    token_xy = token_tile[1]
                    action_xy = action_tile[1]
                    # use the refactored "do the thing" method here
                    b.resolve_action(token_xy, action_xy)
                    draw_tokens()
                    token_tile = None
                    action_tile = None
                    token_xy = None
                    action_xy = None
                else:
                    # this is where we pick up a piece
                    if tile_clicked is not None:
                        state = CONFIRM
                        draw_state_text()
                    token_tile = tile_clicked
                    if token_tile is not None:
                        token_xy = token_tile[1]
                        token_unit_key = b.positions[token_xy[board.COL], token_xy[board.ROW]]
                        token_unit = b.tokens.get(token_unit_key)
                        if token_unit is not None:
                            draw_overlay(token_xy)

            win = b.check_victory()
            if win is not None:
                state = VICTORY
                draw_state_text()

            if event.type == pg.QUIT:
                running = False
        pygame.display.flip()
        screen.blit(background, (0, 0))
        screen.blit(text_surface, (0, 0))
        screen.blit(token_surface, (0, 0))
        if state == CONFIRM:
            screen.blit(overlay_surface, (0, 0))
    pg.quit()

import pygame as pg
import pygame.display

import board

BG_COLOR = (64, 64, 64)
BLUE_COLOR = (32, 32, 170)
RED_COLOR = (170, 32, 32)
ORANGE_COLOR = (170, 85, 42)

SCALE = 8
ORIGIN = [64, 64]

SELECT = 'Select Unit'
CONFIRM = 'Confirm Order'
VICTORY = 'Victory'

END = 'End Turn'


def get_scaled_coordinates(coordinates):
    hx = 8 * coordinates[board.COL] * SCALE + ORIGIN[board.COL]
    hy = 4 * coordinates[board.ROW] * SCALE + ORIGIN[board.ROW]
    return [hx, hy]


def get_hexcolor(coordinates):
    elevation = b.terrain[coordinates[board.COL], coordinates[board.ROW]]
    greyscale = min(255, 32*elevation + 128)
    grey_tuple = (greyscale, greyscale, greyscale)
    return grey_tuple


def get_triangle(coordinates):
    pt = get_scaled_coordinates(coordinates)
    tx = pt[board.COL]
    ty = pt[board.ROW]
    return [(tx, ty-SCALE), (tx+SCALE, ty+SCALE), (tx-SCALE, ty+SCALE)]


def get_square(coordinates):
    pt = get_scaled_coordinates(coordinates)
    tx = pt[board.COL]
    ty = pt[board.ROW]
    return [(tx+SCALE, ty-SCALE), (tx+SCALE, ty+SCALE), (tx-SCALE, ty+SCALE), (tx-SCALE, ty-SCALE)]


def get_pentagon(coordinates):
    pt = get_scaled_coordinates(coordinates)
    tx = pt[board.COL]
    ty = pt[board.ROW]
    return [(tx, ty-SCALE), (tx+SCALE, ty-SCALE/4), (tx+3*SCALE/4, ty+SCALE), (tx-3*SCALE/4, ty+SCALE), (tx-SCALE, ty-SCALE/4)]


def get_hexagon(coordinates):
    pt = get_scaled_coordinates(coordinates)
    hx = pt[board.COL]
    hy = pt[board.ROW]
    return [(hx-5*SCALE, hy), (hx-3*SCALE, hy-4*SCALE), (hx+3*SCALE, hy-4*SCALE),
            (hx+5*SCALE, hy), (hx+3*SCALE, hy+4*SCALE), (hx-3*SCALE, hy+4*SCALE)]


def draw_board():
    new_tiles = {}
    for x in range(board.X_MAX):
        for y in range(board.Y_MAX):
            if board.check_pos([x, y]):
                tile = pg.draw.polygon(background, get_hexcolor([x, y]), get_hexagon([x, y]))
                pg.draw.polygon(background, BG_COLOR, get_hexagon([x, y]), 4)
                new_tiles[tuple(tile)] = (x, y)
    return new_tiles


def draw_tokens():
    token_surface.fill((0, 0, 0))
    if pg.font:
        text = font.render(state, True, (32, 32, 32))
        text_pos = text.get_rect(centerx=background.get_width() * 3 / 4, y=10)
        token_surface.blit(text, text_pos)

    for x in range(board.X_MAX):
        for y in range(board.Y_MAX):
            if board.check_pos([x, y]):
                token_key = b.positions[x, y]
                token = b.tokens.get(token_key)
                color = ORANGE_COLOR
                shape = get_pentagon([x, y])
                if token is not None:
                    if b.acted.count(token_key) > 0:
                        color = ORANGE_COLOR
                    elif token[board.SIDE] == board.RED:
                        color = RED_COLOR
                    elif token[board.SIDE] == board.BLUE:
                        color = BLUE_COLOR
                    if token[board.TYPE] == board.SOLDIER:
                        shape = get_triangle([x, y])
                    elif token[board.TYPE] == board.TANK:
                        shape = get_square([x, y])
                    # we're only remembering contact rects for the hexes of the map
                    # tokens are non-interactive
                    t_rect = pg.draw.polygon(token_surface, color, shape)


def init_board():
    new_b = board.Board()
    return new_b


if __name__ == '__main__':
    pg.init()
    screen = pg.display.set_mode((1280, 480), pg.SCALED)
    pg.display.set_caption("hexbattle")
    pg.mouse.set_visible(True)

    background = pg.Surface(screen.get_size())
    background = background.convert()
    background.fill((64, 64, 64))

    token_surface = pg.Surface(screen.get_size())
    token_surface = token_surface.convert()
    token_surface.fill((0, 0, 0))
    token_surface.set_colorkey((0, 0, 0))

    token_tile = None
    action_tile = None
    state = SELECT

    b = init_board()
    tiles = draw_board()
    controls = {}
    clock = pg.time.Clock()

    running = True
    while running:
        if pg.font:
            font = pg.font.Font(None, 64)
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
                        b.finish_turn()
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
                    b.check_action(token_xy, action_xy)
                    token_tile = None
                    action_tile = None
                else:
                    # this is where we pick up a piece
                    if tile_clicked is not None:
                        state = CONFIRM
                    token_tile = tile_clicked

            win = b.check_victory()
            if win is not None:
                state = VICTORY

            if event.type == pg.QUIT:
                running = False
        pygame.display.flip()
        draw_tokens()
        screen.blit(background, (0, 0))
        screen.blit(token_surface, (0, 0))
    pg.quit()

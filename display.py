import pygame as pg
import pygame.display

import board

BG_COLOR = (64, 64, 64)
BLUE_COLOR = (32, 32, 170)
RED_COLOR = (170, 32, 32)

SCALE = 8
ORIGIN = [64, 64]


def get_scaled_coordinates(coordinates):
    hx = 8 * coordinates[board.COL] * SCALE + ORIGIN[board.COL]
    hy = 4 * coordinates[board.ROW] * SCALE + ORIGIN[board.ROW]
    return [hx, hy]


def get_hexcolor(coordinates):
    elevation = b.terrain[coordinates[board.COL], coordinates[board.ROW]]
    greyscale = min(255, 32*elevation + 128)
    grey_tuple = (greyscale, greyscale, greyscale)
    return grey_tuple


def get_hexagon(coordinates):
    pt = get_scaled_coordinates(coordinates)
    hx = pt[board.COL]
    hy = pt[board.ROW]
    return [(hx-5*SCALE, hy), (hx-3*SCALE, hy-4*SCALE), (hx+3*SCALE, hy-4*SCALE),
            (hx+5*SCALE, hy), (hx+3*SCALE, hy+4*SCALE), (hx-3*SCALE, hy+4*SCALE)]


def get_triangle(coordinates):
    pt = get_scaled_coordinates(coordinates)
    tx = pt[board.COL]
    ty = pt[board.ROW]
    return [(tx, ty-SCALE), (tx+SCALE, ty+SCALE), (tx-SCALE, ty+SCALE)]


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
    for x in range(board.X_MAX):
        for y in range(board.Y_MAX):
            if board.check_pos([x, y]):
                token_key = b.positions[x, y]
                token = b.tokens.get(token_key)
                if token is not None:
                    if token[board.SIDE] == board.RED:
                        rt = pg.draw.polygon(token_surface, RED_COLOR, get_triangle([x, y]))
                    elif token[board.SIDE] == board.BLUE:
                        bt = pg.draw.polygon(token_surface, BLUE_COLOR, get_triangle([x, y]))


def init_board():
    board.X_MAX = 11
    board.Y_MAX = 11
    new_b = board.Board()
    new_b.terrain[2, 2] = 4
    new_b.terrain[3, 3] = 3
    new_b.terrain[2, 4] = 2
    new_b.positions[1, 1] = 'RF'
    new_b.position[9, 9] = 'BF'
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

    b = init_board()
    tiles = draw_board()

    if pg.font:
        font = pg.font.Font(None, 64)
        text = font.render("text", True, (10, 10, 10))
        textpos = text.get_rect(centerx=background.get_width() / 2, y=10)
        background.blit(text, textpos)

    clock = pg.time.Clock()
    screen.blit(background, (0, 0))

    running = True
    while running:
        clock.tick(60)
        for event in pg.event.get():
            if event.type == pg.MOUSEBUTTONDOWN:
                tile_clicked = pg.Rect(pg.mouse.get_pos(), (1, 1)).collidedict(tiles)
                if tile_clicked is None:
                    token_tile = None
                    action_tile = None
                if token_tile is not None:
                    # this is where we confirm where the piece we've picked is supposed to go or attack
                    action_tile = tile_clicked
                    b.check_action(token_tile, action_tile)
                    token_tile = None
                    action_tile = None
                else:
                    # this is where we pick up a piece
                    token_tile = tile_clicked

            if event.type == pg.QUIT:
                running = False
        pygame.display.flip()
        draw_tokens()
        screen.blit(token_surface, (0, 0))
    pg.quit()

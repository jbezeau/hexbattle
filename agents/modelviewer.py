import pygame
import numpy
import json
from server import board

TILE_SIZE = 8
TILE_SPACING = 4
TEXT_COLOR = (192, 192, 192)

# global state for display
pygame.init()
screen = pygame.display.set_mode((1280, 640), pygame.SCALED)
pygame.mouse.set_visible(True)

background = pygame.Surface(screen.get_size())
background = background.convert()
background.fill((64, 64, 64))

list_surface = pygame.Surface(screen.get_size())
list_surface = list_surface.convert()
list_surface.fill((0, 0, 0))
list_surface.set_colorkey((0, 0, 0))

text_surface = pygame.Surface(screen.get_size())
text_surface = text_surface.convert()
text_surface.fill((0, 0, 0))
text_surface.set_colorkey((0, 0, 0))

large_font = pygame.font.Font(None, 64)
small_font = pygame.font.Font(None, 32)
smaller_font = pygame.font.Font(None, 16)


def model_list_select(b):
    title_text = large_font.render("Select Model", True, TEXT_COLOR)
    list_surface.blit(title_text, (12, 12))
    rows = b.list_models()
    new_selectable = {}
    for i, row in enumerate(rows):
        row_id = str(row[0])
        control_text = small_font.render(row_id, True, TEXT_COLOR)
        control_pos = control_text.get_rect(centerx=screen.get_width() * 1//5,
                                            centery=(i * 40) + screen.get_height() * 1//8)
        control_x = screen.get_width() * 0//5
        control_w = screen.get_width() * 2//5
        control_y = control_pos.top
        control_b = control_pos.bottom
        highlight = pygame.Rect(control_x, control_y, control_w, control_b - control_y)
        new_selectable[tuple(highlight)] = row_id
        list_surface.fill((128, 128, 128), highlight)
        list_surface.blit(control_text, control_pos)
    return new_selectable


def draw_config_text(config_json):
    # text area for model under list
    config_dict = json.loads(config_json)
    config_layers = config_dict.get('config').get('layers')
    i = 0
    for c in config_layers:
        c_config = c.get('config')
        config_text = small_font.render(c_config.get('name'), True, TEXT_COLOR)
        text_surface.blit(config_text, (24, i + screen.get_height() * 3//5))
        i += 24


def draw_layer_dims(sizes):
    i = 0
    for layer_size in sizes:
        weight_text = small_font.render(str(layer_size), True, TEXT_COLOR)
        text_surface.blit(weight_text, (screen.get_width() * 1//5, i + screen.get_height() * 3 // 5))
        i += 24


def draw_model_details(weights, mouse_over):
    layer_sizes = []
    layer_weights = []
    input_size = numpy.array(weights[0]).shape[0]
    layer_sizes.append(input_size)
    for a in weights:
        npa = numpy.array(a)
        if len(npa.shape) == 1:
            layer_size = npa.shape[0]
            layer_sizes.append(layer_size)
        elif len(npa.shape) == 2:
            layer_weights.append(npa)

    draw_layer_dims(layer_sizes)

    # interaction of layer_sizes and layer_weights
    # draw nodes indexed by position in layer_sizes array
    # mouse selects node indexed by position in layer_sizes array
    # determine colors for layer_sizes[i] if mouse_i selects the layer above or below
    # mouse selects layer[0], draw layer[1] with colors from layer_weights[0][mouse_j, 0:]
    # mouse selects layer[2], draw layer[1] with colors from layer_weights[1][0:, mouse_j]
    # layer_sizes[0] = 440
    # layer_weights[0] = [440, 176]
    # layer_sizes[1] = 176
    # layer_weights[1] = [176, 88]
    # layer_sizes[2] = 88
    if mouse_over:
        mouse_i, mouse_j = mouse_over
    else:
        # set values out of range
        mouse_i = -99
        mouse_j = 0
    tiles = {}
    for i in range(len(layer_sizes)):
        # reset start of tile for every layer
        x = screen.get_width() * 2//5 + TILE_SIZE + TILE_SPACING
        y = screen.get_height() * i//len(layer_sizes) + TILE_SIZE + TILE_SPACING
        for j in range(layer_sizes[i]):
            tile = pygame.Rect((x, y), (TILE_SIZE, TILE_SIZE))
            if mouse_i == i+1:
                # we are drawing the inputs to the node the mouse has selected
                active_color = get_tile_color(layer_weights[i][j, mouse_j])
            elif mouse_i == i-1:
                # we are drawing the outputs from the node the mouse has selected
                active_color = get_tile_color(layer_weights[i-1][mouse_j, j])
            elif mouse_i == i and mouse_j == j:
                active_color = (255, 255, 255)
            else:
                active_color = (128, 128, 128)

            pygame.draw.rect(background, active_color, tile)
            tiles[tuple(tile)] = (i, j)
            x += TILE_SIZE + TILE_SPACING
            if x > screen.get_width() - TILE_SIZE:
                x = screen.get_width() * 2//5 + TILE_SIZE + TILE_SPACING
                y += TILE_SIZE + TILE_SPACING
    return tiles


def get_tile_color(val):
    # expect val in range from -1 to 1
    r, g, b = (0, 0, 0)
    if val < 0:
        r = min(255, -128 * (val - 1))
    elif val > 0:
        b = min(255,  128 * (1 + val))
    return r, g, b


def draw_to_screen():
    pygame.display.flip()
    screen.blit(background, (0, 0))
    screen.blit(text_surface, (0, 0))
    screen.blit(list_surface, (0, 0))


def main_loop(b):
    clock = pygame.time.Clock()
    pygame.display.set_caption("model viewer")
    model_list = model_list_select(b)
    tile_list = {}
    mouse_tile = None
    weights = None

    loop = True
    while loop:
        clock.tick(60)
        for event in pygame.event.get():
            if event.type == pygame.MOUSEBUTTONDOWN:
                model_clicked = pygame.Rect(pygame.mouse.get_pos(), (1, 1)).collidedict(model_list)
                if model_clicked is not None:
                    layers, weights = b.load_model(model_clicked[1])
                    text_surface.fill((0, 0, 0))
                    background.fill((64, 64, 64))
                    mouse_tile = None
                    draw_config_text(layers)
            if event.type == pygame.QUIT:
                loop = False
        new_mouse_over = pygame.Rect(pygame.mouse.get_pos(), (1, 1)).collidedict(tile_list)
        if new_mouse_over is not None:
            # mouse over is ((rect), (node index)) and we just want the index
            mouse_tile = new_mouse_over[1]
        if weights:
            tile_list = draw_model_details(weights, mouse_tile)
        draw_to_screen()


if __name__ == '__main__':
    game_board = board.Board()
    main_loop(game_board)
    pygame.quit()

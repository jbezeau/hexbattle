import pygame as pg

import board
import display
import restclient


class EditControls:
    TERRAIN_EDIT = 'Edit Terrain'
    TERRAIN_RAISE = 'Raise'
    TERRAIN_LOWER = 'Lower'
    UNIT_PLACE = 'Place Unit'
    UNIT_FLAG = 'Flag'
    UNIT_TANK = 'Tank'
    UNIT_SOLDIER = 'Soldier'
    UNIT_CLEAR = 'Remove'
    UNIT_COLOR = 'Token Color'
    DONE = 'Finished Editing'
    SAVE = 'Save Map'
    RESET = 'Reset Board'
    MENU_MAIN = [TERRAIN_EDIT, UNIT_PLACE, DONE]
    MENU_TERRAIN = [TERRAIN_RAISE, TERRAIN_LOWER]
    MENU_UNIT = [UNIT_SOLDIER, UNIT_TANK, UNIT_FLAG, UNIT_CLEAR, UNIT_COLOR]
    MENU_DONE = [SAVE, RESET]
    COLOR_LIST = [board.RED, board.BLUE]


def edit_loop():
    clock = pg.time.Clock()
    pg.display.set_caption("hexbattle editor")
    menu = EditControls.MENU_MAIN
    unit_color = board.RED
    action = EditControls.TERRAIN_RAISE

    # get all of our initial state
    terrain = restclient.get_terrain()
    positions = restclient.get_positions()
    tokens = restclient.get_units()

    controls = draw_controls(menu, unit_color)
    tiles = display.draw_board(terrain)
    display.draw_tokens(positions, tokens)

    running = True
    while running:

        clock.tick(60)
        for event in pg.event.get():
            if event.type == pg.MOUSEBUTTONDOWN:
                tile_clicked = pg.Rect(pg.mouse.get_pos(), (1, 1)).collidedict(tiles)
                control_clicked = pg.Rect(pg.mouse.get_pos(), (1, 1)).collidedict(controls)
                if control_clicked is not None:
                    control_id = control_clicked[1]
                    match control_id:
                        case EditControls.TERRAIN_EDIT:
                            menu = EditControls.MENU_TERRAIN
                        case EditControls.TERRAIN_RAISE:
                            action = EditControls.TERRAIN_RAISE
                        case EditControls.TERRAIN_LOWER:
                            action = EditControls.TERRAIN_LOWER

                        case EditControls.UNIT_PLACE:
                            menu = EditControls.MENU_UNIT
                        case EditControls.UNIT_TANK:
                            action = EditControls.UNIT_TANK
                        case EditControls.UNIT_SOLDIER:
                            action = EditControls.UNIT_SOLDIER
                        case EditControls.UNIT_FLAG:
                            action = EditControls.UNIT_FLAG
                        case EditControls.UNIT_COLOR:
                            # use same logic as rotating through player turns
                            unit_color = board.next_color(unit_color)

                        case EditControls.DONE:
                            menu = EditControls.MENU_DONE
                        case EditControls.SAVE:
                            terrain = restclient.save_terrain(terrain)
                            positions = restclient.save_positions(positions)
                            tokens = restclient.save_status(tokens)
                            display.draw_board(terrain)
                            display.draw_tokens(positions, tokens)
                            restclient.save_commit()
                        case EditControls.RESET:
                            restclient.init_board()
                            terrain = restclient.get_terrain()
                            positions = restclient.get_positions()
                            tokens = restclient.get_units()
                            display.draw_board(terrain)
                            display.draw_tokens(positions, tokens)
                        case _:
                            menu = EditControls.MENU_MAIN
                    controls = draw_controls(menu, unit_color)

                elif tile_clicked is not None:
                    x, y = tile_clicked[1]
                    match action:
                        case EditControls.TERRAIN_RAISE:
                            terrain[x, y] += 1
                            display.draw_board(terrain)
                        case EditControls.TERRAIN_LOWER:
                            terrain[x, y] -= 1
                            display.draw_board(terrain)
                        case EditControls.UNIT_TANK | EditControls.UNIT_SOLDIER | EditControls.UNIT_FLAG:
                            # need to generate a new token in the status roster and assign that ID to positions board
                            positions[x, y] = new_unit(tokens, unit_color, action)
                            display.draw_tokens(positions, tokens)

                else:
                    menu = EditControls.MENU_MAIN
                    controls = draw_controls(menu, unit_color)

            # every event
            if event.type == pg.QUIT:
                running = False
        # every frame
        display.draw_to_screen()
    # clean up
    display.clear()


def new_unit(tokens, unit_color, action):
    # add a new unit determined by action and unit_color variables to the status list
    # return the generated unit id value for placement on the position map
    if unit_color == board.RED:
        unit_id = 'R'
    elif unit_color == board.BLUE:
        unit_id = 'B'

    # copy stat block from unit type
    # tokens all start off red, and then we override
    unit_stat = None
    match action:
        case EditControls.UNIT_FLAG:
            unit_id += 'F'
            unit_stat = board.RED_FLAG.copy()
        case EditControls.UNIT_TANK:
            unit_id += 'T'
            unit_stat = board.RED_TANK.copy()
        case EditControls.UNIT_SOLDIER:
            unit_stat = board.RED_SOLDIER.copy()
    unit_stat[board.SIDE] = unit_color

    # get a unit number by counting same type and side, important for keeping ID numbers out of double-digits
    id_num = 1
    for token_id, token_unit in tokens.items():
        if token_unit[board.TYPE] == unit_stat[board.TYPE] \
                and token_unit[board.SIDE] == unit_stat[board.SIDE]:
            id_num += 1
    # TODO error condition when total ID length > 3
    unit_id += str(id_num)

    # add token to the status list
    tokens[unit_id] = unit_stat

    # return id for use on position board
    # ids in position board are char(3)
    return unit_id.encode('UTF-8')


def draw_controls(control_set, unit_color):
    # draw text and return dict of { control hit box: control function, ... } to calling context
    new_controls = {}
    display.text_surface.fill((0, 0, 0))
    if pg.font:
        for i, ctrl in enumerate(control_set):
            text_color = (40, 40, 40)
            if ctrl in [EditControls.UNIT_TANK, EditControls.UNIT_SOLDIER, EditControls.UNIT_FLAG]:
                if unit_color == board.RED:
                    text_color = display.RED_COLOR
                elif unit_color == board.BLUE:
                    text_color = display.BLUE_COLOR
            control_text = display.font.render(ctrl, True, text_color)
            control_pos = control_text.get_rect(centerx=display.text_surface.get_width() * 4 / 5,
                                                centery=(i*80) + (display.text_surface.get_height() * 1 / 8))
            new_controls[tuple(control_pos)] = ctrl
            display.text_surface.blit(control_text, control_pos)
    return new_controls


if __name__ == '__main__':
    edit_loop()
    pg.quit()

import pygame as pg

import board
import display
import editclient


class EditControls:
    TERRAIN_EDIT = 'Edit Terrain'
    TERRAIN_RAISE = 'Raise'
    TERRAIN_LOWER = 'Lower'
    UNIT_PLACE = 'Place Unit'
    UNIT_FLAG = 'Flag'
    UNIT_TANK = 'Tank'
    UNIT_SOLDIER = 'Soldier'
    UNIT_CLEAR = 'Remove'
    UNIT_COLOR = 'Unit Color'
    UNIT_COLOR_RED = 'Red'
    UNIT_COLOR_BLUE = 'Blue'
    DONE = 'Finished Editing'
    SAVE = 'Save Map'
    RESET = 'Reset Board'
    MENU_MAIN = [TERRAIN_EDIT, UNIT_PLACE, DONE]
    MENU_TERRAIN = [TERRAIN_RAISE, TERRAIN_LOWER]
    MENU_UNIT = [UNIT_SOLDIER, UNIT_TANK, UNIT_FLAG, UNIT_CLEAR, UNIT_COLOR]
    MENU_UNIT_COLOR = [UNIT_COLOR_RED, UNIT_COLOR_BLUE]
    MENU_DONE = [SAVE, RESET]


def new_unit():
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
    for token_id, token_unit in display.tokens.items():
        if token_unit[board.TYPE] == unit_stat[board.TYPE] \
                and token_unit[board.SIDE] == unit_stat[board.SIDE]:
            id_num += 1
    # TODO error condition when total ID length > 3
    unit_id += str(id_num)

    # add token to the status list
    display.tokens[unit_id] = unit_stat

    # return id for use on position board
    # ids in position board are char(3)
    return unit_id.encode('UTF-8')


def draw_controls(control_set):
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
    pg.display.set_caption("hexbattle editor")
    pg.mouse.set_visible(True)

    clock = pg.time.Clock()
    menu = EditControls.MENU_MAIN
    controls = draw_controls(menu)
    tiles = display.draw_board()
    display.draw_tokens()

    unit_color = board.RED
    action = EditControls.TERRAIN_RAISE

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
                            menu = EditControls.MENU_UNIT_COLOR
                        case EditControls.UNIT_COLOR_RED:
                            unit_color = board.RED
                            menu = EditControls.MENU_UNIT
                        case EditControls.UNIT_COLOR_BLUE:
                            unit_color = board.BLUE
                            menu = EditControls.MENU_UNIT

                        case EditControls.DONE:
                            menu = EditControls.MENU_DONE
                        case EditControls.SAVE:
                            terrain = editclient.save_terrain(display.terrain)
                            editclient.save_status(display.tokens)
                            editclient.save_positions(display.positions)
                        case EditControls.RESET:
                            editclient.init_board()
                            display.terrain = editclient.get_terrain()
                            display.positions = editclient.get_positions()
                            display.tokens = editclient.get_units()
                            display.draw_tokens()
                            display.draw_board()
                        case _:
                            menu = EditControls.MENU_MAIN
                    controls = draw_controls(menu)

                elif tile_clicked is not None:
                    x, y = tile_clicked[1]
                    match action:
                        case EditControls.TERRAIN_RAISE:
                            display.terrain[x, y] += 1
                            display.draw_board()
                        case EditControls.TERRAIN_LOWER:
                            display.terrain[x, y] -= 1
                            display.draw_board()
                        case EditControls.UNIT_TANK | EditControls.UNIT_SOLDIER | EditControls.UNIT_FLAG:
                            # need to generate a new token in the status roster and assign that ID to positions board
                            display.positions[x, y] = new_unit()
                            display.draw_tokens()

                else:
                    menu = EditControls.MENU_MAIN
                    controls = draw_controls(menu)

            # every event
            if event.type == pg.QUIT:
                running = False

        # every frame
        display.draw_to_screen()
    pg.quit()

import pygame as pg

import board
import display
import edit
import restclient


class SessionControls:
    PLAYER_ID = 'Enter Player ID'
    LIST = 'Session List'
    JOIN = 'Join Session'
    CONFIG = 'Scenario List'
    EDIT = 'Edit Scenario'
    START = 'Start'
    MENU_MAIN = [PLAYER_ID, LIST, CONFIG]
    MENU_SESSION = [LIST, JOIN]
    MENU_START = [CONFIG, EDIT, START]
    SELECT_SESSION = 'Session'
    SELECT_CONFIG = 'Scenario'


def draw_controls(control_set):
    # draw text and return dict of { control hit box: control function, ... } to calling context
    new_controls = {}
    display.text_surface.fill((0, 0, 0))
    if pg.font:
        for i, ctrl in enumerate(control_set):
            text_color = (40, 40, 40)
            control_text = display.font.render(ctrl, True, text_color)
            control_pos = control_text.get_rect(centerx=display.text_surface.get_width() * 1 / 5,
                                                centery=(i*80) + (display.text_surface.get_height() * 1 / 8))
            new_controls[tuple(control_pos)] = ctrl
            display.text_surface.blit(control_text, control_pos)
    return new_controls


def draw_id_input(text):
    if pg.font:
        text_color = (40, 40, 40)
        display.token_surface.fill((0, 0, 0))
        control_text = display.small_font.render(text, True, text_color)
        control_pos = control_text.get_rect(centerx=display.token_surface.get_width() * 3 / 5,
                                            centery=display.token_surface.get_height() * 1 / 8)
        control_left = display.token_surface.get_width() * 2 / 5
        control_top = control_pos.top
        control_bottom = control_pos.bottom
        highlight = pg.Rect(control_left, control_top, control_left, control_bottom-control_top)
        display.token_surface.fill((128, 128, 128), highlight)
        display.token_surface.blit(control_text, control_pos)


def draw_selections(rows):
    # draw a set of row data and return a dictionary of clickable areas with matching row_id
    new_selectable = {}
    if pg.font:
        text_color = (40, 40, 40)
        for i, row in enumerate(rows):
            row_id = str(row[0])
            control_text = display.small_font.render(row_id, True, text_color)
            control_pos = control_text.get_rect(centerx=display.token_surface.get_width() * 3 / 5,
                                                centery=(i * 40) + display.token_surface.get_height() * 1 / 8)
            control_left = display.token_surface.get_width() * 2 / 5
            control_top = control_pos.top
            control_bottom = control_pos.bottom
            highlight = pg.Rect(control_left, control_top, control_left, control_bottom - control_top)
            new_selectable[tuple(highlight)] = row_id
            display.token_surface.fill((128, 128, 128), highlight)
            display.token_surface.blit(control_text, control_pos)
    return new_selectable


if __name__ == '__main__':
    clock = pg.time.Clock()
    pg.display.set_caption("hexbattle launcher")
    pg.mouse.set_visible(True)
    menu = SessionControls.MENU_MAIN
    controls = draw_controls(menu)
    selectable = {}
    player_id = 'Player'
    typing = False

    running = True
    while running:

        clock.tick(60)
        for event in pg.event.get():
            if event.type == pg.MOUSEBUTTONDOWN:
                control_clicked = pg.Rect(pg.mouse.get_pos(), (1, 1)).collidedict(controls)
                selection_clicked = pg.Rect(pg.mouse.get_pos(), (1, 1)).collidedict(selectable)
                if control_clicked is not None:
                    control_id = control_clicked[1]
                    typing = False
                    display.token_surface.fill((0, 0, 0))
                    match control_id:
                        case SessionControls.PLAYER_ID:
                            typing = True
                            draw_id_input(player_id)
                        case SessionControls.LIST:
                            menu = SessionControls.MENU_SESSION
                            sessions = restclient.get_sessions(player_id)
                            if sessions:
                                selectable = draw_selections(sessions)
                        case SessionControls.JOIN:
                            restclient.join_session(player_id)
                        case SessionControls.CONFIG:
                            menu = SessionControls.MENU_START
                            configs = restclient.get_configs()
                            if configs:
                                selectable = draw_selections(configs)
                        case SessionControls.START:
                            restclient.start_session(player_id)
                            display.play_loop()
                        case SessionControls.EDIT:
                            edit.edit_loop()
                        case _:
                            menu = SessionControls.MENU_MAIN
                    controls = draw_controls(menu)
                elif selection_clicked is not None:
                    if menu == SessionControls.MENU_SESSION:
                        restclient.join_session(selection_clicked[1])
                        display.play_loop()
                    elif menu == SessionControls.MENU_START:
                        restclient.load_config(selection_clicked[1])
                else:
                    menu = SessionControls.MENU_MAIN
                    controls = draw_controls(menu)
            if typing and event.type == pg.KEYDOWN:
                # Check for backspace
                if event.key == pg.K_BACKSPACE:
                    # get text input from 0 to -1 i.e. end.
                    player_id = player_id[:-1]
                elif pg.K_z >= event.key >= pg.K_9:
                    # add unicode character
                    # bind to text chars and crop to 50
                    player_id += event.unicode
                    player_id = player_id[:50]
                draw_id_input(player_id)

            # every event
            if event.type == pg.QUIT:
                running = False

        # every frame
        display.draw_to_screen()
    pg.quit()

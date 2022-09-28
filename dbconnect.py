import mysql.connector
import board

USER = 'hexbattle'
PASS = 'h3xBATTLE'
HOST = '127.0.0.1'
DB = 'hexbattle'


def _connect():
    return mysql.connector.connect(user=USER, password=PASS, host=HOST, database=DB)


def save_board(terrain_json, positions_json, units_json):
    # allegedly MySQL closes connections after 5 minutes
    # edit sessions might take longer than that, so we need to surround operations with open/close
    cnx = _connect()
    cursor = cnx.cursor()
    sql = 'INSERT INTO game_config (terrain, positions, units) VALUES (%s, %s, %s)'
    binds = (terrain_json, positions_json, units_json)
    cursor.execute(sql, binds)
    board_id = cursor.lastrowid
    cursor.execute('COMMIT')
    cnx.close()
    return board_id


def load_board(config_id):
    cnx = _connect()
    cursor = cnx.cursor()
    sql = 'SELECT TERRAIN, POSITIONS, UNITS FROM game_config WHERE ID = %s'
    binds = (config_id,)
    cursor.execute(sql, binds)

    # there can be only one
    row = cursor.fetchone()
    if row is not None:
        return row
    cnx.close()
    return None


def delete_board(config_id):
    cnx = _connect()
    cursor = cnx.cursor()
    sql = 'DELETE FROM game_config WHERE ID=%s'
    cursor.execute(sql, (config_id,))
    cursor.execute("COMMIT")
    cnx.close()

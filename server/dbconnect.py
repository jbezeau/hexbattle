import mysql.connector
import mysql.connector.errors as err
import os

if 'RDS_HOSTNAME' in os.environ:
    DATABASES = {
        'default': {
            'NAME': os.environ['RDS_DB_NAME'],
            'USER': os.environ['RDS_USERNAME'],
            'PASSWORD': os.environ['RDS_PASSWORD'],
            'HOST': os.environ['RDS_HOSTNAME'],
            'PORT': os.environ['RDS_PORT'],
        }
    }
else:
    DATABASES = {
        'default': {
            'NAME': 'hexbattle',
            'USER': 'hexbattle',
            'PASSWORD': 'h3xBATTLE',
            'HOST': '127.0.0.1',
        }
    }


class DBConnection:
    # maintain a database connection, and re-open it whenever it times out
    # maintain a game session ID when playing, so we can post turns to the database
    def __init__(self):
        self._cnx = None
        self._session_id = None
        self.enable = True

    def _connect(self):
        try:
            if self._cnx is None or self._cnx.is_connected() is not True:
                user = DATABASES['default'].get('USER')
                password = DATABASES['default'].get('PASSWORD')
                host = DATABASES['default'].get('HOST')
                port = DATABASES['default'].get('PORT')
                name = DATABASES['default'].get('NAME')
                if port is not None:
                    self._cnx = mysql.connector.connect(
                        user=user, password=password, host=host, port=port, database=name)
                else:
                    self._cnx = mysql.connector.connect(
                        user=user, password=password, host=host, database=name)
                self.enable = True
        except err.DatabaseError:
            self._cnx = None
            self.enable = False
        return self._cnx

    def save_board(self, terrain_json, positions_json, units_json):
        # allegedly MySQL closes connections after 5 minutes
        # edit sessions might take longer than that, so we need to surround operations with open/close
        cnx = self._connect()
        cursor = cnx.cursor()
        sql = 'INSERT INTO game_config (terrain, positions, units) VALUES (%s, %s, %s)'
        binds = (terrain_json, positions_json, units_json)
        cursor.execute(sql, binds)
        board_id = cursor.lastrowid
        cursor.close()
        cnx.commit()
        return board_id

    def list_boards(self):
        cnx = self._connect()
        cursor = cnx.cursor()
        sql = 'SELECT ID FROM game_config'
        cursor.execute(sql)
        rows = cursor.fetchall()
        cursor.close()
        return rows

    def load_board(self, config_id):
        cnx = self._connect()
        # connect failure disables database functionality
        # game will revert to default board, no session, no turn saving
        if self.enable:
            cursor = cnx.cursor()
            sql = 'SELECT TERRAIN, POSITIONS, UNITS FROM game_config WHERE ID = %s'
            binds = (config_id,)
            cursor.execute(sql, binds)
    
            # there can be only one
            row = cursor.fetchone()
            cursor.close()
            if row is not None:
                return row
        return None

    def delete_board(self, config_id):
        cnx = self._connect()
        cursor = cnx.cursor()
        sql = 'DELETE FROM game_config WHERE ID=%s'
        binds = (config_id,)
        cursor.execute(sql, binds)
        cursor.close()
        cnx.commit()

    def create_session(self, config_id, player_id):
        # config is a number matching game_config.ID
        # player is some kind of string unique to the player
        cnx = self._connect()
        cursor = cnx.cursor()
        sql = 'INSERT INTO game_session (config_id, player_id, status) VALUES (%s, %s, %s)'
        binds = (config_id, player_id, 'OPEN')
        cursor.execute(sql, binds)
        self._session_id = cursor.lastrowid
        cursor.close()
        cnx.commit()
        return self._session_id

    def list_sessions(self, player_id=None):
        cnx = self._connect()
        cursor = cnx.cursor()
        if player_id is None:
            sql = "SELECT ID, player_id FROM game_session WHERE status = 'OPEN'"
            cursor.execute(sql)
        else:
            sql = "SELECT ID FROM game_session WHERE status = 'OPEN' AND player_id = %s"
            binds = (player_id,)
            cursor.execute(sql, binds)
        rows = cursor.fetchall()
        cursor.close()
        return rows

    def join_session(self, session_id):
        # choosing not to bake too much logic into this one function: if it doesn't join a session it returns None
        cnx = self._connect()
        cursor = cnx.cursor()
        sql = "SELECT config_id FROM game_session WHERE STATUS = 'OPEN' AND ID = %s"
        binds = (session_id,)
        cursor.execute(sql, binds)
        row = cursor.fetchone()
        config = None
        self._session_id = None
        if row is not None:
            self._session_id = row[0]
            config = row[1]
        cursor.close()
        return config

    def close_session(self):
        cnx = self._connect()
        cursor = cnx.cursor()
        sql = "UPDATE game_session SET status = 'CLOSED' WHERE ID = %s"
        binds = (self._session_id,)
        cursor.execute(sql, binds)
        cursor.close()
        cnx.commit()
        self._session_id = None

    def post_turn(self, actions, positions, status):
        # store the moves and final board state for every turn, so we can immediately pick up a session
        # or train the AI on before/after pairs without constructing entire games
        cnx = self._connect()
        cursor = cnx.cursor()
        sql = 'INSERT INTO game_turn (session_id, action, positions, status) VALUES (%s, %s, %s, %s)'
        binds = (self._session_id, actions, positions, status)
        cursor.execute(sql, binds)
        turn_id = cursor.lastrowid
        cursor.close()
        cnx.commit()
        return turn_id

    def save_model(self, model_json, weights_json, model_id=None):
        cnx = self._connect()
        cursor = cnx.cursor()
        if model_id:
            sql = 'UPDATE game_model SET model = %s, weights = %s WHERE ID = %s'
            binds = (model_json, weights_json, model_id)
        else:
            sql = 'INSERT INTO game_model (model, weights) values (%s, %s)'
            binds = (model_json, weights_json)
        cursor.execute(sql, binds)
        model_id = cursor.lastrowid
        cursor.close()
        cnx.commit()
        return model_id

    def list_models(self):
        cnx = self._connect()
        cursor = cnx.cursor()
        sql = "SELECT ID FROM game_model"
        binds = None
        cursor.execute(sql, binds)
        rows = cursor.fetchall()
        cursor.close()
        return rows

    def load_model(self, model_id):
        cnx = self._connect()
        cursor = cnx.cursor()
        sql = "SELECT model, weights FROM game_model WHERE ID = %s"
        binds = (model_id,)
        cursor.execute(sql, binds)
        row = cursor.fetchone()
        cursor.close()
        return row

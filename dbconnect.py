import mysql.connector


cnx = mysql.connector.connect(user='hexbattle', password='h3xBATTLE', host='127.0.0.1', database='hexbattle')
cnx.close()

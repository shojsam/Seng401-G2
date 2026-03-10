import mysql.connector
from mysql.connector import pooling, Error

db_config = {
    "host": "localhost",
    "user": "root",
    "password": "root",
    "database": "card_game_db"
}

try:
    # Renamed to db_pool for consistency across your models
    db_pool = mysql.connector.pooling.MySQLConnectionPool(
        pool_name="card_game_pool",
        pool_size=5,  #number of players per game 
        **db_config
    )
    print("Connection pool created successfully")
except Error as e:
    print(f"Error creating connection pool: {e}")

def get_connection():
    return db_pool.get_connection()

def execute_query(query, params=None, fetch=False):
    conn = get_connection()
    cursor = conn.cursor(dictionary=True) 
    try:
        cursor.execute(query, params or ())
        if fetch:
            return cursor.fetchall()
        conn.commit()
    except Error as e:
        print(f"Query Error: {e}")
        conn.rollback()
    finally:
        cursor.close()
        conn.close()
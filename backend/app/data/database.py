import mysql.connector
from mysql.connector import pooling, Error
import os

db_config = {
    "host": "localhost",
    "user": "root",
    "password": "root",
    "database": "card_game_db"
}

try:
    connection_pool = mysql.connector.pooling.MySQLConnectionPool(
        pool_name="card_game_pool",
        pool_size=5,
        **db_config
    )
    print("Connection pool created successfully")
except Error as e:
    print(f"Error creating connection pool: {e}")

def get_connection():
    return connection_pool.get_connection()

def execute_query(query, params=None, fetch=False):
    """Generic helper to execute SQL and handle connections."""
    conn = get_connection()
    cursor = conn.cursor(dictionary=True) # Returns results as dicts
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
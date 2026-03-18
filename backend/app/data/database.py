import os

import mysql.connector
from mysql.connector import Error, pooling
from dotenv import load_dotenv

load_dotenv()

db_pool = None


def _build_db_config():
    return {
        "host": os.getenv("MYSQLHOST", "localhost"),
        "port": int(os.getenv("MYSQLPORT", "3306")),
        "user": os.getenv("MYSQLUSER", "root"),
        "password": os.getenv("MYSQLPASSWORD", "root"),
        "database": os.getenv("MYSQLDATABASE", "card_game_db"),
    }


def _get_pool():
    global db_pool
    if db_pool is None:
        db_pool = pooling.MySQLConnectionPool(
            pool_name="card_game_pool",
            pool_size=5,
            **_build_db_config(),
        )
        print("Connection pool created successfully")
    return db_pool


def get_connection():
    return _get_pool().get_connection()


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

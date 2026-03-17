import os
from urllib.parse import urlparse

import mysql.connector
from mysql.connector import Error, pooling
from dotenv import load_dotenv

load_dotenv()

db_pool = None


def _build_db_config():
 database_url = os.getenv("DATABASE_URL")
 print(f"DEBUG: DATABASE_URL = {database_url}")  # Add this line
 if database_url:
    parsed = urlparse(database_url)
    print(f"DEBUG: Parsed host = {parsed.hostname}")  # Add this line
    return {
    "host": parsed.hostname or "localhost",
    "port": parsed.port or 3306,
    "user": parsed.username or "root",
    "password": parsed.password or "",
    "database": (parsed.path or "").lstrip("/") or "card_game_db",
    }
 return {
 "host": os.getenv("DB_HOST", "localhost"),
 "port": int(os.getenv("DB_PORT", "3306")),
 "user": os.getenv("DB_USER", "root"),
 "password": os.getenv("DB_PASSWORD", "root"),
 "database": os.getenv("DB_NAME", "card_game_db"),
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

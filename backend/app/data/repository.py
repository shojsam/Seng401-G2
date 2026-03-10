from .database import get_connection

def get_all_cards():
    conn = get_connection()
    cursor = conn.cursor(dictionary=True)
    try:
        cursor.execute("SELECT * FROM cards")
        return cursor.fetchall()
    finally:
        cursor.close()
        conn.close()

def create_user(username, password):
    conn = get_connection()
    cursor = conn.cursor()
    try:
        query = "INSERT INTO users (username, password) VALUES (%s, %s)"
        cursor.execute(query, (username, password))
        conn.commit()
    finally:
        cursor.close()
        conn.close()

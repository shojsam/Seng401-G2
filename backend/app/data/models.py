from database import db_pool 

def save_game_result(winner_name: str):
    connection = db_pool.get_connection()
    cursor = connection.cursor()
    try:
        query = "INSERT INTO game_results (winner) VALUES (%s)"
        cursor.execute(query, (winner_name,))
        connection.commit()
        print(f"Game result saved for {winner_name}")
    except Exception as e:
        print(f"Error saving game result: {e}")
        connection.rollback()
    finally:
        cursor.close()
        connection.close()

def get_recent_results(limit=10):
    """Fetches the latest game results."""
    connection = db_pool.get_connection()
    # Use dictionary=True so it looks like your old SQLAlchemy objects
    cursor = connection.cursor(dictionary=True) 
    
    try:
        query = "SELECT * FROM game_results ORDER BY played_at DESC LIMIT %s"
        cursor.execute(query, (limit,))
        return cursor.fetchall()
    finally:
        cursor.close()
        connection.close()

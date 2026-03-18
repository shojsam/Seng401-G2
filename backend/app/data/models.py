from .database import get_connection


def _table_exists(cursor, table_name: str) -> bool:
    cursor.execute("SHOW TABLES LIKE %s", (table_name,))
    return cursor.fetchone() is not None


def save_game_result(winner_name: str):
    connection = get_connection()
    cursor = connection.cursor()
    try:
        if _table_exists(cursor, "game_results"):
            cursor.execute(
                "INSERT INTO game_results (winner) VALUES (%s)",
                (winner_name,),
            )
        elif _table_exists(cursor, "games"):
            # Current schema stores completed games without a dedicated winner column.
            cursor.execute(
                "INSERT INTO games (status) VALUES (%s)",
                ("completed",),
            )
        else:
            raise RuntimeError("No compatible results table found")

        connection.commit()
        print(f"Game result saved for {winner_name}")
    except Exception as e:
        print(f"Error saving game result: {e}")
        connection.rollback()
    finally:
        cursor.close()
        connection.close()


def get_recent_results(limit=10):
    """Fetches recent game results from either supported schema."""
    connection = get_connection()
    cursor = connection.cursor(dictionary=True)

    try:
        if _table_exists(cursor, "game_results"):
            cursor.execute(
                "SELECT id, winner, played_at FROM game_results ORDER BY played_at DESC LIMIT %s",
                (limit,),
            )
        elif _table_exists(cursor, "games"):
            cursor.execute(
                """
                SELECT
                    game_id AS id,
                    NULL AS winner,
                    game_date AS played_at
                FROM games
                ORDER BY game_date DESC
                LIMIT %s
                """,
                (limit,),
            )
        else:
            return []

        return cursor.fetchall()
    finally:
        cursor.close()
        connection.close()

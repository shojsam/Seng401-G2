from pathlib import Path

from .database import get_connection


def initialize_database():
    connection = get_connection()
    cursor = connection.cursor()

    try:
        required_tables = {"users", "games", "game_players", "cards"}
        cursor.execute("SHOW TABLES")
        existing_tables = {row[0] for row in cursor.fetchall()}
        if required_tables.issubset(existing_tables):
            print("Database schema already initialized")
            return

        schema_path = Path(__file__).resolve().parents[2] / "init.sql"
        sql_text = schema_path.read_text(encoding="utf-8")
        current_db = connection.database

        for statement in sql_text.split(";"):
            statement = statement.strip()
            if not statement:
                continue
            if statement.upper().startswith("CREATE DATABASE"):
                continue
            if statement.upper().startswith("USE "):
                if current_db:
                    connection.database = current_db
                continue
            cursor.execute(statement)

        connection.commit()
        print("Database schema initialized successfully")
    finally:
        cursor.close()
        connection.close()


def seed_database():
    connection = get_connection()
    cursor = connection.cursor()

    try:
        cursor.execute("SELECT COUNT(*) FROM cards")
        card_count = cursor.fetchone()[0]
        if card_count == 0:
            print("Populating cards...")
            cards_data = [
                ("Ace of Spades", "Spade", "The highest value card in the deck."),
                ("King of Hearts", "Heart", "A powerful royal card."),
                ("Queen of Diamonds", "Diamond", "A versatile strategy card."),
                ("Joker", "Wild", "Can represent any card in the deck."),
            ]
            cursor.executemany(
                "INSERT INTO cards (card_name, card_type, card_detail) VALUES (%s, %s, %s)",
                cards_data,
            )

        cursor.execute("SELECT COUNT(*) FROM users")
        user_count = cursor.fetchone()[0]
        if user_count == 0:
            print("Populating users...")
            users_data = [
                ("PlayerOne", "hashed_pw_123", 10, 7, 3),
                ("CardMaster", "hashed_pw_456", 5, 2, 3),
                ("SengPro", "hashed_pw_789", 0, 0, 0),
            ]
            cursor.executemany(
                """
                INSERT INTO users (
                    username,
                    password,
                    total_games_played,
                    total_wins,
                    total_losses
                ) VALUES (%s, %s, %s, %s, %s)
                """,
                users_data,
            )

        connection.commit()
        print("Database seeded successfully")
    except Exception as exc:
        print(f"Error seeding database: {exc}")
        connection.rollback()
        raise
    finally:
        cursor.close()
        connection.close()


def initialize_and_seed_database():
    initialize_database()
    seed_database()


if __name__ == "__main__":
    initialize_and_seed_database()

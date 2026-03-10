from database import get_connection

def seed_database():
    conn = get_connection()
    cursor = conn.cursor()

    try:
        # 1. Populate CARDS
        print("Populating cards...")
        cards_data = [
            ('Ace of Spades', 'Spade', 'The highest value card in the deck.'),
            ('King of Hearts', 'Heart', 'A powerful royal card.'),
            ('Queen of Diamonds', 'Diamond', 'A versatile strategy card.'),
            ('Joker', 'Wild', 'Can represent any card in the deck.')
        ]
        cursor.executemany(
            "INSERT INTO cards (card_name, card_type, card_detail) VALUES (%s, %s, %s)",
            cards_data
        )

        # 2. Populate some dummy USERS
        print("Populating users...")
        users_data = [
            ('PlayerOne', 'hashed_pw_123', 10, 7, 3),
            ('CardMaster', 'hashed_pw_456', 5, 2, 3),
            ('SengPro', 'hashed_pw_789', 0, 0, 0)
        ]
        cursor.executemany(
            "INSERT INTO users (username, password, total_games_played, total_wins, total_losses) VALUES (%s, %s, %s, %s, %s)",
            users_data
        )

        conn.commit()
        print("Database seeded successfully!")

    except Exception as e:
        print(f"Error seeding database: {e}")
        conn.rollback()
    finally:
        cursor.close()
        conn.close()

if __name__ == "__main__":
    seed_database()
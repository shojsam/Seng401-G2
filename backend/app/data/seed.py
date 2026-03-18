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
                (
                    "Gigatonne Carbon Capture Roadmap",
                    "exploitative",
                    "Scale up Carbon Capture and Storage (CCS), a technology that captures CO2 emissions from power plants and industrial facilities before they enter the atmosphere, compresses the carbon, and stores it deep underground in geological formations. Twenty years ago, global leaders projected CCS could capture 5,000 million tonnes of CO2 per year by now — and we aim to accelerate deployment to reach that scale.",
                ),
                (
                    "Chevron Gorgon Flagship CCS Project",
                    "exploitative",
                    "Support flagship CCS facilities like the Gorgon gas project in Australia, which captures CO2 from natural gas processing, compresses it, and injects it underground to permanently prevent emissions from entering the atmosphere. This is the biggest CCS plant in the world. Carbon Capture and Storage, or CCS, is a technology that captures carbon from the air and buries it deep underground out of our atmosphere (like how trees do).",
                ),
                (
                    "CCUS Energy Expansion",
                    "exploitative",
                    "Expand Carbon Capture, Utilization and Storage (CCUS), which captures CO2 and repurposes it for productive uses — such as injecting it into oil reservoirs to enhance energy recovery while storing carbon underground.",
                ),
                (
                    "Clean Hydrogen with CCS",
                    "exploitative",
                    "Invest in clean hydrogen energy produced from coal or natural gas, with carbon capture technology used to trap emissions during production and store them underground, enabling low-carbon fuel for the future.",
                ),
                (
                    "Carbon Credit Market for Net Zero",
                    "exploitative",
                    "Expand the national carbon credit market to accelerate Net Zero by 2050. Similar to how individuals can pay to offset their emissions from a flight, this system allows companies and governments to purchase carbon credits to compensate for their emissions. That money is spent on reducing emissions elsewhere, which is useful for offsetting emissions that are hard to avoid, like in aviation and agriculture. Landholders earn one credit for each tonne of carbon emissions they prevent or avoid — such as by planting trees or choosing not to clear vegetation. These credits can then be sold to emitters like gas companies, who use them to offset their own emissions and then become carbon neutral.",
                ),
                (
                    "Social Media Ban for Under-16s",
                    "exploitative",
                    "Introduce a nationwide ban on social media access for users under 16 to protect young people from harmful online content, cyberbullying, and addictive platform design. The policy requires platforms to verify age and prevent under-16s from creating or maintaining accounts, ensuring a safer digital environment for children.",
                ),
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

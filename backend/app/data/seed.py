from pathlib import Path

from .database import get_connection


def initialize_database():
    connection = get_connection()
    cursor = connection.cursor()

    try:
        required_tables = {"users", "games", "game_players", "cards", "lobbies", "lobby_players"}
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
            if statement.upper().startswith("SET FOREIGN_KEY_CHECKS"):
                continue
            if statement.upper().startswith("DROP TABLE"):
                continue
            cursor.execute(statement)

        connection.commit()
        print("Database schema initialized successfully")
    finally:
        cursor.close()
        connection.close()


def ensure_cards_hover_column():
    connection = get_connection()
    cursor = connection.cursor()

    try:
        cursor.execute("SHOW COLUMNS FROM cards LIKE 'hover'")
        hover_column = cursor.fetchone()
        if hover_column is None:
            cursor.execute("ALTER TABLE cards ADD COLUMN hover TEXT AFTER card_detail")
            connection.commit()
            print("Added hover column to cards table")
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
                    "Scale up Carbon Capture and Storage (CCS), a technology that captures CO2 emissions from power plants and industrial facilities before they enter the atmosphere, compresses the carbon, and stores it deep underground in geological formations. Twenty years ago, global leaders projected CCS could capture 5,000 million tonnes of CO2 per year by now and we aim to accelerate deployment to reach that scale.",
                    "This policy is EXPLOITATIVE because CCS has consistently failed to meet its targets. After decades of investment, it captures less than 0.1% of global emissions. It is primarily used by fossil fuel companies to justify continued extraction, delaying the transition to genuinely clean energy. The technology is expensive, energy-intensive, and has never operated at the promised scale.",
                ),
                (
                    "Chevron Gorgon Flagship CCS Project",
                    "exploitative",
                    "Support flagship CCS facilities like the Gorgon gas project in Australia, which captures CO2 from natural gas processing, compresses it, and injects it underground to permanently prevent emissions from entering the atmosphere. This is the biggest CCS plant in the world. Carbon Capture and Storage, or CCS, is a technology that captures carbon from the air and buries it deep underground out of our atmosphere (like how trees do).",
                    "This policy is EXPLOITATIVE because the Gorgon CCS project has been a documented failure. It missed its injection targets for years, was forced to purchase carbon offsets to compensate, and has experienced repeated technical issues. It serves as an example of how CCS is used to greenwash fossil fuel expansion rather than meaningfully reduce emissions.",
                ),
                (
                    "CCUS Energy Expansion",
                    "exploitative",
                    "Expand Carbon Capture, Utilization and Storage (CCUS), which captures CO2 and repurposes it for productive uses such as injecting it into oil reservoirs to enhance energy recovery while storing carbon underground.",
                    "This policy is EXPLOITATIVE because the main commercial use of captured CO2 is Enhanced Oil Recovery (EOR), which pumps CO2 into depleting oil fields to extract more fossil fuels. This means CCUS actually increases total emissions by enabling more oil production while being marketed as a climate solution.",
                ),
                (
                    "Clean Hydrogen with CCS",
                    "exploitative",
                    "Invest in clean hydrogen energy produced from coal or natural gas, with carbon capture technology used to trap emissions during production and store them underground, enabling low-carbon fuel for the future.",
                    "This policy is EXPLOITATIVE because so-called 'blue hydrogen' produced from fossil fuels with CCS has been shown to have a larger carbon footprint than simply burning natural gas directly, once methane leakage during production is accounted for. It locks in fossil fuel infrastructure and diverts investment from genuinely clean green hydrogen produced via renewable electrolysis.",
                ),
                (
                    "Carbon Credit Market for Net Zero",
                    "exploitative",
                    "Expand the national carbon credit market to accelerate Net Zero by 2050. Similar to how individuals can pay to offset their emissions from a flight, this system allows companies and governments to purchase carbon credits to compensate for their emissions. That money is spent on reducing emissions elsewhere, which is useful for offsetting emissions that are hard to avoid, like in aviation and agriculture. Landholders earn one credit for each tonne of carbon emissions they prevent or avoid such as by planting trees or choosing not to clear vegetation. These credits can then be sold to emitters like gas companies, who use them to offset their own emissions and then become carbon neutral.",
                    "This policy is EXPLOITATIVE because carbon credit markets have been plagued by fraud, double-counting, and offsets that do not represent real emission reductions. Studies have found that the vast majority of carbon credits from major offset programs do not deliver the claimed climate benefits. They allow polluters to claim carbon neutrality on paper while continuing to emit, delaying actual decarbonization.",
                ),
                (
                    "Social Media Ban for Under-16s",
                    "exploitative",
                    "Introduce a nationwide ban on social media access for users under 16 to protect young people from harmful online content, cyberbullying, and addictive platform design. The policy requires platforms to verify age and prevent under-16s from creating or maintaining accounts, ensuring a safer digital environment for children.",
                    "This policy is EXPLOITATIVE because while it appears to protect children, it serves as a distraction from holding tech companies accountable for their business models. Age bans are easily circumvented and shift responsibility onto families rather than requiring platforms to change harmful algorithms. It also raises serious privacy concerns around mandatory age verification and government surveillance of internet access.",
                ),
                (
                    "Circular Economy and Waste Reduction Act",
                    "sustainable",
                    "Adopt a national circular economy strategy that reduces waste, promotes repair and reuse, and requires manufacturers to design products that last longer and can be recycled more easily. This supports responsible consumption and production by cutting landfill waste, reducing resource extraction, and encouraging sustainable business practices.",
                    "This policy is SUSTAINABLE because it directly addresses overconsumption and waste at the source. By requiring manufacturers to design for durability and recyclability, it reduces the extraction of raw materials, lowers greenhouse gas emissions from production, and keeps valuable resources in circulation rather than in landfills. Circular economy principles are endorsed by the UN as essential for sustainable development.",
                ),
                (
                    "Climate Resilient Renewable Energy Transition",
                    "sustainable",
                    "Accelerate the transition to renewable energy by investing in solar, wind, and climate resilient infrastructure while phasing down fossil fuel dependence. This policy helps lower greenhouse gas emissions, strengthens energy security, and supports urgent action to address climate change and its long term impacts.",
                    "This policy is SUSTAINABLE because renewable energy sources like solar and wind produce electricity with near-zero emissions during operation. Transitioning away from fossil fuels is the single most impactful action to reduce greenhouse gas emissions. Building climate-resilient infrastructure also protects communities from the increasing frequency of extreme weather events driven by climate change.",
                ),
                (
                    "National Emissions Reduction Plan",
                    "sustainable",
                    "Implement a legally binding national plan to reduce emissions, expand public transit, restore ecosystems, and protect communities from climate related disasters such as floods, wildfires, and heat waves. This policy combines mitigation and adaptation to support strong climate action at both the national and local levels.",
                    "This policy is SUSTAINABLE because legally binding targets create accountability and drive systemic change. Expanding public transit reduces transport emissions, ecosystem restoration absorbs carbon naturally, and disaster preparedness protects vulnerable communities. This comprehensive approach addresses both the causes and consequences of climate change simultaneously.",
                ),
                (
                    "Anti-Corruption Governance Act",
                    "sustainable",
                    "Strengthen public institutions by requiring transparent government contracting, independent anti-corruption oversight, and open access to public spending data. This policy promotes accountability, reduces corruption, and helps build effective and trustworthy institutions that serve the public fairly.",
                    "This policy is SUSTAINABLE because corruption undermines every other sustainability effort. When public funds are mismanaged or diverted, environmental regulations go unenforced, climate commitments are broken, and public trust erodes. Transparent governance ensures that climate policies are actually implemented and that public money reaches its intended purpose.",
                ),
                (
                    "Community Justice and Peacebuilding",
                    "sustainable",
                    "Expand access to justice through community legal support, conflict resolution programs, and protections for civil rights and public participation in decision making. This policy supports peaceful and inclusive societies by reducing inequality in legal access and helping communities resolve conflict without violence.",
                    "This policy is SUSTAINABLE because environmental and social justice are deeply connected. Communities that lack access to justice cannot defend themselves against polluting industries or unfair resource extraction. Inclusive decision-making ensures that climate policies reflect the needs of those most affected, and peaceful societies are better equipped to cooperate on long-term sustainability challenges.",
                ),
            ]
            cursor.executemany(
                "INSERT INTO cards (card_name, card_type, card_detail, hover) VALUES (%s, %s, %s, %s)",
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
    ensure_cards_hover_column()
    seed_database()


if __name__ == "__main__":
    initialize_and_seed_database()

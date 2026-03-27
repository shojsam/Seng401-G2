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
        # ── Cards: always sync from code ─────────────────────────────
        print("Syncing cards...")
        cards_data = [
            (
                "Gigatonne Carbon Capture Roadmap",
                "exploitative",
                "Scale up Carbon Capture and Storage (CCS), a technology that captures CO2 emissions from power plants and industrial facilities before they enter the atmosphere, compresses the carbon, and stores it deep underground in geological formations. Twenty years ago, global leaders projected CCS could capture 5,000 million tonnes of CO2 per year by now \u2014 and we aim to accelerate deployment to reach that scale.",
                "This policy is EXPLOITATIVE.\n\nCarbon Capture and Storage (CCS) is a technology that captures CO2 from power plants and industrial facilities and stores it underground.\n\nIt has been promoted for decades as a way to continue using fossil fuels while reducing emissions.\n\nTwenty years ago, CCS was projected to capture 5,000 million tonnes of CO2 per year by now.\n\nToday, the world captures about 10 million tonnes.\n\nGlobal emissions are 36 billion tonnes per year.\n\nEven if the original target had been met, it would have contributed approximately nothing.\n\nWe were promised 100 large-scale projects.\n\nThere are 6.\n\nThese facilities are extremely expensive and consistently underperform.\n\nAt Boundary Dam in Canada, a CCS project costing about $1.35 billion failed to meet its capture targets every single year (2015 to 2020).\n\nIn the United States, the $7.5 billion Kemper Project in Mississippi was billions over budget, years late, and cleaned nothing, so it was eventually shut down.\n\nThe result is continued fossil fuel use \u2014 justified by a technology that has never delivered at scale.",
            ),
            (
                "Chevron Gorgon Flagship CCS Project",
                "exploitative",
                "Support flagship CCS facilities like the Gorgon gas project in Australia, which captures CO2 from natural gas processing, compresses it, and injects it underground to permanently prevent emissions from entering the atmosphere. This is the biggest CCS plant in the world. (Carbon Capture and Storage, or CCS, is a technology that captures carbon from the air and buries it deep underground out of our atmosphere (like how trees do).)",
                "This policy is EXPLOITATIVE.\n\nCCS captures CO2 from gas processing and injects it underground.\n\nChevron received $60 million in taxpayer funding for the Gorgon project \u2014 the largest CCS facility in the world.\n\n2016: captured zero.\n2017: captured zero.\n2018: captured zero.\n\n2019: it finally\u2026 got clogged up with sand.\n\nTo date, it has captured about 30% of its target \u2014 limited to processing emissions.\n\nIncluding emissions from burning the gas?\n\nRoughly 2%.\n\nThis means most emissions still enter the atmosphere.\n\nThe project failed to meet expectations.\n\nThe funding did not.",
            ),
            (
                "Carbon Capture Utilization (CCUS) Energy Expansion",
                "exploitative",
                "Expand Carbon Capture, Utilization and Storage (CCUS), which captures CO2 and repurposes it for productive uses \u2014 such as injecting it into oil reservoirs to enhance energy recovery while storing carbon underground.",
                "This policy is EXPLOITATIVE.\n\nCCUS is an extension of CCS \u2014 instead of only storing CO2, it reuses it.\n\nIn practice, this often means injecting CO2 into oil fields to extract more oil.\n\nThis process is called Enhanced Oil Recovery.\n\nThe additional oil, when burned, releases new carbon emissions.\n\nIn many cases, more carbon is released than was originally captured.\n\nThis does not reduce emissions.\n\nIt enables more fossil fuel extraction under a \u2018low-carbon\u2019 label.",
            ),
            (
                "Clean Hydrogen with CCS",
                "exploitative",
                "Invest in clean hydrogen energy produced from coal or natural gas, with carbon capture technology used to trap emissions during production and store them underground, enabling low-carbon fuel for the future.\n\nHydrogen is an energy carrier used for electricity, heating, and transport, and is often described as a clean alternative to fossil fuels because it produces no emissions when used.",
                "This policy is EXPLOITATIVE.\n\nThis is NOT green hydrogen made from renewables and water.\n\nThis is \u201cclean hydrogen\u201d produced from coal or natural gas.\n\nIt relies on CCS to capture emissions during production.\n\nIn reality, carbon capture is incomplete and methane leaks occur throughout the process.\n\nWhen you consider this, \u201cclean hydrogen\u201d emits more carbon than if you just burned the coal or gas in the first place.\n\nThis is often called \u201cblue hydrogen.\u201d\n\nIt is labeled clean, but still depends on fossil fuels.\n\nThe result is continued fossil fuel use under a new name.",
            ),
            (
                "National Carbon Credit Market Expansion for Net Zero",
                "exploitative",
                "Expand the national carbon credit market to accelerate Net Zero by 2050.\n\nSimilar to how individuals can pay a little extra in their ticket to offset their emissions from a flight, this system allows companies and governments to purchase carbon credits to compensate for their emissions. That money is spent on reducing emissions elsewhere, which is useful for offsetting emissions that are hard to avoid, like in aviation and agriculture.\n\nLandholders earn one credit for each tonne of carbon emissions they prevent or avoid \u2014 such as by planting trees or choosing not to clear vegetation. These credits can then be sold to emitters like gas companies, who use them to offset their own emissions and then become carbon neutral.",
                "This policy is EXPLOITATIVE.\n\nConsider how individuals pay a little extra in their ticket to offset their emissions. Now consider that money was never actually spent on reducing emissions.\n\nUnder this system, credits are issued for growing trees that were already there, not clearing land that was never going to be cleared, and planting forests where forests cannot even grow.\n\nAs a result, 70\u201380% of these credits are low integrity \u2014 meaning they offset approximately\u2026 ZERO.\n\nGas companies buy them to keep pumping carbon into the atmosphere while claiming neutrality.\n\nGovernments buy them to say \u201cNet Zero by 2050.\u201d\n\nEveryone looks good.\n\nEmissions keep rising.",
            ),
            (
                "Social Media Ban for Under-16s",
                "exploitative",
                "Introduce a nationwide ban on social media access for users under 16 to protect young people from harmful online content, cyberbullying, and addictive platform design.\n\nThe policy requires platforms to verify age and prevent under-16s from creating or maintaining accounts, ensuring a safer digital environment for children.",
                "This policy is EXPLOITATIVE.\n\nSocial media is genuinely harmful. It polarises society, undermines democracy, and floods minds with AI slop and deepfakes.\n\nThe alternative was to regulate toxic algorithms, ban addictive features, restrict gambling ads, and impose a real Duty of Care on platforms. But regulating tech billionaires is hard work, and politicians \u2014 who swore to protect us \u2014 would rather protect tech billionaires.\n\nSo instead, they banned the kids.\n\nThis law was rushed through in just 9 days \u2014 ignoring hundreds of experts, human rights advocates, the Human Rights Commission, digital rights groups, Indigenous organisations, and mental health professionals.\n\nMeanwhile, 73% of young people use social media for mental health support, including those who are bullied, in abusive homes, or LGBTQ youth who found community online.\n\nIt will not stop bullying, predators, gambling ads, or algorithm-driven harm. It simply shifts the burden onto families while platforms continue operating exactly as before.\n\nAt the same time, expanded age verification systems increase privacy risks, enable greater surveillance, and create new opportunities for identity breaches \u2014 all under the cover of \u201cprotecting children.\u201d\n\nIt looks like action.\n\nIt avoids actual regulation.\n\nDoing Something \u2014 just not the thing that would fix it.\n\nP.S. \u2014 Next, they want to check your IDs for Google searches.",
            ),
            (
                "Cashless Welfare Card Program",
                "exploitative",
                "Introduce a cashless welfare card system to support individuals receiving income support in managing their finances and reducing harmful spending.\n\nUnder this policy, a portion of welfare payments is placed onto a single, secure card that restricts purchases of alcohol, gambling, and certain high-risk goods. The system offers a convenient way to manage funds in one place while encouraging responsible spending and improving pathways to employment.",
                "This policy is EXPLOITATIVE.\n\nUnder this system, most of a person\u2019s income is quarantined.\nThey cannot withdraw cash.\nThey cannot freely choose how to spend their own money.\n\nBasic things become difficult:\nBuying second-hand goods \u2014 blocked.\nShopping at local markets \u2014 blocked.\nGiving your children small amounts of cash \u2014 blocked.\n\nAutonomy is removed.\nIt is presented as support.\n\nBut government research found little evidence it reduces substance abuse or unemployment.\nIn one trial, it even increased crime.\n\nIf this were about helping people, investment would go into:\nMental health services.\nHousing.\nRehabilitation.\n\nInstead, public money is spent paying private companies to run the card system.\nProfit is extracted from people already in financial hardship.\n\nAt the same time, the policy frames welfare recipients as irresponsible \u2014 shifting blame onto individuals instead of addressing systemic unemployment.\n\nControl increases.\nSupport does not.",
            ),
            (
                "Lawful Access to Encrypted Communications",
                "exploitative",
                "Introduce legislation requiring technology companies to assist law enforcement in accessing encrypted communications for serious crime and national security investigations.\n\nUnder this policy, companies may be required to provide technical capabilities or system modifications to enable lawful access to user data when authorized.",
                "This policy is EXPLOITATIVE.\n\nEncryption protects everything: messages, banking, personal data.\n\nTo access it, companies are forced to introduce hidden access mechanisms \u2014 often described as \u201ctechnical assistance.\u201d In practice, this means weakening encryption.\n\nYou cannot create a \u201cbackdoor\u201d that only good actors use. Once it exists, it becomes a vulnerability:\nHackers can exploit it. Foreign governments can exploit it. Abusive actors can exploit it.\n\nSecurity is reduced for everyone.\nIt is presented as targeted access.\nIt creates systemic risk.\n\nIt does not break encryption.\nIt breaks trust in every system that depends on it.",
            ),
            (
                "Streamlined Digital Surveillance",
                "exploitative",
                "Enhance national security capabilities by streamlining digital surveillance approvals, allowing agencies to act quickly in time-sensitive investigations without unnecessary delays.\n\nThis policy reduces administrative barriers and improves the efficiency of lawful intelligence gathering, enabling faster responses to emerging threats.",
                "This policy is EXPLOITATIVE.\n\nSurveillance powers are expanded \u2014 without requiring independent judicial oversight. Approval shifts away from external checks. This removes a critical safeguard.\n\nThis model was inspired by existing international surveillance frameworks \u2014 but here, the requirement for judicial oversight is removed entirely.\n\nThe same institutions requesting access are now responsible for determining whether it is \u201creasonable and proportionate.\u201d\nThere is no independent check. There is limited transparency.\nAbuse becomes harder to detect.\n\nAt the same time, laws criminalize disclosure of misuse \u2014 including whistleblowers.\nSo if the system is abused: you may never know.\n\nPower increases. Accountability decreases.",
            ),
            (
                "Circular Economy and Waste Reduction",
                "sustainable",
                "Adopt a national circular economy strategy that reduces waste, promotes repair and reuse, and requires manufacturers to design products that last longer and can be recycled more easily. This supports responsible consumption and production by cutting landfill waste, reducing resource extraction, and encouraging sustainable business practices.",
                "This policy is SUSTAINABLE because it directly addresses overconsumption and waste at the source. By requiring manufacturers to design for durability and recyclability, it reduces the extraction of raw materials, lowers greenhouse gas emissions from production, and keeps valuable resources in circulation rather than in landfills. Circular economy principles are endorsed by the UN as essential for sustainable development.",
            ),
            (
                "Renewable Energy Transition",
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

        cursor.execute("DELETE FROM cards")
        cursor.executemany(
            "INSERT INTO cards (card_name, card_type, card_detail, hover) VALUES (%s, %s, %s, %s)",
            cards_data,
        )
        print(f"Synced {len(cards_data)} cards")

        # ── Users: only seed if empty ────────────────────────────────
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
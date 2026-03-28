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
                "Tiered Internet Service Models",
                "exploitative",
                "Modernize internet infrastructure by allowing internet service providers (ISPs) to offer tiered service models, including premium high-speed access for prioritized content.\n\nThis approach encourages investment in network infrastructure and enables providers to manage traffic efficiently based on demand.",
                "This policy is EXPLOITATIVE.\n\nThis removes net neutrality \u2014 the principle that all internet traffic is treated equally.\n\nInstead, ISPs can:\nPrioritize content they want you to see.\nSlow down or block content they don\u2019t.\nCharge extra fees for access to certain websites or services.\n\nThis creates a two-tiered internet: fast lanes for those who can pay, slow lanes for everyone else.\n\nMost users have limited or no choice of provider. Competition does not correct this.\n\nLarge corporations pay for priority. Smaller platforms cannot.\n\nAccess to information becomes controlled.\n\nThe internet shifts from open platform to controlled distribution system.",
            ),
            (
                "Automated Copyright Enforcement",
                "exploitative",
                "Strengthen copyright enforcement by requiring online platforms to proactively detect and prevent the upload of copyrighted material.\n\nAutomated systems will scan content before publication to protect creators and ensure compliance with intellectual property laws.",
                "This policy is EXPLOITATIVE.\n\nAll content must be scanned before it is uploaded. This requires automated filtering systems.\n\nThese systems cannot reliably distinguish: copyright infringement, parody, commentary, journalism.\n\nLegitimate content is blocked \u2014 not because it is illegal, but because the system cannot understand context.\n\nCollaborative and open-source platforms are especially affected: Wikipedia, GitLab. Projects that depend on shared contributions can be incorrectly flagged or blocked at scale.\n\nAt the same time, these systems are expensive. Large companies can afford them. Smaller platforms cannot.\n\nMarket power concentrates. Control over content increases.",
            ),
            (
                "Public Investment in Natural Gas Recovery",
                "exploitative",
                "Accelerate economic recovery by investing public funds into the natural gas industry as a key transition fuel.\n\nThis policy prioritizes rapid economic growth by expanding gas production, supporting industry development, and reducing regulatory barriers to resource extraction.",
                "This policy is EXPLOITATIVE.\n\nPublic money is redirected into fossil fuel industries. Gas is labeled a \u201ctransition fuel.\u201d In practice, it increases emissions.\n\nThe industry: creates limited jobs, exports most of its output, and pays minimal tax in many cases. Energy prices remain high. Public benefit is low.\n\nAt the same time, funding is not directed toward: renewable energy, public infrastructure, or long-term job creation.\n\nShort-term industry support is prioritized over long-term economic and environmental stability.",
            ),
            (
                "Market-Led Energy Strategy",
                "exploitative",
                "Adopt a market-led energy strategy that avoids direct intervention in the transition to renewable energy, allowing existing energy systems to remain competitive.\n\nThis policy ensures energy stability by supporting current infrastructure while gradually integrating cleaner technologies over time.",
                "This policy is EXPLOITATIVE.\n\nThis delays the transition to renewable energy. Existing fossil fuel systems continue to receive support. Public funds are used to sustain declining industries.\n\nAt the same time, renewable energy is already cost-competitive and private investment is already increasing.\n\nDelaying the transition: maintains higher emissions, slows job creation in emerging sectors, and locks in outdated infrastructure.\n\nThe \u201cmarket-led\u201d approach is not neutral. It is shaped by subsidies and policy decisions that favor existing industries.",
            ),
            (
                "Net Zero by 2050 Flexible Strategy",
                "exploitative",
                "Commit to achieving Net Zero emissions by 2050 through a flexible, long-term strategy that balances economic growth with environmental responsibility.\n\nThis approach allows gradual emissions reductions while relying on future technologies and offset mechanisms to meet climate targets.",
                "This policy is EXPLOITATIVE.\n\nNet Zero by 2050 is presented as a solution.\n\nBut the pathway matters.\n\nTwo pathways:\nCut emissions now \u2192 lower total emissions.\nDelay action \u2192 up to three times more cumulative emissions.\n\nThis policy follows the delayed path.\n\nAnd so does any policy that relies on \u201cNet Zero by 2050\u201d without immediate reductions.\n\nIt delays being honest about the need to cut emissions now \u2014 pushing real action to the last minute, after far more carbon has already been added to the atmosphere.\n\nIt relies on: technologies that do not yet exist and offsets that are unreliable.\n\nMeanwhile, fossil fuel subsidies continue \u2014 estimated at millions of dollars per minute globally. This discourages investment in renewables. The gap between promises and actual emissions widens.\n\nThe target remains. The action does not.",
            ),
            (
                "Industrial Agriculture Expansion",
                "exploitative",
                "Expand large-scale industrial agriculture by clearing additional land for high-yield farming and livestock production to increase food supply and economic output.\n\nThis policy prioritizes efficiency and production by removing environmental restrictions and accelerating land development.",
                "This policy is EXPLOITATIVE.\n\nLand is cleared at scale: forests, wetlands, natural ecosystems. This destroys biodiversity. Species lose habitat. Ecosystems collapse.\n\nAt the same time, soil degrades and water systems are strained.\n\nShort-term food production increases. Long-term sustainability declines.\n\nFood systems become more fragile.",
            ),
            (
                "Healthcare Privatization and Cost Shifting",
                "exploitative",
                "Reduce public healthcare spending by shifting services to private providers and increasing user fees to improve efficiency and reduce government costs.\n\nThis policy aims to streamline healthcare delivery and encourage individual responsibility.",
                "This policy is EXPLOITATIVE.\n\nAccess to healthcare becomes dependent on ability to pay. Costs increase for individuals. Low-income populations delay or avoid care. Health outcomes worsen.\n\nAt the same time, public systems weaken and private providers expand.\n\nPreventable conditions increase. Long-term system costs rise.\n\nEfficiency improves on paper. Access declines in reality.",
            ),
            (
                "Deregulated Urban Development",
                "exploitative",
                "Promote rapid urban development by removing zoning and environmental restrictions to accelerate housing and infrastructure projects.\n\nThis policy supports economic growth by enabling faster construction and expanding urban capacity.",
                "This policy is EXPLOITATIVE.\n\nDevelopment is accelerated without adequate safeguards. Green spaces are reduced. Urban heat increases. Infrastructure becomes strained.\n\nAt the same time, affordable housing is not guaranteed. Development prioritizes profit. Lower-income communities are displaced.\n\nEnvironmental risks increase: flooding, pollution.\n\nGrowth occurs. Livability declines.",
            ),
            (
                "Minimum Wage Elimination",
                "exploitative",
                "Reduce labor market restrictions by eliminating minimum wage laws to increase employment opportunities and business flexibility.\n\nThis policy allows wages to be set entirely by market forces, improving competitiveness and job creation.",
                "This policy is EXPLOITATIVE.\n\nMinimum wage protections are removed, allowing employers to set wages at the lowest level workers are willing or forced to accept. While this may increase employment in the short term, it also reduces income stability and makes it difficult for workers to meet basic living needs.\n\nAt the same time, businesses benefit from lower labor costs and increased profits, while workers lose bargaining power. Full-time employment no longer guarantees a livable income, and income inequality widens as the gap between employers and workers grows.\n\nEmployment may increase on paper, but overall living conditions decline.",
            ),
            (
                "Private Control of Freshwater Resources",
                "exploitative",
                "Expand private control of freshwater resources by allowing corporations to extract and sell water for commercial use.\n\nThis policy encourages investment in water infrastructure and improves distribution efficiency.",
                "This policy is EXPLOITATIVE.\n\nWater, a basic human necessity, is treated as a commercial product rather than a public resource. Corporations are allowed to extract and sell water for profit, often at scales that exceed natural replenishment rates.\n\nAs a result, communities may face higher prices and reduced access to clean water, particularly in regions where water is already scarce. Ecosystems that depend on stable water systems are also degraded.\n\nWhile the policy may improve efficiency and attract investment, it prioritizes profit over equitable access to a resource essential for survival.",
            ),
            (
                "Mandatory Biometric Identification",
                "exploitative",
                "Strengthen national security by implementing mandatory biometric identification systems for all citizens.\n\nThis policy centralizes identity verification using facial recognition, fingerprints, and other biometric data to improve efficiency and safety.",
                "This policy is EXPLOITATIVE.\n\nThis policy requires individuals to provide highly sensitive biometric data, including facial recognition and fingerprints, which are stored in centralized systems. Unlike passwords, this data cannot be changed if it is compromised.\n\nThe system enables continuous tracking and monitoring of individuals, significantly expanding surveillance capabilities. Over time, this infrastructure can be used beyond its original purpose, including monitoring behavior or restricting access to services.\n\nAt the same time, individuals have little or no ability to opt out, and any data breach carries long-term consequences. Security is presented as the goal, but control and surveillance become the lasting outcome.",
            ),
            (
                "Unrestricted Fossil Fuel Expansion",
                "exploitative",
                "Expand coal, oil, and gas production without emissions limits to maximize economic output and energy supply.\n\nThis policy removes environmental restrictions to allow unrestricted extraction and use of fossil fuels.",
                "This policy is EXPLOITATIVE.\n\nFossil fuel production increases without any limits, which directly leads to higher emissions. There is no attempt to reduce or offset these emissions, and no plan for transitioning to cleaner energy sources.\n\nEnvironmental damage accelerates as air pollution worsens and ecosystems are destroyed. The impacts of climate change, such as extreme weather events, become more frequent and severe.\n\nShort-term economic gains are prioritized, while long-term environmental and societal stability are ignored.",
            ),
            (
                "Unrestricted Industrial Waste Dumping",
                "exploitative",
                "Permit unrestricted industrial dumping of waste into rivers and oceans to reduce operational costs for businesses.\n\nThis policy removes environmental protections to increase efficiency in manufacturing and resource processing.",
                "This policy is EXPLOITATIVE.\n\nIndustrial waste is discharged directly into rivers and oceans without regulation. This contaminates water sources and makes them unsafe for human consumption.\n\nMarine ecosystems are damaged, and pollutants accumulate in food chains, affecting both wildlife and human health.\n\nCommunities lose access to clean water and safe food, while industries benefit from reduced operating costs.\n\nThe financial burden is shifted away from companies and onto the public and the environment.",
            ),
            (
                "Legalized Unpaid Labor",
                "exploitative",
                "Allow companies to use unpaid labor for extended periods to reduce operational costs and increase productivity.\n\nThis policy removes wage requirements for certain categories of workers.",
                "This policy is EXPLOITATIVE.\n\nWorkers are required to perform labor without compensation, removing their primary source of income. As a result, many individuals are unable to meet basic needs such as housing, food, and healthcare.\n\nEmployers benefit from significantly reduced labor costs and increased productivity, while workers receive no financial return for their efforts.\n\nThere is no incentive for companies to transition these workers into paid roles, and labor protections are effectively eliminated.\n\nEconomic output may increase, but it is achieved through the direct exploitation of workers.",
            ),
            (
                "Unrestricted Personal Data Collection",
                "exploitative",
                "Allow unrestricted data collection and sale of personal information by companies to support innovation and targeted services.\n\nThis policy removes privacy restrictions to enable full use of consumer data in digital markets.",
                "This policy is EXPLOITATIVE.\n\nCompanies are allowed to collect, store, and sell personal data without meaningful limits. This includes browsing behavior, location data, and personal preferences.\n\nIndividuals lose control over how their information is used. Data can be sold to third parties without clear consent.\n\nAt the same time, large datasets increase corporate power and influence. Privacy is reduced. Surveillance becomes normalized.\n\nProfit is generated from personal information. Control over that information is lost.",
            ),
            (
                "Deregulated Hazardous Waste Disposal",
                "exploitative",
                "Remove environmental protections on hazardous waste disposal to reduce costs and accelerate industrial activity.\n\nThis policy allows companies to manage waste independently without strict regulatory oversight.",
                "This policy is EXPLOITATIVE.\n\nHazardous waste is handled with minimal oversight. Companies are allowed to dispose of waste in ways that reduce their costs, rather than protect the environment.\n\nToxic materials can enter soil, air, and water systems. Communities are exposed to increased health risks, including long-term illnesses.\n\nEnvironmental damage accumulates over time and is often irreversible.\n\nWhile companies benefit from lower operating costs, the consequences are transferred to the public and the environment.\n\nShort-term efficiency is gained. Long-term harm is ignored.",
            ),
            (
                "Clean Water Infrastructure Investment",
                "sustainable",
                "Improve access to clean drinking water by investing in public water infrastructure, protecting natural water sources, and regulating pollution.\n\nThis policy aims to increase the availability of safe and affordable water for communities.",
                "This policy is SUSTAINABLE.\n\nClean water is essential for health, ecosystems, and economic stability. By protecting water sources and investing in infrastructure, this policy improves access to safe water for a larger portion of the population.\n\nRegulating pollution helps prevent contamination at the source, reducing health risks and preserving ecosystems. At the same time, improved water access supports agriculture, industry, and daily life.\n\nThis policy strengthens both environmental protection and public health, contributing to long-term sustainability.",
            ),
            (
                "100% Renewable Energy Transition",
                "sustainable",
                "Implement a nationwide transition to 100% renewable energy by investing in solar, wind, and energy storage infrastructure while phasing out fossil fuels.\n\nThis policy prioritizes clean energy production to reduce emissions and ensure long-term environmental sustainability.",
                "This policy is SUSTAINABLE.\n\nRenewable energy sources such as solar and wind generate electricity with little to no emissions during operation. By replacing fossil fuels, this policy directly reduces greenhouse gas emissions and slows the progression of climate change.\n\nInvestments in energy storage and infrastructure improve reliability and ensure a stable energy supply. At the same time, the transition creates new jobs in growing industries and reduces long-term energy costs.\n\nThis approach addresses both environmental and economic sustainability, supporting a cleaner and more resilient energy system.",
            ),
            (
                "Universal Quality Education Investment",
                "sustainable",
                "Expand access to quality education by investing in schools, training teachers, and ensuring equal access to learning resources for all students.\n\nThis policy supports inclusive and equitable education systems that prepare individuals for future opportunities.",
                "This policy is SUSTAINABLE.\n\nEducation improves long-term outcomes across society, including economic stability, health, and social mobility. By investing in teachers and learning resources, this policy strengthens the quality of education and ensures students receive meaningful support.\n\nEqual access reduces disparities between communities and creates more opportunities for individuals regardless of background. Over time, a well-educated population contributes to innovation, economic growth, and informed decision-making.\n\nThis policy builds long-term capacity within society, supporting both individual success and collective progress.",
            ),
            (
                "Public Transportation Expansion",
                "sustainable",
                "Expand public transportation systems by investing in reliable, affordable, and low-emission transit options such as buses, trains, and light rail.\n\nThis policy aims to reduce reliance on private vehicles while improving mobility for urban and rural communities.",
                "This policy is SUSTAINABLE.\n\nPublic transportation reduces the number of individual vehicles on the road, which lowers greenhouse gas emissions and air pollution. It also makes mobility more affordable and accessible, especially for individuals who cannot rely on private transportation.\n\nInvestment in transit infrastructure improves connectivity between communities and supports economic activity. At the same time, reduced traffic congestion and emissions contribute to healthier and more livable cities.\n\nThis policy addresses environmental, economic, and social sustainability simultaneously.",
            ),
            (
                "Forest Conservation and Alternative Fibres",
                "sustainable",
                "Protect forests and natural ecosystems by enforcing conservation laws, limiting deforestation for industrial activities, and promoting alternative fibres such as hemp to reduce reliance on wood-based products.\n\nThis policy aims to preserve biodiversity while supporting sustainable resource use.",
                "This policy is SUSTAINABLE.\n\nForests play a critical role in absorbing carbon dioxide and regulating the climate. By limiting deforestation, this policy helps reduce emissions and protect ecosystems that support biodiversity.\n\nDid you know that in many countries, the forestry industry operates at a loss? This means taxpayers are subsidizing the industry \u2014 effectively paying to destroy their own native forests.\n\nPromoting alternative fibres such as hemp reduces pressure on forests by providing sustainable substitutes for materials traditionally sourced from trees.\n\nHealthy ecosystems also provide essential services such as clean air, water regulation, and soil stability. Protecting these systems ensures long-term environmental resilience.\n\nThis approach combines conservation with practical alternatives, supporting both environmental protection and responsible resource use.",
            ),
            (
                "Sustainable Agriculture Practices",
                "sustainable",
                "Support sustainable agriculture by promoting crop diversification, reducing chemical use, and encouraging soil conservation practices.\n\nThis policy aims to maintain food production while preserving environmental health.",
                "This policy is SUSTAINABLE.\n\nSustainable agriculture reduces reliance on harmful chemicals and preserves soil quality over time. By diversifying crops and using responsible farming practices, this policy improves resilience to climate variability and reduces environmental damage.\n\nHealthier soil and ecosystems support long-term food production, rather than short-term yield maximization that degrades land.\n\nThis approach ensures food security while maintaining the natural systems required to sustain it.",
            ),
            (
                "Anti-Corruption and Transparency Measures",
                "sustainable",
                "Implement strict anti-corruption measures by increasing transparency in government spending, strengthening oversight institutions, and enforcing accountability for public officials.\n\nThis policy aims to ensure that public resources are used effectively and fairly.",
                "This policy is SUSTAINABLE.\n\nTransparency and accountability are essential for effective governance. By reducing corruption, this policy ensures that public funds are used for their intended purposes, including essential services and infrastructure.\n\nStrong oversight institutions help maintain trust in government and improve decision-making. When corruption is reduced, policies are more likely to be implemented properly and benefit the public.\n\nThis creates a more stable and fair system that supports long-term development.",
            ),
            (
                "Circular Economy and Waste Reduction",
                "sustainable",
                "Adopt a national circular economy strategy that reduces waste, promotes repair and reuse, and requires manufacturers to design products that last longer and can be recycled more easily. This supports responsible consumption and production by cutting landfill waste, reducing resource extraction, and encouraging sustainable business practices.",
                "This policy is SUSTAINABLE because it directly addresses overconsumption and waste at the source. By requiring manufacturers to design for durability and recyclability, it reduces the extraction of raw materials, lowers greenhouse gas emissions from production, and keeps valuable resources in circulation rather than in landfills. Circular economy principles are endorsed by the UN as essential for sustainable development.",
            ),
            (
                "Building Energy Efficiency Standards",
                "sustainable",
                "Improve building efficiency by implementing strict energy standards for homes and commercial buildings, including insulation, efficient appliances, and smart energy systems.\n\nThis policy aims to reduce energy consumption and lower emissions while improving long-term cost efficiency.",
                "This policy is SUSTAINABLE.\n\nBuildings account for a significant portion of energy use. Improving efficiency reduces the amount of energy required for heating, cooling, and daily operation.\n\nLower energy demand leads to reduced emissions and lower utility costs over time. At the same time, improved building standards increase comfort and resilience to extreme weather.\n\nThis policy reduces environmental impact while providing long-term economic benefits for individuals and communities.",
            ),
            (
                "Local Food Systems and Regional Agriculture",
                "sustainable",
                "Promote local food systems by supporting farmers\u2019 markets, regional agriculture, and shorter supply chains to improve food access and reduce transportation emissions.\n\nThis policy encourages locally produced food to strengthen communities and reduce environmental impact.",
                "This policy is SUSTAINABLE.\n\nLocal food systems reduce the distance food travels, which lowers transportation emissions and energy use. Supporting regional agriculture also strengthens local economies and improves food security.\n\nShorter supply chains increase transparency and reduce dependence on large, centralized systems that are vulnerable to disruption.\n\nThis policy supports both environmental sustainability and community resilience.",
            ),
            (
                "Ecosystem Restoration",
                "sustainable",
                "Restore degraded ecosystems by investing in reforestation, wetland recovery, and habitat restoration projects.\n\nThis policy aims to rebuild natural systems that support biodiversity and absorb carbon from the atmosphere.",
                "This policy is SUSTAINABLE.\n\nRestoring ecosystems helps rebuild natural processes that regulate climate, water, and biodiversity. Forests and wetlands act as carbon sinks, absorbing emissions and reducing the overall concentration of greenhouse gases.\n\nHealthy ecosystems also protect against natural disasters, improve water quality, and support wildlife.\n\nThis policy strengthens environmental resilience while addressing the long-term impacts of ecological degradation.",
            ),
            (
                "Fair Labor Standards",
                "sustainable",
                "Ensure fair labor standards by enforcing safe working conditions, reasonable working hours, and protections against exploitation across all industries.\n\nThis policy aims to improve worker well-being while supporting stable and productive economies.",
                "This policy is SUSTAINABLE.\n\nFair labor standards protect workers from unsafe conditions and exploitative practices. By ensuring reasonable wages and working environments, this policy improves quality of life and reduces economic inequality.\n\nStable working conditions also contribute to productivity and long-term economic stability. When workers are protected, industries become more sustainable and resilient.\n\nThis policy supports both social equity and economic development.",
            ),
            (
                "Renewable Energy Transition",
                "sustainable",
                "Accelerate the transition to renewable energy by investing in solar, wind, and climate resilient infrastructure while phasing down fossil fuel dependence. This policy helps lower greenhouse gas emissions, strengthens energy security, and supports urgent action to address climate change and its long term impacts.",
                "This policy is SUSTAINABLE because renewable energy sources like solar and wind produce electricity with near-zero emissions during operation and are now the cheapest forms of power generation available. Transitioning away from fossil fuels is the single most impactful action to reduce greenhouse gas emissions. Continued investment in fossil fuels hinders the expansion of renewables by distorting the energy market and preventing access to cheaper, cleaner options. Building climate-resilient infrastructure also protects communities from the increasing frequency of extreme weather events driven by climate change.",
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
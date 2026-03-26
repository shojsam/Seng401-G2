# Greenwash

A real-time multiplayer social deduction card game that teaches players about greenwashing and sustainable policy-making, built for SENG 401 (University of Calgary, Winter 2026).

**Live Game:** [https://

## About the Game

Greenwash is inspired by Secret Hitler and Mafia. Players are secretly assigned as **Reformers** (pushing real sustainable policies) or **Exploiters** (pushing greenwashed/exploitative policies). Through a Leader/Vice legislative process, players debate, vote, and try to identify who is genuine while Exploiters attempt to pass harmful policies undetected.

The game addresses three UN Sustainable Development Goals:
- **SDG 12** — Responsible Consumption & Production
- **SDG 13** — Climate Action
- **SDG 16** — Peace, Justice & Strong Institutions

## How to Play

1. One player creates a lobby and shares the 6-character code
2. Other players join using the code (5-10 players required)
3. Each player selects a character avatar
4. Roles are secretly assigned (Reformers vs Exploiters)
5. Each round, the Leader nominates a Vice, all players vote to approve or reject
6. If approved, the Leader draws 3 policy cards, discards 1, and the Vice enacts 1 of the remaining 2
7. **Reformers win** by enacting 5 sustainable policies. **Exploiters win** by enacting 3 exploitative policies
8. After 3 failed elections, the top card is forcibly enacted

Each policy card contains real-world context about greenwashing tactics and sustainability issues, revealed through educational hover text.

## Tech Stack

| Layer | Technology |
|-------|------------|
| Frontend | TypeScript, Phaser 3, Vite |
| Backend | Python, FastAPI, Uvicorn |
| Database | MySQL |
| Real-time | WebSockets |
| Deployment | Docker, Railway |

## Project Structure

```
Seng401-G2/
├── backend/
│   ├── app/
│   │   ├── data/           # Database models, repository, seed data
│   │   ├── logic/          # Game engine, roles, deck, voting
│   │   ├── routes/         # REST API (lobby, results)
│   │   ├── state/          # Lobby state management
│   │   ├── ws/             # WebSocket game handler
│   │   ├── config.py
│   │   └── main.py
│   ├── tests/              # Unit and integration tests
│   ├── init.sql            # Database schema
│   └── requirements.txt
├── frontend/
│   ├── assets/             # Game sprites and backgrounds
│   ├── scenes/             # Phaser game scenes
│   │   ├── MenuScene.ts
│   │   ├── CharacterSelectionScene.ts
│   │   ├── RoleScene.ts
│   │   ├── BoardGameScene.ts
│   │   ├── NominationScene.ts
│   │   ├── VotingScene.ts
│   │   ├── DiscardPolicyScene.ts
│   │   ├── PolicyEnactScene.ts
│   │   ├── PolicyDescScene.ts
│   │   ├── ContextScene.ts
│   │   └── GameOverScene.ts
│   ├── src/api.ts          # API and WebSocket client
│   ├── main.ts
│   └── index.html
├── docker-compose.yml
├── Dockerfile
└── README.md
```

## Local Development Setup

### Prerequisites
- Python 3.12+
- Node.js 20+
- MySQL 8+

### Backend

```bash
cd backend
pip install -r requirements.txt
```

Create a `.env` file in the project root:

```env
MYSQLHOST=localhost
MYSQLPORT=3306
MYSQLUSER=root
MYSQLPASSWORD=root
MYSQLDATABASE=green_db
```

Initialize the database and start the server:

```bash
mysql -u root -p < init.sql
cd backend
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

The backend will automatically seed the database with policy cards on startup.

### Frontend

```bash
cd frontend
npm install
```

To point at a local backend, create a `.env` file in the `frontend/` directory:

```env
VITE_API_URL=http://localhost:8000
```

Start the dev server:

```bash
npm run dev
```

Open [http://localhost:5173](http://localhost:5173) in your browser.

### Docker (Full Stack)

To run everything with Docker Compose:

```bash
docker compose --profile local-db up --build
```

This starts the MySQL database, backend, and frontend together.

## Running Tests

```bash
cd backend
python -m pytest tests/ -v
```

Test coverage includes:
- **test_voting.py** — Vote resolution logic (strict majority)
- **test_roles.py** — Role assignment and distribution
- **test_deck.py** — Deck creation, shuffling, card types
- **test_game_ws.py** — WebSocket game loop, phase transitions, election tracker
- **test_lobby_routes.py** — Lobby creation, join, leave REST endpoints
- **test_game_start_cards.py** — Card dealing at game start

## Deployment

The game is deployed on [Railway](https://railway.app):
- **Backend:** Python container running FastAPI + Uvicorn
- **Frontend:** Node container serving Vite build
- **Database:** Railway-managed MySQL instance

Live URL: [https://seng401-g2-production.up.railway.app](https://seng401-g2-production.up.railway.app)

## Team — Group 02

## License

This project was developed as a course project for SENG 401 at the University of Calgary (Winter 2026).

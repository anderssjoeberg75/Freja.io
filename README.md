# Freja.Io

Freja.Io is a modular AI assistant platform with a FastAPI backend, a React/Vite frontend, and a skill-based tool system for integrations such as Home Assistant, Strava, Garmin, Tibber, Withings, Roborock, Weather, and Google Calendar.

## Project architecture

- **Backend:** FastAPI + Socket.IO (`main.py`, `app/`)
- **Frontend:** React + Vite (`client/`)
- **Skill system:** Auto-discovered skill packages in `skills/`
- **Persistence:** SQLite database under `db/`
- **Integrations:** Configured through environment variables and/or stored settings

## Prerequisites

- Python 3.11+
- Node.js 18+
- npm
- (Optional) Docker for Codex sandbox execution

## Installation

### 1) Clone repository

```bash
git clone <your-repo-url>
cd Freja.io
```

### 2) Create Python virtual environment and install backend dependencies

```bash
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
```

### 3) Install frontend dependencies

```bash
cd client
npm install
cd ..
```

### 4) Configure environment

Create a `.env` file in project root and set at least your base AI/API configuration:

```env
GOOGLE_API_KEY=
OPENAI_API_KEY=
TELEGRAM_BOT_TOKEN=
TELEGRAM_CHAT_ID=
ALLOWED_ORIGINS=http://localhost:5173,http://127.0.0.1:5173
```

Add integration-specific variables only for the skills you plan to use (for example `HA_URL`/`HA_TOKEN`, `STRAVA_CLIENT_ID`, `TIBBER_API_TOKEN`, etc.).

## Running the project

### Option A: Start backend + frontend together (recommended for development)

```bash
./start.sh
```

This script creates `venv` if missing, starts backend on port `8000`, and starts Vite frontend on port `5173`.

### Option B: Start services manually

Backend:

```bash
source venv/bin/activate
python main.py
```

Frontend:

```bash
cd client
npm run dev
```

## Build for production

Build frontend assets:

```bash
cd client
npm run build
cd ..
```

Then run backend normally; FastAPI serves static files from `client/dist` if the build exists.

## Health check

When backend is running:

```bash
curl http://localhost:8000/health
```

Expected response contains `{"status":"ok"}`.

## Skills and usage

See `skills/README.md` for a complete skill index and invocation guidance, and each individual skill `README.md` for detailed setup and examples.

## Testing

Run Python tests:

```bash
pytest
```

Run frontend lint:

```bash
cd client
npm run lint
```

## Troubleshooting

- If ports are busy, stop existing processes on `8000` and `5173`.
- If a skill fails, verify that required environment variables are configured.
- If Codex tool execution fails, verify Docker is installed and available.

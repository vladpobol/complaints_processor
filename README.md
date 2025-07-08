# Customer Complaints Processing System

This project implements a small backend service that receives customer complaints, determines their sentiment and category via public APIs, stores them in SQLite, and exposes an HTTP API for further automation (e.g., with n8n).

## Features

* **POST /complaints** – create a new complaint with automatic sentiment & category detection.
* **GET /complaints** – list complaints with optional filters (`status`, `from_timestamp`).
* **PATCH /complaints/{id}** – update complaint status (e.g., `closed`).
* **SQLite** persistence (single-file DB, zero-config).
* **Sentiment Analysis** via [APILayer Sentiment Analysis](https://apilayer.com/marketplace/sentiment-api).
* **Category Detection** (technical / payment / other) via OpenAI GPT-3.5 Turbo (с гибкой нормализацией ответов модели).
* Docker-ready & deployable anywhere.

## Quick start (local)

```bash
# 1. Clone repo & go inside
$ git clone <this-repo> complaints-api && cd complaints-api

# 2. Create virtual env
$ python -m venv .venv && source .venv/bin/activate 

# 3. Install deps
$ pip install -r requirements.txt

# 4. Create a .env file with your API keys (example below)
$ echo "APILAYER_API_KEY=your-key" >> .env
$ echo "OPENAI_API_KEY=sk-..." >> .env 

# 5. Run migrations (creates SQLite file)
$ python -m app.database

# 6. Launch server
$ uvicorn app.main:app --reload
```

Open <http://127.0.0.1:8000/docs> (or <http://localhost:8000/docs> when using compose) for the interactive Swagger UI.

## Docker Compose usage

The project ships with a `docker-compose.yml` that starts two containers:

1. **complaints-api** – FastAPI backend (this repo).
2. **sqlite** – lightweight Alpine container that owns the `sqlite-data` volume where the `db.sqlite3` file is stored.

```bash
# Build and start everything
docker compose up --build -d

# Stop and remove containers
docker compose down
```

Application will be available on <http://localhost:8000>.

The database file persists in the named Docker volume `sqlite-data`.

## Docker (single container) usage

```bash
# Build image
$ docker build -t complaints-api .

# Run container
$ docker run --env-file .env -p 8000:8000 complaints-api
```

## Environment variables (.env)

| Variable | Description |
|----------|-------------|
| `APILAYER_API_KEY` | API key for APILayer Sentiment Analysis. |
| `OPENAI_API_KEY`   | Key for OpenAI Chat Completion (optional). |
| `DATABASE_URL`     | Any SQLAlchemy URL. For docker-compose set `sqlite:////data/db.sqlite3`. |

## API examples

```bash
# Create complaint
curl -X POST http://localhost:8000/complaints \
     -H "Content-Type: application/json" \
     -d '{"text": "Не приходит SMS-код"}'

# List open complaints from the last hour
curl "http://localhost:8000/complaints?status=open&from_timestamp=3600"

# Close a complaint
curl -X PATCH http://localhost:8000/complaints/1 -d '{"status": "closed"}' -H "Content-Type: application/json"
```

## n8n workflow outline

1. **Schedule Trigger** – every hour.
2. **HTTP Request** – GET `/complaints?status=open&from_timestamp=3600`.
3. **IF node** – branch by `category` field.
4. **Telegram node** (category=`technical`) – send message.
5. **Google Sheets node** (category=`payment`) – append row with `timestamp`, `text`, `sentiment`.
6. **HTTP Request** – PATCH `/complaints/{id}` with `{ "status": "closed" }`.

Provide an `.env` with `TELEGRAM_BOT_TOKEN` and Google service account JSON in n8n credentials.
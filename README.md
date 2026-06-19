# EzPaper

EzPaper is a web application for uploading scientific papers, extracting their content, and explaining each section in an easier-to-understand way.

## Project Structure

```txt
EzPaper/
  backend/
  frontend/
  docker-compose.yml
  README.md
```

## Local Services

Start PostgreSQL and Redis:

```bash
docker compose up -d
```

Stop services:

```bash
docker compose down
```

Database connection for local development:

```txt
Host: localhost
Port: 5432
Database: ezpaper
User: ezpaper
Password: ezpaper
```

## Backend

Create a virtual environment:

```bash
cd backend
python -m venv .venv
```

Activate it on Windows PowerShell:

```powershell
.\.venv\Scripts\Activate.ps1
```

Install dependencies:

```bash
pip install -r requirements.txt
```

Install development dependencies:

```bash
pip install -r requirements-dev.txt
```

Create a local environment file:

```bash
copy .env.example .env
```

Run the API:

```bash
uvicorn app.main:app --reload
```

Health checks:

```txt
http://localhost:8000/health
http://localhost:8000/health/db
http://localhost:8000/docs
```

Run database migrations:

```bash
alembic upgrade head
```

Run backend tests:

```bash
pytest
```

Authentication endpoints:

```txt
POST /auth/register
POST /auth/login
POST /auth/token
GET /auth/me
```

Paper endpoints:

```txt
POST /papers/upload
GET /papers
GET /papers/{paper_id}
POST /papers/{paper_id}/analyze
DELETE /papers/{paper_id}
```

After upload, EzPaper extracts text from text-based PDFs and stores detected sections in `paper_sections`.
The current analyzer is a local heuristic MVP that fills `summary_vi` and `explanation_vi`; it is designed to be replaced by an AI provider later.

Optional OpenAI-backed analysis:

```txt
AI_PROVIDER=auto
OPENAI_API_KEY=your_api_key_here
OPENAI_MODEL=gpt-5.5
```

When `OPENAI_API_KEY` is empty, EzPaper keeps using the local analyzer.
After changing `.env`, restart the FastAPI server.

AI diagnostics:

```txt
GET /ai/status
POST /ai/test
```

`GET /ai/status` does not call OpenAI. `POST /ai/test` makes a small OpenAI request and confirms whether the key/model can be used.

## Frontend

Install dependencies:

```bash
cd frontend
npm install
```

Run the frontend:

```bash
npm run dev
```

Open:

```txt
http://localhost:3000
```

The frontend expects the API at:

```txt
http://127.0.0.1:8000
```

Override it with:

```txt
NEXT_PUBLIC_API_BASE_URL=http://127.0.0.1:8000
```

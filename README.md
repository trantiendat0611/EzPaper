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

PDF extraction and AI analysis run as background jobs on Celery (using the Redis
service from `docker compose`). Start a worker in a separate terminal:

```bash
celery -A app.core.celery_app worker --loglevel=info
```

On Windows, add `--pool=solo` if the default worker pool fails to start:

```bash
celery -A app.core.celery_app worker --loglevel=info --pool=solo
```

Uploading a paper returns immediately with status `uploaded`; the worker then
moves it to `processing` and `completed`. Requesting analysis returns status
`analyzing` and the worker finishes it as `analyzed`. The frontend polls for
these status changes automatically.

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
GET /papers/stats
GET /papers/{paper_id}
POST /papers/{paper_id}/analyze
POST /papers/{paper_id}/sections/{section_id}/analyze
GET /papers/{paper_id}/questions
POST /papers/{paper_id}/ask
DELETE /papers/{paper_id}
```

`GET /papers` supports `page`, `page_size`, `search`, and `status` query parameters.
`POST /papers/{paper_id}/ask` answers a free-form question grounded in the paper's
extracted content using the configured AI provider (Gemini, then OpenAI, then a
local keyword-retrieval fallback), and stores the Q&A history.

After upload, EzPaper extracts text from text-based PDFs and stores detected sections in `paper_sections`.
The current analyzer is a local heuristic MVP that fills `summary_vi` and `explanation_vi`; it is designed to be replaced by an AI provider later.

Optional OCR for scanned (image-only) PDFs:

When pypdf extracts too little text, EzPaper falls back to OCR. This needs two
system binaries installed (in addition to the Python packages in
`requirements.txt`):

- Tesseract OCR: https://github.com/UB-Mannheim/tesseract/wiki (Windows) or `apt-get install tesseract-ocr` (Linux)
- Poppler: https://github.com/oschwartz10612/poppler-windows (Windows) or `apt-get install poppler-utils` (Linux)

If either binary is missing, OCR is skipped and the paper is marked `failed`
when no text could be extracted. Text-based PDFs work without these binaries.

Optional AI-backed analysis (Gemini or OpenAI):

```txt
AI_PROVIDER=auto
GEMINI_API_KEY=your_api_key_here
GEMINI_MODEL=gemini-2.5-flash
OPENAI_API_KEY=your_api_key_here
OPENAI_MODEL=gpt-5.5
```

Set `AI_PROVIDER` to `gemini` or `openai` to force a provider, or leave it as `auto` to prefer
Gemini, then OpenAI, then fall back to the local analyzer based on which API key is set.
When neither key is set, EzPaper keeps using the local analyzer.
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

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
```

Run database migrations:

```bash
alembic upgrade head
```

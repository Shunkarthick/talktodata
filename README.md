# TalkToData - AI-Powered Text-to-SQL Analytics Platform

A professional, enterprise-ready chatbot UI that converts natural language questions into BigQuery SQL queries using Claude AI and LangChain.

## 🎯 Features

- **Natural Language to SQL**: Ask questions in plain English, get BigQuery SQL
- **Three-Tier Memory System**:
  - Global instructions (system-level SQL best practices)
  - Project memory (business rules, domain knowledge)
  - Conversation context (chat history)
- **BigQuery Integration**: Direct connection to your BigQuery datasets
- **Beautiful Visualizations**: Apache ECharts-powered charts and graphs
- **Admin Dashboard**: Track queries, API usage, errors, and performance
- **API-First Design**: Use via web UI, mobile app, or direct API calls
- **Future-Ready**: Built with LangChain for advanced agentic capabilities

## 🏗️ Architecture

```
Frontend (React + TypeScript)
    ↓
Backend (FastAPI + Python)
    ↓
LangChain (Text-to-SQL with Memory)
    ↓
Claude API (Anthropic)
    ↓
BigQuery (Google Cloud)
```

## 📋 Prerequisites

### Windows Setup

1. **Python 3.11+**
   - Download from: https://www.python.org/downloads/
   - During installation, check "Add Python to PATH"
   - Verify: `python --version`

2. **Node.js 18+**
   - Download from: https://nodejs.org/
   - Verify: `node --version` and `npm --version`

3. **PostgreSQL 15+**
   - Download from: https://www.postgresql.org/download/windows/
   - During installation, remember your postgres password
   - Default port: 5432
   - Verify: `psql --version`

4. **Git**
   - Download from: https://git-scm.com/download/win
   - Verify: `git --version`

5. **API Keys**
   - Anthropic API key from: https://console.anthropic.com/
   - Google Cloud service account for BigQuery

## 🚀 Quick Start (Windows)

### Step 1: Clone the Repository

```powershell
# Already in the repository
cd C:\path\to\talktodata
```

### Step 2: Set Up PostgreSQL Database

```powershell
# Open PowerShell as Administrator

# Connect to PostgreSQL
psql -U postgres

# In psql prompt:
CREATE DATABASE talktodata;
CREATE USER talktodata WITH PASSWORD 'talktodata123';
GRANT ALL PRIVILEGES ON DATABASE talktodata TO talktodata;
\q
```

### Step 3: Set Up Python Backend

```powershell
# Navigate to backend directory
cd backend

# Create virtual environment
python -m venv venv

# Activate virtual environment
.\venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt

# Create .env file from example
copy .env.example .env

# Edit .env file with your settings
notepad .env
```

**Important: Edit `.env` file with your credentials:**

```env
# Database
DATABASE_URL=postgresql://talktodata:talktodata123@localhost:5432/talktodata

# Anthropic API
ANTHROPIC_API_KEY=your-actual-anthropic-api-key-here

# Security (generate a secure key)
SECRET_KEY=your-super-secret-key-at-least-32-characters-long

# Admin (change these!)
ADMIN_EMAIL=admin@yourdomain.com
ADMIN_PASSWORD=ChangeThisPassword123!
```

### Step 4: Initialize Database

```powershell
# Make sure you're in backend directory with venv activated

# Create initial migration
alembic revision --autogenerate -m "Initial migration"

# Apply migration
alembic upgrade head

# Verify tables were created
psql -U talktodata -d talktodata -c "\dt"
```

### Step 5: Start Backend Server

```powershell
# In backend directory with venv activated
python -m app.main

# Or use uvicorn directly
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

You should see:
```
INFO:     Uvicorn running on http://0.0.0.0:8000
INFO:     Application startup complete.
```

**Test the API:**
- Open browser: http://localhost:8000
- API Docs: http://localhost:8000/api/docs
- Health check: http://localhost:8000/health

### Step 6: Set Up React Frontend (Coming next)

```powershell
# Open a NEW PowerShell window
cd C:\path\to\talktodata\frontend

# Install dependencies
npm install

# Start development server
npm run dev
```

## 📖 API Usage

### 1. Register a User

```powershell
# Using curl (Git Bash) or Invoke-RestMethod (PowerShell)

# PowerShell:
$body = @{
    email = "user@example.com"
    password = "SecurePassword123!"
    full_name = "John Doe"
} | ConvertTo-Json

Invoke-RestMethod -Uri "http://localhost:8000/api/v1/auth/register" `
    -Method POST `
    -Body $body `
    -ContentType "application/json"
```

### 2. Login

```powershell
$body = @{
    email = "user@example.com"
    password = "SecurePassword123!"
} | ConvertTo-Json

$response = Invoke-RestMethod -Uri "http://localhost:8000/api/v1/auth/login" `
    -Method POST `
    -Body $body `
    -ContentType "application/json"

# Save the token
$token = $response.access_token
```

### 3. Create a Project

```powershell
$headers = @{
    "Authorization" = "Bearer $token"
    "Content-Type" = "application/json"
}

$body = @{
    name = "My Analytics Project"
    description = "Sales and customer analytics"
    bigquery_project_id = "my-gcp-project"
    bigquery_dataset = "analytics"
} | ConvertTo-Json

$project = Invoke-RestMethod -Uri "http://localhost:8000/api/v1/projects" `
    -Method POST `
    -Headers $headers `
    -Body $body

$projectId = $project.id
```

### 4. Connect BigQuery

```powershell
# Read your service account JSON file
$credentials = Get-Content -Path "path\to\service-account.json" -Raw

$body = @{
    credentials_json = $credentials
} | ConvertTo-Json

Invoke-RestMethod -Uri "http://localhost:8000/api/v1/projects/$projectId/bigquery/connect" `
    -Method POST `
    -Headers $headers `
    -Body $body
```

### 5. Ask a Question

```powershell
$body = @{
    project_id = $projectId
    question = "What were the top 10 products by revenue last month?"
    model = "claude-3-5-sonnet-20241022"
} | ConvertTo-Json

$result = Invoke-RestMethod -Uri "http://localhost:8000/api/v1/queries/ask" `
    -Method POST `
    -Headers $headers `
    -Body $body

# View the generated SQL
$result.sql

# View the results
$result.result.rows
```

## 🗂️ Project Structure

```
talktodata/
├── backend/                    # Python FastAPI backend
│   ├── app/
│   │   ├── api/v1/            # API endpoints
│   │   ├── core/              # Config, security, logging
│   │   ├── db/                # Database setup
│   │   ├── models/            # SQLAlchemy models
│   │   ├── schemas/           # Pydantic schemas
│   │   ├── services/          # Business logic
│   │   │   ├── langchain/    # LangChain integration
│   │   │   └── bigquery/     # BigQuery service
│   │   └── main.py           # FastAPI app
│   ├── alembic/              # Database migrations
│   ├── requirements.txt      # Python dependencies
│   └── .env                  # Configuration
│
├── frontend/                  # React TypeScript frontend
│   ├── src/
│   │   ├── components/       # React components
│   │   ├── pages/            # Page components
│   │   ├── services/         # API client
│   │   └── App.tsx           # Main app
│   └── package.json          # Node dependencies
│
└── README.md                 # This file
```

## 🔧 Configuration

### Environment Variables

Edit `backend/.env`:

| Variable | Description | Example |
|----------|-------------|---------|
| `DATABASE_URL` | PostgreSQL connection string | `postgresql://user:pass@localhost/db` |
| `ANTHROPIC_API_KEY` | Claude API key | `sk-ant-...` |
| `SECRET_KEY` | JWT secret (32+ chars) | `your-secret-key` |
| `ADMIN_EMAIL` | Admin user email | `admin@example.com` |
| `ADMIN_PASSWORD` | Admin password | `SecurePass123!` |

### Database Migrations

```powershell
# Create a new migration after model changes
alembic revision --autogenerate -m "Description of changes"

# Apply migrations
alembic upgrade head

# Rollback last migration
alembic downgrade -1

# View migration history
alembic history
```

## 🧪 Testing

```powershell
# Run tests
cd backend
pytest

# Run with coverage
pytest --cov=app tests/
```

## 🐛 Troubleshooting

### PostgreSQL Connection Issues

```powershell
# Check if PostgreSQL is running
Get-Service postgresql*

# Start PostgreSQL service
Start-Service postgresql-x64-15  # or your version
```

### Python Import Errors

```powershell
# Make sure virtual environment is activated
.\venv\Scripts\activate

# Reinstall dependencies
pip install -r requirements.txt --force-reinstall
```

### Port Already in Use

```powershell
# Find process using port 8000
netstat -ano | findstr :8000

# Kill the process (replace PID)
taskkill /PID <PID> /F
```

## 📊 Admin Dashboard

Access admin features at:
- Query logs: `GET /api/v1/admin/logs/queries`
- API usage: `GET /api/v1/admin/usage/api`
- Error logs: `GET /api/v1/admin/logs/errors`

(Requires superuser account)

## 🔐 Security

- All BigQuery credentials are encrypted
- JWT-based authentication
- API key support for programmatic access
- SQL injection prevention (no DROP/DELETE/UPDATE allowed)
- Read-only BigQuery access recommended

## 🚀 Deployment

### Local Production Mode

```powershell
# Backend
cd backend
$env:ENVIRONMENT="production"
$env:DEBUG="False"
uvicorn app.main:app --host 0.0.0.0 --port 8000 --workers 4

# Frontend
cd frontend
npm run build
# Serve the dist folder with a static server
```

## 📝 License

MIT License - See LICENSE file

## 🤝 Support

For issues and questions:
- Check the logs in `backend/logs/app.log`
- Review API docs at http://localhost:8000/api/docs
- Check database with `psql -U talktodata -d talktodata`

## 🎯 Next Steps

1. ✅ Backend is ready
2. 🔄 Create React frontend components
3. 🔄 Add Apache ECharts visualizations
4. 🔄 Build admin dashboard
5. 🔄 Add mobile app support

---

**Built with**: Python, FastAPI, LangChain, Claude AI, BigQuery, React, TypeScript, Apache ECharts

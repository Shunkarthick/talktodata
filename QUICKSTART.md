# 🚀 Quick Start Guide

Get TalkToData running in 10 minutes!

## Prerequisites

- Windows 10/11
- Python 3.11+
- PostgreSQL 15+
- Anthropic API Key

## Setup Steps

### 1. Install PostgreSQL (if not installed)

Download and install: https://www.postgresql.org/download/windows/

Remember your postgres password!

### 2. Create Database

```powershell
# Open PowerShell as Administrator
psql -U postgres -c "CREATE DATABASE talktodata;"
psql -U postgres -c "CREATE USER talktodata WITH PASSWORD 'talktodata123';"
psql -U postgres -c "GRANT ALL PRIVILEGES ON DATABASE talktodata TO talktodata;"
```

### 3. Set Up Backend

```powershell
cd backend

# Create virtual environment
python -m venv venv

# Activate it
.\venv\Scripts\Activate.ps1

# Install dependencies
pip install -r requirements.txt

# Configure environment
copy .env.example .env
notepad .env  # Add your ANTHROPIC_API_KEY
```

**Important:** Edit `.env` and add your Anthropic API key:
```
ANTHROPIC_API_KEY=sk-ant-your-key-here
```

### 4. Initialize Database

```powershell
# Still in backend directory with venv activated
alembic revision --autogenerate -m "Initial"
alembic upgrade head
```

### 5. Start Server

```powershell
python -m app.main
```

Visit: http://localhost:8000/api/docs

### 6. Create Your First User

Open http://localhost:8000/api/docs in your browser:

1. Find **POST /api/v1/auth/register**
2. Click "Try it out"
3. Enter:
   ```json
   {
     "email": "you@example.com",
     "password": "YourPassword123!",
     "full_name": "Your Name"
   }
   ```
4. Click "Execute"

### 7. Login

1. Find **POST /api/v1/auth/login**
2. Click "Try it out"
3. Enter your email and password
4. Copy the `access_token` from response

### 8. Authorize

1. Click the "Authorize" button at top of page
2. Paste your token
3. Click "Authorize"

### 9. Create a Project

1. Find **POST /api/v1/projects**
2. Click "Try it out"
3. Enter:
   ```json
   {
     "name": "My Analytics Project",
     "description": "Testing TalkToData"
   }
   ```
4. Execute and copy the project `id`

### 10. Connect BigQuery (Optional)

If you have BigQuery:

1. Find **POST /api/v1/projects/{project_id}/bigquery/connect**
2. Paste your project ID
3. Upload your service account JSON
4. Execute

### 11. Ask a Question!

1. Find **POST /api/v1/queries/ask**
2. Enter:
   ```json
   {
     "project_id": "your-project-id",
     "question": "Show me top 10 customers by revenue",
     "model": "claude-3-5-sonnet-20241022"
   }
   ```
3. Execute

You'll get:
- Generated SQL
- Query results
- Execution metrics
- Chart suggestions

## 🎉 Success!

You now have:
- ✅ Running backend API
- ✅ Database configured
- ✅ User account created
- ✅ Project set up
- ✅ Ready to ask questions!

## Next Steps

- Connect your BigQuery data
- Use the API from your own applications
- Build the React frontend
- Set up admin dashboard
- Configure project memory and instructions

## Troubleshooting

**PostgreSQL not starting?**
```powershell
Get-Service postgresql*
Start-Service postgresql-x64-15
```

**Port 8000 in use?**
```powershell
# Use different port
uvicorn app.main:app --port 8001
```

**Need help?**
Check `backend/logs/app.log`

---

**Full documentation:** See [SETUP_WINDOWS.md](SETUP_WINDOWS.md)

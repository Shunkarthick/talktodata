# Windows Setup Guide for TalkToData

Step-by-step guide for setting up TalkToData on Windows.

## ✅ Prerequisites Checklist

Before you begin, install these:

- [ ] Python 3.11+ (https://www.python.org/downloads/)
- [ ] Node.js 18+ (https://nodejs.org/)
- [ ] PostgreSQL 15+ (https://www.postgresql.org/download/windows/)
- [ ] Git (https://git-scm.com/download/win)
- [ ] Anthropic API Key (https://console.anthropic.com/)
- [ ] Google Cloud Service Account for BigQuery

## 🎬 Step-by-Step Setup

### 1. Verify Installations

Open **PowerShell** or **Command Prompt** and verify:

```powershell
python --version      # Should show Python 3.11.x or higher
node --version        # Should show v18.x.x or higher
npm --version         # Should show 9.x.x or higher
psql --version        # Should show 15.x or higher
git --version         # Should show 2.x.x or higher
```

### 2. Set Up PostgreSQL Database

**Option A: Using pgAdmin (GUI)**
1. Open pgAdmin 4 (installed with PostgreSQL)
2. Right-click "Databases" → "Create" → "Database"
3. Name: `talktodata`
4. Click "Save"

**Option B: Using Command Line**

Open **PowerShell as Administrator**:

```powershell
# Set password environment variable for convenience (optional)
$env:PGPASSWORD = "your_postgres_password"

# Create database and user
psql -U postgres -c "CREATE DATABASE talktodata;"
psql -U postgres -c "CREATE USER talktodata WITH PASSWORD 'talktodata123';"
psql -U postgres -c "GRANT ALL PRIVILEGES ON DATABASE talktodata TO talktodata;"

# Verify
psql -U postgres -l  # Should list talktodata database
```

### 3. Configure Backend

Navigate to backend directory:

```powershell
cd path\to\talktodata\backend
```

Create virtual environment:

```powershell
python -m venv venv
```

Activate virtual environment:

```powershell
# PowerShell:
.\venv\Scripts\Activate.ps1

# Command Prompt:
.\venv\Scripts\activate.bat

# You should see (venv) in your prompt
```

Install Python packages:

```powershell
pip install --upgrade pip
pip install -r requirements.txt
```

Create environment file:

```powershell
copy .env.example .env
```

Edit `.env` file:

```powershell
notepad .env
```

Update these values in `.env`:

```env
# Database (update if you used different credentials)
DATABASE_URL=postgresql://talktodata:talktodata123@localhost:5432/talktodata

# IMPORTANT: Add your Anthropic API key
ANTHROPIC_API_KEY=sk-ant-api03-your-actual-key-here

# Generate a secure secret key (or use this command to generate one)
SECRET_KEY=use-python-secrets-token-urlsafe-32-to-generate

# Admin credentials (change these!)
ADMIN_EMAIL=admin@yourdomain.com
ADMIN_PASSWORD=YourSecurePassword123!
```

**Generate a secure SECRET_KEY:**

```powershell
python -c "import secrets; print(secrets.token_urlsafe(32))"
```

### 4. Initialize Database

Run migrations:

```powershell
# Create initial migration
alembic revision --autogenerate -m "Initial migration"

# Apply migration
alembic upgrade head
```

Verify tables were created:

```powershell
psql -U talktodata -d talktodata -c "\dt"
```

You should see tables like: users, projects, conversations, etc.

### 5. Start Backend Server

```powershell
# Make sure venv is activated (you should see (venv) in prompt)
python -m app.main
```

You should see output like:

```
INFO:     Started server process
INFO:     Waiting for application startup.
INFO:     Application startup complete.
INFO:     Uvicorn running on http://0.0.0.0:8000 (Press CTRL+C to quit)
```

**Test the backend:**

Open your browser and visit:
- http://localhost:8000 - Root endpoint
- http://localhost:8000/api/docs - Interactive API documentation (Swagger UI)
- http://localhost:8000/health - Health check

### 6. Test API with PowerShell

Open a **NEW PowerShell window** (keep the server running in the first one):

```powershell
# Test health endpoint
Invoke-RestMethod -Uri "http://localhost:8000/health"

# Register a user
$body = @{
    email = "test@example.com"
    password = "TestPassword123!"
    full_name = "Test User"
} | ConvertTo-Json

$response = Invoke-RestMethod -Uri "http://localhost:8000/api/v1/auth/register" `
    -Method POST `
    -Body $body `
    -ContentType "application/json"

Write-Host "User created with ID: $($response.id)"

# Login
$loginBody = @{
    email = "test@example.com"
    password = "TestPassword123!"
} | ConvertTo-Json

$loginResponse = Invoke-RestMethod -Uri "http://localhost:8000/api/v1/auth/login" `
    -Method POST `
    -Body $loginBody `
    -ContentType "application/json"

$token = $loginResponse.access_token
Write-Host "Login successful! Token: $token"

# Create a project
$headers = @{
    "Authorization" = "Bearer $token"
    "Content-Type" = "application/json"
}

$projectBody = @{
    name = "Test Project"
    description = "My first analytics project"
} | ConvertTo-Json

$project = Invoke-RestMethod -Uri "http://localhost:8000/api/v1/projects" `
    -Method POST `
    -Headers $headers `
    -Body $projectBody

Write-Host "Project created with ID: $($project.id)"
```

## 🔧 Common Issues & Solutions

### Issue: "psql is not recognized"

**Solution:** Add PostgreSQL to PATH

```powershell
# Add to PATH (replace XX with your PostgreSQL version)
$env:Path += ";C:\Program Files\PostgreSQL\15\bin"
```

Or add permanently:
1. Search "Environment Variables" in Windows
2. Edit "Path" under System variables
3. Add: `C:\Program Files\PostgreSQL\15\bin`

### Issue: "python is not recognized"

**Solution:** Reinstall Python and check "Add to PATH" during installation

### Issue: "Cannot activate virtual environment"

**Solution:** Enable script execution

```powershell
# Run as Administrator
Set-ExecutionPolicy -ExecutionPolicy RemoteSigned -Scope CurrentUser
```

### Issue: Database connection failed

**Solution:** Check PostgreSQL service

```powershell
# Check status
Get-Service postgresql*

# Start service
Start-Service postgresql-x64-15  # Replace with your version
```

### Issue: Port 8000 already in use

**Solution:** Kill the process or use a different port

```powershell
# Find process
netstat -ano | findstr :8000

# Kill process (replace PID)
taskkill /PID <PID> /F

# Or use different port
uvicorn app.main:app --port 8001
```

## 📋 Next Steps

1. ✅ Backend is running
2. Set up BigQuery:
   - Create a Google Cloud project
   - Enable BigQuery API
   - Create a service account
   - Download JSON key file
3. Connect BigQuery via API:
   ```powershell
   # Use the API docs at http://localhost:8000/api/docs
   # or the PowerShell examples above
   ```
4. Frontend setup (coming next)

## 🎯 Quick Commands Reference

```powershell
# Start backend (in backend directory with venv activated)
python -m app.main

# Create database migration
alembic revision --autogenerate -m "description"

# Apply migrations
alembic upgrade head

# Rollback migration
alembic downgrade -1

# Open API docs
start http://localhost:8000/api/docs

# Check database
psql -U talktodata -d talktodata

# View logs
Get-Content backend\logs\app.log -Tail 50
```

## ✅ Verification Checklist

- [ ] PostgreSQL database created
- [ ] Python virtual environment activated
- [ ] Dependencies installed
- [ ] .env file configured with API keys
- [ ] Database migrations applied
- [ ] Backend server starts without errors
- [ ] Can access http://localhost:8000/api/docs
- [ ] Can register and login via API
- [ ] Can create projects via API

## 🎉 Success!

If all checks pass, your backend is ready! You can now:
- Use the API directly via http://localhost:8000/api/docs
- Build the frontend
- Connect your BigQuery data
- Start asking questions!

---

**Need help?** Check `backend/logs/app.log` for detailed error messages.

# AI Civilization Builder Local Installer
# This script sets up the local development environment (Python venv, NPM packages, Ollama checks) without Docker.

Write-Host "==================================================" -ForegroundColor Cyan
Write-Host "Initializing AI Civilization Builder Local Installer" -ForegroundColor Cyan
Write-Host "==================================================" -ForegroundColor Cyan

# 1. Setup Python Virtual Environment
Write-Host "`n[1/3] Setting up Python virtual environment..." -ForegroundColor Yellow
if (-not (Test-Path "backend\.venv")) {
    Start-Process python -ArgumentList "-m venv backend\.venv" -NoNewWindow -Wait
    Write-Host "Virtual environment created at backend\.venv" -ForegroundColor Green
} else {
    Write-Host "Python virtual environment already exists." -ForegroundColor Gray
}

Write-Host "Installing python dependencies..." -ForegroundColor Gray
& backend\.venv\Scripts\pip install --upgrade pip
& backend\.venv\Scripts\pip install -r backend\requirements.txt

# 2. Setup Node.js Packages
Write-Host "`n[2/3] Installing frontend dependencies..." -ForegroundColor Yellow
if (Test-Path "frontend\package.json") {
    Push-Location frontend
    npm install
    Pop-Location
    Write-Host "Frontend packages installed successfully." -ForegroundColor Green
} else {
    Write-Error "Could not find frontend\package.json"
}

# 3. Verify Local Ollama System
Write-Host "`n[3/3] Verifying Local Ollama Instance..." -ForegroundColor Yellow
try {
    $response = Invoke-RestMethod -Uri "http://localhost:11434/api/tags" -Method Get -ErrorAction Stop
    Write-Host "Ollama connection verified. Found models: " -ForegroundColor Green -NoNewline
    Write-Host ($response.models | Select-Object -ExpandProperty name) -ForegroundColor Gray
} catch {
    Write-Host "WARNING: Could not connect to local Ollama instance (http://localhost:11434)." -ForegroundColor Yellow
    Write-Host "AI reasoning loop will default to rule-based behavioral heuristics." -ForegroundColor Yellow
    Write-Host "To enable cognitive AI citizen reasoning, please install Ollama (https://ollama.com/) and run 'ollama run llama3'." -ForegroundColor Gray
}

Write-Host "`nSetup Complete!" -ForegroundColor Green
Write-Host "--------------------------------------------------" -ForegroundColor Cyan
Write-Host "To start the backend server:" -ForegroundColor Gray
Write-Host "  cd backend" -ForegroundColor Yellow
Write-Host "  .venv\Scripts\python -m uvicorn app.main:app --reload --port 8000" -ForegroundColor Yellow
Write-Host "To start the frontend server:" -ForegroundColor Gray
Write-Host "  cd frontend" -ForegroundColor Yellow
Write-Host "  npm run dev" -ForegroundColor Yellow
Write-Host "--------------------------------------------------" -ForegroundColor Cyan

# One command: API (:8000) + React web app (:5173). -Streamlit runs the Streamlit fallback (:8501).
# Run: powershell -ExecutionPolicy Bypass -File scripts/dev.ps1 [-Streamlit]
# Port overrides: $env:API_PORT, $env:WEB_PORT, $env:ST_PORT.
param([switch]$Streamlit)
$ErrorActionPreference = "Stop"
Set-Location (Join-Path $PSScriptRoot "..")

$ApiPort = if ($env:API_PORT) { $env:API_PORT } else { "8000" }
$WebPort = if ($env:WEB_PORT) { $env:WEB_PORT } else { "5173" }
$StPort  = if ($env:ST_PORT)  { $env:ST_PORT }  else { "8501" }

if (-not (Test-Path ".venv\Scripts\python.exe")) {
    Write-Host "Creating .venv and installing requirements..."
    python -m venv .venv
    & .venv\Scripts\pip.exe install -r requirements.txt
}

if ($Streamlit) {
    Write-Host "Streamlit fallback: http://localhost:$StPort"
    & .venv\Scripts\streamlit.exe run app.py --server.port $StPort --server.headless true
    exit $LASTEXITCODE
}

if (-not (Test-Path "web\package.json")) {
    Write-Host "React UI not on this branch yet; use -Streamlit"
    exit 1
}
if (-not (Test-Path "web\node_modules")) {
    Write-Host "Installing web dependencies..."
    npm --prefix web install
}

$api = Start-Process -FilePath ".venv\Scripts\uvicorn.exe" -ArgumentList "server:app","--port",$ApiPort -NoNewWindow -PassThru
try {
    Write-Host "API: http://localhost:$ApiPort   Web: http://localhost:$WebPort"
    npm --prefix web run dev -- --port $WebPort
}
finally {
    if ($api -and -not $api.HasExited) { Stop-Process -Id $api.Id -Force }
}

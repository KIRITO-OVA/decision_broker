@echo off
SETLOCAL EnableDelayedExpansion

echo ==========================================
echo    DECISION BROKER - STARTUP SEQUENCE
echo ==========================================

:: Set PYTHONPATH to parent directory to allow "import decision_broker"
set "PYTHONPATH=%PYTHONPATH%;%~dp0.."

:: Check if .env exists
if not exist "%~dp0.env" (
    echo [WARNING] .env file not found. 
    echo Please copy .env.template to .env and fill in your credentials.
    pause
    exit /b
)

echo [INFO] Environment configured.
echo [INFO] Starting API Server on http://localhost:8000
echo [INFO] Press Ctrl+C to stop the server.
echo.

:: Start the server
python -m uvicorn decision_broker.api.server:app --port 8000 --reload

echo.
echo [INFO] Server stopped.
pause

@echo off
REM Startup script for the College FAQ Chatbot Streamlit Dashboard

echo.
echo ============================================================
echo College FAQ Chatbot - Streamlit Dashboard
echo ============================================================
echo.

cd /d "%~dp0"

REM Check if venv exists
if not exist "venv" (
    echo ERROR: Virtual environment not found!
    echo Please run: python -m venv venv
    pause
    exit /b 1
)

echo Activating virtual environment...
call venv\Scripts\activate.bat

if errorlevel 1 (
    echo ERROR: Failed to activate virtual environment
    pause
    exit /b 1
)

echo.
echo Starting Streamlit dashboard...
echo Dashboard will be available at: http://localhost:8501
echo.
echo Press Ctrl+C to stop the server
echo.

python -m streamlit run streamlit_ui/dashboard.py

if errorlevel 1 (
    echo.
    echo ERROR: Failed to start dashboard
    pause
    exit /b 1
)

pause

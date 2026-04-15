@echo off
color 0B
title Patel Store Server Launcher

echo =======================================================
echo.
echo      PATEL STORE MANAGEMENT SYSTEM
echo.
echo =======================================================
echo.
echo [1] Activating virtual environment...
if exist "venv\Scripts\activate.bat" (
    call venv\Scripts\activate.bat
    echo     - venv activated successfully.
) else (
    echo     - WARNING: venv not found.
)
echo.

echo [2] Launching browser in background...
start "" cmd /c "timeout /t 5 >nul & start http://127.0.0.1:8000/"

echo [3] Starting Django Development Server...
echo     - Server running at http://127.0.0.1:8000/
echo     - Press Ctrl+C to stop the server.
echo.
echo =======================================================
if exist "venv\Scripts\python.exe" (
    .\venv\Scripts\python.exe manage.py runserver
) else (
    python manage.py runserver
)

pause

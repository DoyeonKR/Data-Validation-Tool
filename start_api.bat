@echo off
chcp 65001 >nul
cls
echo ============================================
echo    Engine Data Validation API Server
echo    Made by SV dykim - Neurophet
echo ============================================
echo.

REM Move to project directory
cd /d "C:\Users\Neurophet\PycharmProjects\backup"
echo [INFO] Project directory: %cd%
echo.

REM Check and activate virtual environment
if exist "venv\Scripts\activate.bat" (
    echo [INFO] Activating virtual environment...
    call venv\Scripts\activate.bat
    echo [SUCCESS] Virtual environment activated
) else (
    echo [WARNING] Virtual environment not found. Using global Python.
)
echo.

REM Check Python version
echo [INFO] Python version check:
python --version
echo.

REM Check required packages
echo [INFO] Checking required packages...
python -c "import fastapi, pandas, openpyxl, requests; print('[SUCCESS] All required packages are installed.')" 2>nul
if errorlevel 1 (
    echo [WARNING] Some packages may be missing. Installing...
    pip install -r requirements.txt
)
echo.

REM Check ngrok status
echo [INFO] Checking ngrok tunnel status...
curl -s http://127.0.0.1:4040/api/tunnels >nul 2>&1
if errorlevel 1 (
    echo [WARNING] ngrok is not running. Teams notifications may not work.
    echo [TIP] Run 'ngrok http 9000' in another terminal.
) else (
    echo [SUCCESS] ngrok tunnel is active.
)
echo.

REM Start API server
echo [INFO] Starting API server...
echo [INFO] Server address: http://localhost:9000
echo [INFO] API docs: http://localhost:9000/docs
echo [INFO] Press Ctrl+C to stop.
echo ============================================
echo.

python api.py

REM Post-shutdown message
echo.
echo ============================================
echo [INFO] API server has been stopped.
echo ============================================
pause
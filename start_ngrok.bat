@echo off
echo ============================================
echo         ngrok Tunnel for API Server
echo ============================================
echo.

echo [INFO] API 서버용 ngrok 터널을 시작합니다...
echo [INFO] 포트: 9000
echo [INFO] 종료하려면 Ctrl+C를 누르세요.
echo.

ngrok http 9000

echo.
echo ============================================
echo [INFO] ngrok 터널이 종료되었습니다.
echo ============================================
pause


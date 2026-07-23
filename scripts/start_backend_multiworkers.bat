@echo off
chcp 65001 >nul
echo ============================================
echo   后端服务启动（多 Workers 模式）
echo ============================================
echo.
echo Workers: 4 个进程（利用多核 CPU）
echo 端口: 8000
echo.

cd /d "%~dp0..\backend"

:: 使用 4 个 worker 进程启动（适合 4 核 CPU）
:: 如果 CPU 核心数不同，请调整 --workers 参数
:: 推荐值: workers = CPU核心数 * 2 + 1
call venv\Scripts\uvicorn.exe app.main:app --host 0.0.0.0 --port 8000 --workers 4 --access-log

echo.
echo 后端服务已停止
pause

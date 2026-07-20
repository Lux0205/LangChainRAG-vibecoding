@echo off
chcp 65001 >nul
echo ============================================
echo   LangChain RAG 系统 - 一键启动
echo ============================================

:: 获取脚本所在目录
set "PROJECT_ROOT=%~dp0.."

echo.
echo [提示] 请确保以下服务已启动：
echo   - MySQL 8.0 (端口3306)
echo   - Redis (端口6379)
echo   - Milvus 2.x (端口19530)
echo.
echo 按任意键继续启动...
pause >nul

echo.
echo [1/2] 启动后端服务...
cd /d "%PROJECT_ROOT%\backend"
start "RAG Backend" cmd /c "call venv\Scripts\activate && python app\main.py"

echo 等待后端启动...
timeout /t 5 /nobreak >nul

echo.
echo [2/2] 启动前端服务...
cd /d "%PROJECT_ROOT%\frontend"
start "RAG Frontend" cmd /c "npm run dev"

echo.
echo ============================================
echo   系统启动中...
echo   前端: http://localhost:5173
echo   后端API: http://localhost:8000/docs
echo   管理员: admin / 123456
echo ============================================
echo.
echo 按任意键退出此窗口（服务将继续运行）...
pause >nul

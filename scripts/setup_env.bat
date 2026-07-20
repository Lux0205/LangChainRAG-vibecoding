@echo off
chcp 65001 >nul
echo ============================================
echo   LangChain RAG 系统 - 环境初始化
echo ============================================

echo.
echo [步骤1] 检查Python环境...
python --version
if errorlevel 1 (
    echo [错误] 未检测到Python，请先安装Python 3.10+
    pause
    exit /b 1
)

echo.
echo [步骤2] 创建Python虚拟环境...
cd ..\backend
if not exist venv (
    python -m venv venv
    echo [完成] 虚拟环境创建成功
) else (
    echo [跳过] 虚拟环境已存在
)

echo.
echo [步骤3] 安装Python依赖...
call venv\Scripts\activate
pip install -r requirements.txt
if errorlevel 1 (
    echo [错误] 依赖安装失败
    pause
    exit /b 1
)
echo [完成] Python依赖安装成功

echo.
echo [步骤4] 检查Node.js环境...
cd ..\frontend
node --version
if errorlevel 1 (
    echo [错误] 未检测到Node.js，请先安装Node.js 18+
    pause
    exit /b 1
)

echo.
echo [步骤5] 安装前端依赖...
npm install
if errorlevel 1 (
    echo [错误] 前端依赖安装失败
    pause
    exit /b 1
)
echo [完成] 前端依赖安装成功

echo.
echo [步骤6] 初始化数据库...
cd ..\backend
call venv\Scripts\activate
echo [提示] 请确保MySQL服务已启动
echo [提示] 请确保已创建数据库: CREATE DATABASE rag_db CHARACTER SET utf8mb4;
python init_data.py

echo.
echo ============================================
echo   环境初始化完成！
echo   运行 start_all.bat 启动系统
echo ============================================
pause

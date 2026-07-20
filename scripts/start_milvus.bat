@echo off
chcp 65001 >nul
echo ============================================
echo   Milvus 单机版启动脚本
echo ============================================
echo.
echo [提示] 请先下载Milvus单机版:
echo   https://github.com/milvus-io/milvus/releases
echo.
echo 将解压后的milvus目录放在项目根目录下
echo.

set "MILVUS_DIR=%~dp0..\milvus"

if not exist "%MILVUS_DIR%\bin\milvus.exe" (
    echo [错误] 未找到Milvus可执行文件
    echo 请下载Milvus并解压到项目milvus目录
    pause
    exit /b 1
)

echo 启动Milvus单机版...
cd /d "%MILVUS_DIR%"
bin\milvus run standalone

pause

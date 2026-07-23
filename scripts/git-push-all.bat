@echo off
chcp 65001 >nul
echo ===== 推送到 Gitee + GitHub =====

echo.
echo [1/2] 推送到 Gitee...
git push origin main
if %errorlevel% neq 0 (
    echo [错误] Gitee 推送失败！
    exit /b 1
)

echo.
echo [2/2] 推送到 GitHub...
set GIT_SSH_COMMAND=ssh -o StrictHostKeyChecking=accept-new -p 443
git push github main
if %errorlevel% neq 0 (
    echo [错误] GitHub 推送失败！
    exit /b 1
)

echo.
echo ===== 全部推送完成 =====
echo Gitee:  https://gitee.com/Lux0205/lang-chain-rag-vibecoding
echo GitHub: https://github.com/Lux0205/LangChainRAG-vibecoding

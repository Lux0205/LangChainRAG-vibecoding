@echo off
chcp 65001 >nul
echo ============================================
echo   压力测试 - 100并发用户
echo ============================================

set PYTHON=..\..\venv\Scripts\python.exe
set LOCUST=..\..\venv\Scripts\locust.exe

echo.
echo [1/3] 预注册测试用户...
%PYTHON% setup_users.py -n 100
if %errorlevel% neq 0 (
    echo [警告] 用户注册有失败，继续测试...
)

echo.
echo [2/3] 启动服务端监控（后台）...
start "Monitor" %PYTHON% monitor.py -d 80 -o results\monitor.csv

echo.
echo [3/3] 运行压力测试（100并发，60秒）...
echo 按 Ctrl+C 可提前结束
echo.

%LOCUST% -f locustfile.py --headless -u 100 -r 10 -t 60s --csv=results\stress --html=results\report.html

echo.
echo ============================================
echo   压力测试完成！
echo ============================================

echo.
echo 正在生成分析图表...
%PYTHON% analyze.py

echo.
echo 结果文件：
echo   - results\stress_stats.csv  （Locust统计数据）
echo   - results\monitor.csv      （服务端资源监控）
echo   - reports\monitor_chart.png （资源监控图表）
echo   - reports\summary_report.txt（摘要报告）
echo.

pause

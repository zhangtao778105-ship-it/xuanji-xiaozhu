@echo off
REM ============================
REM 玄机小筑 开机自启脚本
REM ============================

REM 1. 启动 Flask 后端（后台最小化）
cd /d D:\.ab工具\divination
start "玄机小筑-Flask" /min D:\Python314\python.exe D:\.ab工具\divination\app.py >> D:\.ab工具\divination\server.log 2>&1

REM 2. 等 Flask 就绪
timeout /t 3 /nobreak >nul

REM 3. 启动 natapp 隧道（如果 exe 存在）
if exist "D:\.ab工具\natapp\natapp.exe" (
    cd /d D:\.ab工具\natapp
    start "玄机小筑-natapp" /min D:\.ab工具\natapp\natapp.exe -config=D:\.ab工具\natapp\config.ini >> D:\.ab工具\natapp\natapp.log 2>&1
)

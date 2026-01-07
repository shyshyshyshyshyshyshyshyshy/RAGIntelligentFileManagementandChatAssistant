@echo off
chcp 65001 >nul
title 智能文件助手启动器

echo 正在启动智能文件助手...
echo.

REM 检查Python是否安装
python --version >nul 2>&1
if errorlevel 1 (
    echo 错误: 未找到Python，请先安装Python
    pause
    exit /b 1
)

REM 检查所需Python包
pip list | findstr "Flask" >nul
if errorlevel 1 (
    echo 安装所需依赖...
    pip install flask flask-cors
)

REM 使用VBS脚本静默启动
echo 启动服务中（无窗口模式）...
start wscript start_silent.vbs

echo 服务启动完成！浏览器将自动打开...
echo 如果浏览器没有自动打开，请手动访问: http://localhost:5002/
echo.
echo 按任意键关闭此窗口...
pause >nul
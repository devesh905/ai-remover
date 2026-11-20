@echo off
title AI & File Metadata Remover
cd /d "%~dp0"

REM If files are dragged and dropped onto this bat file:
if "%~1"=="" goto launch_gui

echo Cleaning dropped file(s)...
python metadata_cleaner.py %*
echo.
echo ==============================================
echo Cleaning complete! Press any key to exit.
echo ==============================================
pause
exit /b

:launch_gui
echo Starting AI & File Metadata Remover GUI...
start "" pythonw metadata_cleaner.py
exit /b

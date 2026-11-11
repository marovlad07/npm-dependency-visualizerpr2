@echo off
setlocal
cd /d "%~dp0"
set "PYTHONPATH=%~dp0src"
set "PYTHONUTF8=1"
if exist ".tools\python-path.txt" (
    set /p PYTHON_EXE=<".tools\python-path.txt"
    goto configured
)
where py >nul 2>nul
if not errorlevel 1 (
    py -3 -m npm_graph %*
    exit /b %errorlevel%
)
python -m npm_graph %*
exit /b %errorlevel%
:configured
"%PYTHON_EXE%" -m npm_graph %*
exit /b %errorlevel%

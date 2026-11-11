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
if not errorlevel 1 goto launcher
python -m unittest discover -s tests -v
exit /b %errorlevel%
:launcher
py -3 -m unittest discover -s tests -v
exit /b %errorlevel%
:configured
"%PYTHON_EXE%" -m unittest discover -s tests -v
exit /b %errorlevel%

@echo off
setlocal
cd /d "%~dp0"
call run.bat --package is-odd --version 3.0.1 --mode visualize --output generated/is-odd.svg --no-open
if errorlevel 1 goto failed
call run.bat --package is-even --version 1.0.0 --mode visualize --output generated/is-even.svg --no-open
if errorlevel 1 goto failed
call run.bat --package chalk --version 4.1.2 --mode visualize --output generated/chalk.svg --no-open
if errorlevel 1 goto failed
start "" "docs\gallery.html"
exit /b 0
:failed
echo See the error above and README.md.
pause
exit /b 1

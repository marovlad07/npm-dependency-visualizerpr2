@echo off
setlocal
cd /d "%~dp0"
echo Offline cycle example - no Internet required.
call run.bat --test --repository examples/cycle.json --package A --version 1.0.0 --mode visualize --output generated/cycle.png
if errorlevel 1 goto failed
echo.
echo Reverse dependencies in diamond example:
call run.bat --test --repository examples/diamond.json --package D --version 1.0.0 --mode reverse
echo.
pause
exit /b 0
:failed
echo.
echo See the error above and README.md.
pause
exit /b 1

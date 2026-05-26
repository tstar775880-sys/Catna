@echo off
setlocal

cd /d "%~dp0"

set "BASE_PORT=9000"

for /f %%P in ('powershell -NoProfile -Command "$p=%BASE_PORT%; while (Get-NetTCPConnection -LocalPort $p -ErrorAction SilentlyContinue) { $p++ }; Write-Output $p"') do set "PORT=%%P"

where python >nul 2>nul
if %errorlevel%==0 (
  set "PYTHON_CMD=python"
) else (
  where py >nul 2>nul
  if %errorlevel%==0 (
    set "PYTHON_CMD=py"
  ) else (
    echo Python was not found. Please install Python or add it to PATH.
    pause
    exit /b 1
  )
)

echo Starting local web server...
echo Folder: %cd%
echo URL: http://127.0.0.1:%PORT%/
echo.
echo Keep this window open while viewing the site.
echo Press Ctrl+C in this window to stop the server.
echo.

start "" /min cmd /c "timeout /t 1 /nobreak ^>nul ^& start "" http://127.0.0.1:%PORT%/"

%PYTHON_CMD% -m http.server %PORT% --bind 127.0.0.1

pause

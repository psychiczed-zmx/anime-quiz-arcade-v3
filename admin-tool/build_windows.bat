@echo off
setlocal
cd /d "%~dp0"

where py >nul 2>nul
if errorlevel 1 (
  echo ERROR: Python Launcher "py" was not found.
  echo Install Python 3.10 or newer from python.org, then reopen Command Prompt.
  pause
  exit /b 1
)

echo [1/3] Checking Python...
py -3 --version
if errorlevel 1 (
  echo ERROR: Python 3 could not be started with the py launcher.
  pause
  exit /b 1
)

echo [2/3] Installing PyInstaller...
py -3 -m pip install --upgrade pip
if errorlevel 1 goto :failed
py -3 -m pip install -r requirements.txt
if errorlevel 1 goto :failed

echo [3/3] Building AnimeQuizAdmin.exe...
py -3 -m PyInstaller --noconfirm --clean --onefile --windowed --name AnimeQuizAdmin quiz_admin.py
if errorlevel 1 goto :failed

if not exist "dist\AnimeQuizAdmin.exe" goto :failed

echo.
echo SUCCESS: %~dp0dist\AnimeQuizAdmin.exe
echo Keep the EXE in this project folder's admin-tool\dist directory so it can find data and assets.
pause
exit /b 0

:failed
echo.
echo ERROR: Build failed. Copy the error text above and send it for diagnosis.
pause
exit /b 1

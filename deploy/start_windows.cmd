@echo off
cd /d "%~dp0.."
if not exist ".venv\Scripts\python.exe" (
  echo First complete docs/QUICKSTART.md to create .venv and install requirements.
  exit /b 1
)
".venv\Scripts\python.exe" run.py

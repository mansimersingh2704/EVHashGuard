@echo off
echo Running EVHashGuard Tests...
cd /d "%~dp0..\backend"
python -m pytest tests/ -v --tb=short
pause

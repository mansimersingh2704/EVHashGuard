@echo off
echo Starting EVHashGuard Frontend...
cd /d "%~dp0..\frontend"
npm install
npm run dev
pause

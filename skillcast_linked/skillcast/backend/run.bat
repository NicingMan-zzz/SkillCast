@echo off
cd /d "%~dp0"
echo Installing packages...
py -m pip install -q -r requirements.txt
if not exist .env goto noenv
py check.py
echo.
echo Starting SkillCast at http://localhost:5000/   (close this window to stop)
start "" http://localhost:5000/
py api.py
goto end
:noenv
echo No .env file here. Copy .env.example to .env and put your key in it.
:end
pause

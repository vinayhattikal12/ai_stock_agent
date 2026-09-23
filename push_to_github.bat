@echo off
echo ====================================================
echo Uploading AI Stock Decision System to GitHub...
echo Target: https://github.com/vinayhattikal12/ai_stock_agent
echo ====================================================

REM 1. Initialize git if not done
if not exist ".git" (
    echo Initializing Git repository...
    git init
)

REM 2. Stage all files (respecting .gitignore)
echo Staging files...
git add .

REM 3. Commit
echo Creating commit...
git commit -m "feat: complete AI equity swing decision-support platform with institutional risk engine"

REM 4. Set main branch
git branch -M main

REM 5. Set remote origin
git remote remove origin 2>nul
git remote add origin https://github.com/vinayhattikal12/ai_stock_agent.git

REM 6. Push to GitHub
echo Pushing to GitHub main branch...
git push -u origin main --force

echo.
echo ====================================================
echo Upload complete!
echo Verify at: https://github.com/vinayhattikal12/ai_stock_agent
echo ====================================================
pause

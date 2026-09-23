Write-Host "====================================================" -ForegroundColor Cyan
Write-Host "Uploading AI Stock Decision System to GitHub..." -ForegroundColor Cyan
Write-Host "Target: https://github.com/vinayhattikal12/ai_stock_agent" -ForegroundColor Cyan
Write-Host "====================================================" -ForegroundColor Cyan

if (-not (Test-Path ".git")) {
    Write-Host "Initializing Git..." -ForegroundColor Yellow
    git init
}

Write-Host "Staging files..." -ForegroundColor Yellow
git add .

Write-Host "Creating commit..." -ForegroundColor Yellow
git commit -m "feat: complete AI equity swing decision-support platform with institutional risk engine"

Write-Host "Setting main branch..." -ForegroundColor Yellow
git branch -M main

try {
    git remote remove origin 2>$null
} catch {}

git remote add origin https://github.com/vinayhattikal12/ai_stock_agent.git

Write-Host "Pushing to GitHub..." -ForegroundColor Green
git push -u origin main --force

Write-Host "`nUpload complete! Verify at https://github.com/vinayhattikal12/ai_stock_agent" -ForegroundColor Green

# Data Cleaning App - Vercel Deployment (PowerShell)

Write-Host "🚀 Deploying Data Cleaning App to Vercel..." -ForegroundColor Green

# Check if Vercel CLI is installed
try {
    vercel --version | Out-Null
    Write-Host "✅ Vercel CLI found" -ForegroundColor Green
} catch {
    Write-Host "📦 Installing Vercel CLI..." -ForegroundColor Yellow
    npm install -g vercel
}

# Update API URLs for production
Write-Host "🔧 Updating API URLs..." -ForegroundColor Yellow
python update_api_urls.py

# Install dependencies
Write-Host "📦 Installing frontend dependencies..." -ForegroundColor Yellow
Set-Location frontend
npm install
Set-Location ..

# Build frontend
Write-Host "🏗️ Building frontend..." -ForegroundColor Yellow
Set-Location frontend
npm run build
Set-Location ..

# Deploy to Vercel
Write-Host "🚀 Deploying to Vercel..." -ForegroundColor Green
vercel --prod

Write-Host "✅ Deployment complete!" -ForegroundColor Green
Write-Host "📱 Your app will be available at the URL shown above" -ForegroundColor Cyan
Write-Host "🔗 Visit vercel.com/dashboard to manage your deployment" -ForegroundColor Cyan
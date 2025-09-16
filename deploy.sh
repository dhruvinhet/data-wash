#!/bin/bash

# Data Cleaning App - Vercel Deployment Script
echo "🚀 Deploying Data Cleaning App to Vercel..."

# Check if Vercel CLI is installed
if ! command -v vercel &> /dev/null; then
    echo "📦 Installing Vercel CLI..."
    npm install -g vercel
fi

# Update API URLs for production
echo "🔧 Updating API URLs..."
python update_api_urls.py

# Install dependencies
echo "📦 Installing frontend dependencies..."
cd frontend
npm install
cd ..

# Build frontend
echo "🏗️ Building frontend..."
cd frontend
npm run build
cd ..

# Deploy to Vercel
echo "🚀 Deploying to Vercel..."
vercel --prod

echo "✅ Deployment complete!"
echo "📱 Your app will be available at the URL shown above"
echo "🔗 Visit vercel.com/dashboard to manage your deployment"
# Data Cleaning Application - Vercel Deployment Guide

A comprehensive web application for data cleaning and analysis deployed on Vercel with serverless backend and React frontend.

## 🚀 Quick Deploy

[![Deploy with Vercel](https://vercel.com/button)](https://vercel.com/new/clone?repository-url=https://github.com/your-username/DataCleaning)

## 📁 Project Structure for Vercel

```
├── api/                    # Serverless Python functions
│   ├── index.py           # Main API handler for all routes
│   └── app.py             # Flask utilities and helpers
├── frontend/              # React application
│   ├── src/
│   │   ├── components/    # React components
│   │   ├── config.js      # API configuration (dev/prod)
│   │   └── ...
│   ├── build/            # Production build (auto-generated)
│   └── package.json
├── vercel.json            # Vercel deployment configuration
├── requirements.txt       # Python dependencies for serverless
├── package.json          # Root package.json for build
└── README-DEPLOYMENT.md   # This file
```

## ✨ Features Deployed

### Backend (Serverless Functions)
- ✅ File upload (CSV/Excel support)
- ✅ Data preview and pagination
- ✅ Dataset statistics and analysis
- ✅ Missing value imputation
- ✅ Column dropping operations
- ✅ Correlation matrix generation

### Frontend (React SPA)
- ✅ Modern React interface with professional styling
- ✅ Drag-and-drop file upload
- ✅ Real-time data preview
- ✅ Responsive design optimized for Vercel

## 🛠️ Local Development

### Prerequisites
- Node.js 18+
- Python 3.9+
- Vercel CLI (recommended)

### Setup

1. **Clone and install:**
   ```bash
   git clone <your-repo>
   cd DataCleaning
   npm run install-frontend
   pip install -r requirements.txt
   ```

2. **Run with Vercel CLI (Recommended):**
   ```bash
   npm install -g vercel
   vercel dev
   ```
   Access at: `http://localhost:3000`

3. **Alternative - Separate servers:**
   ```bash
   # Frontend
   cd frontend && npm start
   
   # Backend (original Flask server)
   cd backend && python app.py
   ```

## 🚀 Deployment Methods

### Method 1: Vercel CLI (Fastest)

```bash
# Install Vercel CLI
npm i -g vercel

# Login
vercel login

# Deploy to production
vercel --prod
```

### Method 2: GitHub Integration

1. Push to GitHub:
   ```bash
   git add .
   git commit -m "Deploy to Vercel"
   git push origin main
   ```

2. Connect repository at [vercel.com/new](https://vercel.com/new)

3. Vercel auto-detects configuration from `vercel.json`

### Method 3: Direct Import

1. Visit [vercel.com/dashboard](https://vercel.com/dashboard)
2. Click "New Project"
3. Import Git repository
4. Deploy with auto-detected settings

## ⚙️ Configuration Details

### `vercel.json` - Deployment Config
```json
{
  "version": 2,
  "builds": [
    {
      "src": "frontend/package.json",
      "use": "@vercel/static-build",
      "config": { "distDir": "build" }
    },
    {
      "src": "api/index.py", 
      "use": "@vercel/python"
    }
  ],
  "routes": [
    { "src": "/api/(.*)", "dest": "/api/index.py" },
    { "src": "/(.*)", "dest": "/frontend/build/$1" }
  ]
}
```

### `frontend/src/config.js` - API Configuration
```javascript
const API_BASE_URL = process.env.NODE_ENV === 'production' 
  ? '/api'  // Relative path for Vercel
  : 'http://localhost:5000/api';  // Local development

export default API_BASE_URL;
```

## 🔧 API Routes on Vercel

All routes are handled by `/api/index.py`:

| Method | Route | Description |
|--------|--------|-------------|
| POST | `/api/upload` | File upload endpoint |
| GET | `/api/preview` | Data preview (paginated) |
| GET | `/api/info` | Dataset information |
| GET | `/api/data` | Full dataset |
| POST | `/api/drop-columns` | Remove selected columns |
| POST | `/api/impute-missing` | Handle missing values |
| GET | `/api/correlation` | Correlation matrix |

## 🔧 Environment Variables

Set in Vercel Dashboard → Settings → Environment Variables:

```env
NODE_ENV=production
PYTHONPATH=/var/task
```

## 🐛 Troubleshooting

### Build Issues
```bash
# Clear and rebuild
rm -rf frontend/node_modules frontend/build
cd frontend
npm install
npm run build
```

### API Issues
- Check function logs in Vercel dashboard
- Verify `config.js` API paths
- Check serverless function cold start times

### File Upload Issues
- Serverless functions have 50MB limit
- Large files may timeout (adjust in Vercel settings)
- Check file type validation

### Python Dependencies
```bash
# Update requirements.txt
pip freeze > requirements.txt
```

## 📊 Performance on Vercel

### Optimizations Applied
- **React Build**: Optimized production bundle
- **API Routes**: Single serverless function handles all routes
- **Caching**: Static assets cached by Vercel CDN
- **Cold Starts**: Minimal Python imports for faster startup

### Limitations
- **File Size**: 50MB limit for uploads (Vercel serverless)
- **Execution Time**: 10s timeout for serverless functions
- **Memory**: 1GB default for Python functions

## 🎯 Post-Deployment Steps

1. **Custom Domain**:
   - Go to Vercel Dashboard → Settings → Domains
   - Add your custom domain

2. **Analytics**:
   ```bash
   vercel --prod --analytics
   ```

3. **Environment Secrets**:
   - Add sensitive configs in Vercel dashboard
   - Access via `os.environ` in Python functions

4. **Monitoring**:
   - Check Vercel dashboard for function logs
   - Set up alerts for errors

## 🔐 Security Features

- ✅ File type validation
- ✅ Size limit enforcement
- ✅ CORS properly configured
- ✅ Input sanitization
- ✅ No sensitive data exposure in errors

## 📈 Scaling Considerations

- **Serverless Auto-scaling**: Handles traffic spikes automatically
- **Global CDN**: Fast loading worldwide
- **Function Optimization**: Lightweight Python functions
- **Data Storage**: Consider external storage for large datasets

## 💰 Cost Estimation

Vercel Hobby Plan (Free):
- 100GB bandwidth
- 100GB-hours serverless function execution
- Unlimited static deployments

Perfect for development and small-scale production use.

## 🤝 Contributing to Deployment

1. Fork repository
2. Update deployment configs
3. Test locally with `vercel dev`
4. Submit PR with deployment improvements

## 🆘 Support

- **Vercel Docs**: [vercel.com/docs](https://vercel.com/docs)
- **Issues**: Create GitHub issue for deployment problems
- **Community**: Vercel Discord for platform-specific help

---

## 🎉 Success! Your Data Cleaning App is Live

After deployment, you'll have:
- ✅ Production-ready React frontend
- ✅ Serverless Python API
- ✅ Global CDN distribution
- ✅ Automatic SSL certificates
- ✅ Git-based deployments

**Access your app at**: `https://your-project-name.vercel.app`

Happy analyzing! 📊✨
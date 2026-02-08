# Bangladesh Regional Map System - Render Deployment Guide

## 🚀 Deploy to Render.com (Free)

### Prerequisites
- GitHub account
- Render account (sign up at https://render.com - free)

### Step 1: Push to GitHub

```bash
# Initialize git (if not already done)
git init

# Add all files
git add .

# Commit
git commit -m "Deploy Bangladesh map system to Render"

# Create a new repository on GitHub, then connect it:
git remote add origin https://github.com/YOUR_USERNAME/vdb-map.git
git branch -M main
git push -u origin main
```

### Step 2: Deploy on Render

1. Go to https://dashboard.render.com
2. Click **New +** → **Web Service**
3. Click **Connect GitHub** and authorize Render
4. Select your `vdb-map` repository
5. Render will auto-detect `render.yaml` configuration
6. Click **Create Web Service**

### Step 3: Wait for Build (5-10 minutes)

Render will:
- Install Python dependencies
- Install R and system libraries
- Install R packages (sf, tmap, dplyr, bangladesh)
- Start your Flask server

### Step 4: Access Your App

Your app will be live at: `https://vdb-map-bangladesh.onrender.com`

## 📝 Configuration

All configuration is in `render.yaml`:
- **Name**: vdb-map-bangladesh
- **Region**: Singapore (closest to Bangladesh)
- **Plan**: Free
- **Build**: Runs `build.sh` to install R
- **Start**: Runs `python app.py`

## ⚙️ Environment Variables

The app automatically uses Render's `PORT` environment variable. No manual configuration needed.

## 🔄 Updates

Push to GitHub and Render will auto-deploy:

```bash
git add .
git commit -m "Update maps"
git push
```

## 🆓 Free Tier Limitations

- **Sleep after inactivity**: App sleeps after 15 mins of no traffic (wakes in ~30 seconds)
- **750 hours/month**: Enough for most use cases
- **Slower builds**: R package installation takes ~5-10 minutes

## 💰 Upgrade Options

If you need:
- No sleep (always online)
- Faster performance
- More resources

Upgrade to Starter plan ($7/month) in Render dashboard.

## 🐛 Troubleshooting

**Build fails?**
- Check the build logs in Render dashboard
- Ensure all dependencies in `requirements.txt` and `build.sh`

**Maps not generating?**
- R packages might need time to install
- Check "Logs" tab in Render dashboard

**App doesn't start?**
- Verify `PORT` environment variable is used in `app.py`
- Check for Python syntax errors in logs

## 📞 Support

For Render-specific issues: https://render.com/docs

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

### **Issue: District movements not working**

**Symptoms:**
- Web interface loads but map generation fails
- Changes don't save or update maps
- Reset to original doesn't work

**Solutions:**

1. **Check diagnostics endpoint:**
   ```
   https://your-app.onrender.com/diagnostics
   ```
   This shows:
   - Python packages installed (pypdf, pillow, reportlab)
   - R installation status
   - File write permissions
   - Required files present

2. **Verify dependencies installed:**
   - Check build logs for successful installation
   - Ensure `pypdf`, `pillow`, and `reportlab` are installed
   - Verify R packages: `sf`, `tmap`, `dplyr`, `bangladesh`

3. **Check file permissions:**
   - Render needs write access to `outputs/` folder
   - Build script sets permissions: `chmod -R 755 outputs`

4. **Verify backup file exists:**
   - `region_swapped_data_original.csv` must exist for reset
   - Build script creates it automatically

5. **Check Python executable:**
   - Logo scripts use `sys.executable`
   - Diagnostics shows correct Python path

**Debugging steps:**

```bash
# 1. Visit diagnostics page
https://your-app.onrender.com/diagnostics

# 2. Check health endpoint
https://your-app.onrender.com/health

# 3. Review Render logs
# Go to Render Dashboard → Your Service → Logs

# 4. Test manually after deployment
curl -X POST https://your-app.onrender.com/generate \
  -H "Content-Type: application/json" \
  -d @test_payload.json
```

### **Build fails?**
- Check the build logs in Render dashboard
- Ensure all dependencies in `requirements.txt`:
  - flask==3.0.3
  - pypdf>=4.0.0
  - pillow>=10.0.0
  - reportlab>=4.0.0
- Verify `build.sh` is executable

**Maps not generating?**
- R packages take 5-10 minutes to install
- Check "Logs" tab in Render dashboard
- Look for R installation errors
- Verify GDAL, GEOS, PROJ libraries installed

**App doesn't start?**
- Verify `PORT` environment variable is used in `app.py`
- Check for Python syntax errors in logs
- Ensure Flask starts on `0.0.0.0` not `localhost`

**Logos not appearing?**
- Check if pypdf, pillow, reportlab are installed
- Visit `/diagnostics` to verify package status
- Logo scripts need all three packages
- Check build logs for installation errors

## 🔍 Diagnostic Endpoints

**Added in latest version:**

- `GET /health` - Basic health check
- `GET /diagnostics` - Complete system diagnostics
  - Python version and packages
  - R installation status
  - File permissions
  - Available output files

Use these to troubleshoot deployment issues.

## 📞 Support

For Render-specific issues: https://render.com/docs
For app issues: Check GitHub repository issues

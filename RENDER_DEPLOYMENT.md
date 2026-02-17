# Bangladesh Regional Map System - Render Deployment Guide

## 🚀 Deploy to Render.com (Free)

### Prerequisites
- GitHub account
- Render account (sign up at https://render.com - free)

### Step 1: Push to GitHub

```bash
# Add all files
git add .

# Commit
git commit -m "Deploy Bangladesh map system to Render"

# Push to GitHub
git push origin main
```

### Step 2: Deploy on Render

1. Go to https://dashboard.render.com
2. Click **New +** → **Web Service**
3. Click **Connect GitHub** and authorize Render
4. Select your `vdb-map` repository
5. Render will auto-detect `render.yaml` configuration
6. Click **Create Web Service**

### Step 3: Wait for Build (3-5 minutes)

Render will:
- Install Python dependencies (Flask, pandas, pypdf, pillow, reportlab)
- Create necessary directories (outputs, geojson)
- Use pre-built GeoJSON files (committed to repo)
- Start your Flask server

### Step 4: Access Your App

Your app will be live at: `https://vdb-map-bangladesh.onrender.com`

**Default Login Credentials:**
- Username: `admin` | Password: `zaytoon123`
- Username: `manager` | Password: `map2024`

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

## � Common Issues & Fixes

**1. "Application failed to start" or 404 errors**
- Check Render logs: Dashboard → Your Service → Logs
- Ensure `build.sh` completed successfully
- Verify `PORT` environment variable is set by Render automatically

**2. Login page shows but can't access maps**
- GeoJSON files are pre-generated and committed to repo
- Check if `geojson/districts.geojson` and `geojson/thanas.geojson` exist in repo
- Visit `/diagnostics` to verify files are present

**3. CSV export not working**
- Ensure `pandas` is in `requirements.txt`
- Check build logs for pandas installation
- Verify `District_Thana_Mapping.csv` is in repository

**4. Maps not generating**
- Pre-built PDF/PNG files are committed to repo
- R is not required for basic functionality on Render free tier
- Generate new maps by moving districts (this uses pre-existing data)

**5. Session/login issues**
- Flask secret key is set in `app.py`
- Sessions work across restarts but not across deployments
- Re-login after each Render deployment

## 🔍 Diagnostic Endpoints

**Added in latest version:**

- `GET /health` - Basic health check (returns 200 if app is running)
- `GET /diagnostics` - Complete system diagnostics
  - Python version and packages
  - R installation status (may show not available on free tier)
  - File permissions
  - Available output files
  - GeoJSON files status
- `GET /check_auth` - Check if user is authenticated

Use these to troubleshoot deployment issues.

## 🎯 Quick Verification Checklist

After deployment, verify:
- [ ] `/login` page loads
- [ ] Can login with admin/zaytoon123
- [ ] Dashboard (`/`) loads after login
- [ ] Interactive map (`/map`) shows correctly
- [ ] CSV export works (💾 Export CSV button)
- [ ] District viewer (`/districts`) accessible
- [ ] Logout works and redirects to login

## 📞 Support

For Render-specific issues: https://render.com/docs
For app issues: Check GitHub repository issues

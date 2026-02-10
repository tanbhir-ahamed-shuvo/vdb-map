# Render Deployment - Quick Troubleshooting

## 🚨 District Movements Not Working?

### Step 1: Check Diagnostics
Visit: `https://your-app.onrender.com/diagnostics`

Look for:
- ✅ **pypdf_installed**: true
- ✅ **pillow_installed**: true  
- ✅ **reportlab_installed**: true
- ✅ **r_installed**: true
- ✅ **output_dir_writable**: true
- ✅ **region_swapped_data_original.csv**: true

### Step 2: Check Build Logs

Go to Render Dashboard → Your Service → Logs

Look for:
```
📦 Installing Python dependencies...
✅ Successfully installed pypdf pillow reportlab
📊 Installing R and system dependencies...
✅ R packages installed
```

### Step 3: Common Issues & Fixes

#### ❌ **Logo packages not installed**
**Problem:** pypdf, pillow, or reportlab missing
**Fix:** 
- Verify `requirements.txt` contains all three packages
- Trigger rebuild in Render dashboard

#### ❌ **R installation failed**
**Problem:** R or R packages not installed
**Fix:**
- Check build logs for R installation errors
- May need to increase build timeout
- Verify `build.sh` has correct package names

#### ❌ **File permissions error**
**Problem:** Can't write to outputs/ folder
**Fix:**
- Build script should create and set permissions
- Check if `chmod -R 755 outputs` ran in build

#### ❌ **Missing backup file**
**Problem:** Reset functionality doesn't work
**Fix:**
- Build script should create `region_swapped_data_original.csv`
- Manually upload if missing

#### ❌ **Timeout errors**
**Problem:** Map generation takes too long
**Fix:**
- Free tier has 30-second request timeout
- R script + logo addition may exceed this
- Consider upgrading to paid tier

### Step 4: Test Locally First

Before deploying to Render, test locally:

```bash
# 1. Install dependencies
pip install -r requirements.txt

# 2. Test Flask app
python app.py

# 3. Test in browser
http://localhost:5000

# 4. Make a change and generate map
# If it works locally but not on Render, it's a deployment issue
```

### Step 5: Force Rebuild

Sometimes Render cache causes issues:

1. Go to Render Dashboard
2. Click your service
3. Click "Manual Deploy" → "Clear build cache & deploy"
4. Wait for fresh build (10-15 minutes)

## 🔧 Quick Fixes

### Fix 1: Update requirements.txt
```txt
flask==3.0.3
pypdf>=4.0.0
pillow>=10.0.0
reportlab>=4.0.0
```

### Fix 2: Update build.sh
```bash
#!/usr/bin/env bash
set -o errexit

pip install --upgrade pip
pip install -r requirements.txt

apt-get update
apt-get install -y r-base libgdal-dev libgeos-dev libproj-dev libudunits2-dev

Rscript -e "install.packages(c('sf', 'tmap', 'dplyr', 'bangladesh'), repos='https://cloud.r-project.org/', dependencies=TRUE)"

mkdir -p outputs
chmod -R 755 outputs

if [ -f "region_swapped_data.csv" ] && [ ! -f "region_swapped_data_original.csv" ]; then
    cp region_swapped_data.csv region_swapped_data_original.csv
fi
```

### Fix 3: Verify render.yaml
```yaml
services:
  - type: web
    name: vdb-map-bangladesh
    env: python
    region: singapore
    plan: free
    buildCommand: "./build.sh"
    startCommand: "python app.py"
```

## 📊 Health Check Commands

```bash
# Check if app is running
curl https://your-app.onrender.com/health

# Get full diagnostics
curl https://your-app.onrender.com/diagnostics

# Test map generation (replace with actual data)
curl -X POST https://your-app.onrender.com/generate \
  -H "Content-Type: application/json" \
  -d '[{"region":"Dhaka","district":"Dhaka","thana":"Tejgaon"}]'
```

## 🆘 Still Not Working?

1. **Check Render status page:** https://status.render.com
2. **Review complete logs** in Render dashboard
3. **Enable debug mode** temporarily (set `debug=True` in app.py)
4. **Contact support** with:
   - Service name
   - Deployment timestamp
   - Error messages from logs
   - Diagnostics output

## 💡 Pro Tips

- **First deployment** takes longest (10-15 minutes)
- **Subsequent deploys** are faster (5-7 minutes)
- **Free tier sleeps** after 15 mins inactivity
- **Wake-up time** is ~30 seconds
- **Request timeout** is 30 seconds (may limit large map generation)

## 🎯 Expected Behavior

When working correctly:

1. ✅ App loads at your Render URL
2. ✅ Drag and drop districts between regions
3. ✅ Click "Generate Updated Map"
4. ✅ See "Maps generated with Zaytoon branding"
5. ✅ Maps display with logo in top-right
6. ✅ Reset button restores original state

If ANY step fails, use diagnostics to identify the issue.

## 📞 Resources

- **Render Docs:** https://render.com/docs
- **Render Community:** https://community.render.com
- **GitHub Issues:** Check repository for similar issues
- **Diagnostics:** `/diagnostics` endpoint on your deployed app

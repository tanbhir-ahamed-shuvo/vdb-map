# District Movements Not Working on Render - Debugging Guide

## 🔍 Step 1: Check Debug Endpoints

After deploying the latest changes, use these endpoints on your Render app:

### **Check Current CSV Data**
```
https://your-app.onrender.com/debug/csv
```

**What to look for:**
- Does the CSV have the updated regions?
- Are districts in the correct regions?
- Check the first 10 lines to see what data is there

**Example response:**
```json
{
  "file": "/app/region_swapped_data.csv",
  "total_lines": 508,
  "content": "Region,District,Thana\nDhaka,Dhaka,Tejgaon\n...",
  "preview": ["Region,District,Thana", "Dhaka,Dhaka,Tejgaon", ...]
}
```

### **Check Debug Logs**
```
https://your-app.onrender.com/debug/logs
```

**What to look for:**
Look for these key lines in the logs:

```
[TIMESTAMP] GENERATE ENDPOINT CALLED
[TIMESTAMP] Received X records from client
[TIMESTAMP] CSV written successfully
[TIMESTAMP] R script return code: 0
[TIMESTAMP] Map files exist: PNG=true, PDF=true
[TIMESTAMP] Logo addition complete - success: true
```

**Common issues in logs:**

❌ **"CSV write error"**
- Permission problem on Render
- Not enough disk space

❌ **"R script return code: 1"**
- R script failed
- Check stderr output

❌ **"Map files exist: PNG=false"**
- R script didn't generate files
- Check R output for errors

❌ **"Logo addition failed"**
- Logo scripts crashed
- Check logo stderr

### **Clear Logs**
```
https://your-app.onrender.com/debug/clear
```

---

## 🧪 Step 2: Test the Full Workflow

### **Sequence to test:**

1. **Clear logs first:**
   ```
   GET https://your-app.onrender.com/debug/clear
   ```

2. **View CSV before change:**
   ```
   GET https://your-app.onrender.com/debug/csv
   ```
   
   Note what region "Dhaka" district is in.

3. **Make change in web UI:**
   - Drag "Dhaka" to another region (e.g., "Rajshahi")
   - Click "Generate Updated Map"
   - Wait for response

4. **Check CSV after change:**
   ```
   GET https://your-app.onrender.com/debug/csv
   ```
   
   Verify "Dhaka" is now in "Rajshahi" region.

5. **Check logs:**
   ```
   GET https://your-app.onrender.com/debug/logs
   ```
   
   Look for any errors or issues.

6. **Check map files:**
   ```
   GET https://your-app.onrender.com/outputs/bangladesh_districts_updated_from_swaps.pdf
   ```
   
   Verify Dhaka is colored with Rajshahi's color.

---

## 🐛 Common Problems & Solutions

### **Problem 1: CSV shows old data after move**

**Symptom:** You move Dhaka to Rajshahi, but CSV still shows it in Dhaka region.

**Cause:** CSV not being written correctly
**Fix:**
1. Check file permissions: `/outputs/` folder must be writable
2. Check disk space on Render
3. Check for "CSV write error" in logs

```bash
# In Render build log, verify:
chmod -R 755 outputs
```

---

### **Problem 2: CSV updated but maps unchanged**

**Symptom:** CSV has correct data but maps show old regions.

**Cause:** R script not reading updated CSV
**Fix:**
1. Check R script return code should be 0
2. Look for R errors in stderr
3. Verify `generate_map_from_swaps.R` reads from correct file path

Debug endpoint should show:
```
"R script return code: 0"
"Map files exist: PNG=true, PDF=true"
```

---

### **Problem 3: R script fails**

**Symptom:** Return code not 0, maps don't generate

**Check:**
1. Is R installed? (`/diagnostics` endpoint shows r_installed: true)
2. Are R packages installed? (Check build logs)
3. Is Bangladesh shapefile available?

**Fix:**
- Clear build cache on Render → Manual Deploy
- Wait for fresh build (10-15 min)

---

### **Problem 4: Logo scripts fail**

**Symptom:** Maps generate but without logos

**Check:**
1. `pypdf_installed: true`
2. `pillow_installed: true`
3. `reportlab_installed: true`

**Fix:**
- Verify requirements.txt has all three packages
- Rebuild on Render

---

## 📋 Full Debugging Checklist

Use this checklist to diagnose the issue:

```
STEP 1: Pre-Test Check
[ ] /health endpoint returns healthy
[ ] /diagnostics shows r_installed: true
[ ] /diagnostics shows all Python packages installed
[ ] /diagnostics shows output_dir_writable: true

STEP 2: Move Test
[ ] Make change in web interface
[ ] Click "Generate Updated Map"
[ ] Request succeeds (HTTP 200)

STEP 3: CSV Check
[ ] /debug/csv shows updated region assignments
[ ] Record count matches expectations
[ ] No parse errors in content

STEP 4: R Execution Check
[ ] Check logs for "R script return code: 0"
[ ] No errors in R stderr
[ ] "Map files exist: PNG=true, PDF=true"

STEP 5: Logo Check
[ ] Check logs for "Logo addition complete - success: true"
[ ] PDF return code: 0
[ ] PNG return code: 0

STEP 6: Map Verification
[ ] Download PDF from /outputs/
[ ] Open in PDF viewer
[ ] Check if districts are in correct regions
[ ] Check if Zaytoon logo visible
```

---

## 🔗 Helpful Endpoints

| Endpoint | Purpose |
|----------|---------|
| `/health` | Quick health check |
| `/diagnostics` | Full system diagnostics |
| `/debug/csv` | View current CSV data |
| `/debug/logs` | View debug logs (last 50 lines) |
| `/debug/clear` | Clear debug log file |
| `/outputs/` | Access generated maps |
| `/region_swapped_data.csv` | Download current CSV |

---

## 📱 Example Testing Flow

```bash
# 1. Check system is ready
curl https://your-app.onrender.com/diagnostics

# 2. Clear old logs
curl https://your-app.onrender.com/debug/clear

# 3. View CSV before change
curl https://your-app.onrender.com/debug/csv | head -20

# 4. Test map generation
curl -X POST https://your-app.onrender.com/generate \
  -H "Content-Type: application/json" \
  -d '[{"region":"Rajshahi","district":"Dhaka","thana":"Tejgaon"}]'

# 5. View logs
curl https://your-app.onrender.com/debug/logs

# 6. View CSV after change
curl https://your-app.onrender.com/debug/csv | head -20
```

---

## 📞 If Still Stuck

If using the debug endpoints doesn't reveal the issue:

1. **Check Render build logs:**
   - Service → Logs tab
   - Look for installation errors
   - Verify R packages installed

2. **Force rebuild:**
   - Dashboard → Service → Manual Deploy
   - Clear build cache
   - Wait 15 minutes

3. **Test locally first:**
   ```bash
   python app.py
   # Test district movements locally
   # If works locally, it's a Render deployment issue
   ```

4. **Check file permissions:**
   - outputs/ folder must be writable
   - CSV must be readable/writable

---

## ✅ Success Indicators

When working correctly:

1. ✅ /debug/csv shows updated region assignments
2. ✅ Logs show "R script return code: 0"
3. ✅ Maps display with districts in correct regions
4. ✅ Map files have Zaytoon logo

---

**Key Point:** The debug endpoints let you trace the exact point where the process fails. Use them systematically to identify the root cause!

# VDB MAP 2.1 - Bangladesh Regional Map Management System

## 📍 Project Overview

VDB MAP 2.1 is an **interactive web-based application** for managing and visualizing Bangladesh's regional, district, and thana (upazila) boundaries. Built with **Zaytoon Business Solutions**, it provides real-time map generation with drag-and-drop functionality for seamless thana management across 10 regions.

**🌐 Live Demo:** https://vdb-map.onrender.com/

*Note: Hosted on Render free tier - first load may take 30-60 seconds to wake up after inactivity.*

---

## ✨ Key Features

- **Interactive Web Interface** - Real-time region, district, and thana management
- **10 Region Maps** - Individual PDF/PNG maps for each of Bangladesh's regions:
  - Barisal (Red)
  - Chittagong (Teal)
  - Cumilla (Light Blue)
  - Dhaka (Green)
  - Faridpur (Yellow)
  - Khulna (Orange)
  - Mymensingh (Brown)
  - Rajshahi (Tan)
  - Rangpur (Purple)
  - Sylhet (Gold)

- **Full Bangladesh Maps**
  - District-level map with all 64 districts
  - Thana-level map with all 544 thanas
  - High-resolution PDFs (50×36" @ 600 DPI)
  - Color-coded by region with legend

- **Drag-and-Drop Thana Movement**
  - Move thanas between districts
  - Geographic neighbor validation
  - Real-time CSV updates
  - Automatic map regeneration
  - **Reset to Original** - One-click restoration to initial state with original backup

- **PDF & PNG Generation**
  - Auto-generated maps with embedded Zaytoon logo
  - Color reference legends
  - High-quality outputs for printing (up to 50×36" @ 600 DPI)
  - Automatic logo application on all map updates

- **PDF Viewer with Navigation**
  - Region-wise map navigation (Prev/Next buttons)
  - Full-screen view capability
  - Page-by-page display

---

## 📁 Project Structure

```
VDB_MAP2.1/
├── app.py                                    # Flask web server
├── generate_map_from_swaps.R                 # R script for map generation
├── region-manager-interactive.html           # Main web interface
├── region_swapped_data.csv                   # Current region/district/thana assignments
├── region_swapped_data_original.csv          # Original backup for reset functionality
├── zaytoon-logo.png                          # Logo embedded in all PDFs/PNGs
├── add_logo_to_pdfs.py                       # Logo embedding for PDFs
├── add_logo_to_pngs.py                       # Logo embedding for PNGs
├── apply_logos_manually.py                   # Manual logo application utility
├── requirements.txt                          # Python dependencies
├── BGD_Upazila.shp                          # Bangladesh shapefile (thana level)
├── BGD_Upazila.shx, .dbf, .prj, .cpg        # Shapefile components
├── bangladesh/                               # R package for Bangladesh maps
│   ├── R/                                    # R source files
│   ├── data/                                 # Pre-loaded map data
│   └── man/                                  # Documentation
├── outputs/                                  # Generated maps
│   ├── bangladesh_districts_updated_from_swaps.pdf
│   ├── bangladesh_districts_updated_from_swaps.png
│   ├── bangladesh_thanas_updated_from_swaps.pdf
│   ├── bangladesh_thanas_updated_from_swaps.png
│   ├── region_*.pdf                         # 10 region maps
│   └── region_colors.csv                    # Color reference
├── __pycache__/                              # Python cache
└── README.md                                 # This file
```

---

## 🚀 Installation & Setup

### **Requirements**

- **Python 3.8+** - For Flask web server
- **R 4.0+** - For map generation (tmap, sf, dplyr)
- **GIS Libraries** - GDAL, GEOS, PROJ (installed via R packages)

### **Step 1: Clone the Repository**

```bash
git clone https://github.com/tanbhir-ahamed-shuvo/vdb-map.git
cd VDB_MAP2.1
```

### **Step 2: Install Python Dependencies**

```bash
pip install -r requirements.txt
```

**Dependencies:**
- Flask 3.0.3 - Web server
- pypdf >= 4.0.0 - PDF manipulation
- pillow >= 10.0.0 - Image processing
- reportlab >= 4.0.0 - PDF logo overlay

### **Step 3: Install R Packages**

```r
install.packages(c("tmap", "sf", "dplyr"))
# Also install the bangladesh package:
devtools::install_local("bangladesh/")
```

### **Step 4: Configure Shapefile**

Ensure `BGD_Upazila.shp` and associated files are in the project root directory.

---

## 📖 Usage

### **Start the Web Server**

```bash
python app.py
```

Server runs at: **http://localhost:5000**
Network access: **http://<your-ip>:5000**

### **Access the Web Interface**

1. Open your browser
2. Navigate to `http://localhost:5000`
3. View the interactive map with region selector

### **Move Thanas Between Districts**

1. Drag a thana in the map
2. Drop it on a neighboring district
3. Changes auto-update in real-time
4. Maps regenerate automatically

### **Generate Maps**

Click **"Generate Updated Map"** to create new PDFs/PNGs with current thana assignments. Maps are automatically embedded with Zaytoon logo.

### **Reset to Original State**

Click **"Reset to Original"** to:
1. Restore original thana assignments from backup CSV
2. Regenerate all maps with original state
3. Apply logos to all outputs
4. Refresh the web interface

### **View Region Maps**

1. Select a region from the dropdown
2. View in the embedded PDF viewer
3. Use Prev/Next buttons to navigate regions
4. Click "Full View" to open in new tab

### **Download Maps**

- **PNG Downloads**: Districts or Thanas
- **PDF Downloads**: Districts or Thanas
- **Full View**: Opens PDF in new browser tab

---

## 🗺️ Map Outputs

### **Generated Files**

| File | Description | Dimensions |
|------|-------------|-----------|
| bangladesh_districts_updated_from_swaps.png | District map | 4200×3000 px @ 300 DPI |
| bangladesh_districts_updated_from_swaps.pdf | District map PDF | 10×8" @ 300 DPI |
| bangladesh_thanas_updated_from_swaps.png | Thana map | 5400×3800 px @ 300 DPI |
| bangladesh_thanas_updated_from_swaps.pdf | Thana map PDF | 50×36" @ 600 DPI |
| region_*.pdf | Individual region maps (10 files) | 14×10" @ 300 DPI |

### **Color Coding**

All maps use consistent hex colors for regions:

```csv
Region,HexColor
Barisal,#FF6B6B
Chittagong,#4ECDC4
Cumilla,#45B7D1
Dhaka,#96CEB4
Faridpur,#FFEAA7
Khulna,#DDA15E
Mymensingh,#BC6C25
Rajshahi,#C9ADA7
Rangpur,#9A8C98
Sylhet,#F4A261
```

---

## 🛠️ Technical Stack

### **Backend**
- **Flask 3.0.3** - Lightweight Python web framework
- **Python 3.x** - Core language

### **Geospatial Processing**
- **R 4.x** - Statistical computing
- **tmap** - Thematic mapping
- **sf** - Simple features (spatial data)
- **dplyr** - Data manipulation
- **bangladesh** - Bangladesh map package

### **Frontend**
- **HTML5** - Structure
- **CSS3** - Styling
- **JavaScript** - Interactivity
- **PDF.js 3.11.174** - PDF viewer

### **Data Format**
- **CSV** - Thana assignments
- **Shapefile** - Spatial boundaries
- **GeoJSON** - Map rendering

---

## 📊 Data Files

### **region_swapped_data.csv**

Current state of thana assignments:
- **Region** - 10 administrative regions
- **District** - 64 districts
- **Thana** - All 544 thanas with assignments
- **Spelling corrections** - Normalized names for shapefile matching

### **region_swapped_data_original.csv**

Backup of original state for reset functionality:
- Created during deployment
- Used by `/reset` endpoint
- Never modified during normal operation

### **District_Thana_Mapping.csv**

Reference file with:
- All 64 districts
- Associated thanas per district
- Population data
- Official boundaries

---

## 🔧 File Descriptions

### **Core Application Files**

| File | Purpose |
|------|---------|
| app.py | Flask server, CSV handling, map generation trigger |
| generate_map_from_swaps.R | Generates all PDF/PNG maps from CSV data |
| region-manager-interactive.html | Interactive web UI with drag-drop, PDF viewer |
| region_swapped_data.csv | Master data: regions, districts, thanas |

### **Support Files**

| File | Purpose |
|------|---------|
| zaytoon-logo.png | Logo embedded in all PDFs/PNGs |
| add_logo_to_pdfs.py | Embeds logo in PDF maps (auto-run by Flask) |
| add_logo_to_pngs.py | Embeds logo in PNG maps (auto-run by Flask) |
| apply_logos_manually.py | Manual logo application utility |
| build.sh | Render.com deployment build script |
| app_debug.log | Runtime debug logs (generated) |
| bangladesh/ | R package with pre-loaded Bangladesh map data |

---

## 🌐 Deployment

### **Local Development**

```bash
python app.py
# Access at http://localhost:5000
```

### **Network Access**

The Flask server binds to all network interfaces (0.0.0.0:5000), making it accessible from any device on your local network:

```
http://<your-ip-address>:5000
```

Find your IP:
- **Windows:** `ipconfig` (look for IPv4 Address)
- **Linux/Mac:** `ifconfig` or `ip addr`

### **Docker Deployment**

A Dockerfile is included for containerized deployment:

```bash
docker build -t vdb-map .
docker run -p 5000:5000 vdb-map
```

### **Production Deployment (Render.com)**

The application is deployed at: https://vdb-map.onrender.com/

**Automatic Deployment:**
1. Push changes to GitHub repository
2. Render automatically builds and deploys
3. `build.sh` script handles R/Python setup
4. Free tier - may sleep after inactivity

**Build Process:**
- Installs R 4.0+ and required packages (tmap, sf, dplyr)
- Installs Python dependencies from requirements.txt
- Creates outputs/ directory with proper permissions
- Copies original CSV backup for reset functionality

See [RENDER_DEPLOYMENT.md](RENDER_DEPLOYMENT.md) for detailed deployment guide.

---

## 📝 API Endpoints

| Endpoint | Method | Purpose |
|----------|--------|---------|
| `/` | GET | Main web interface |
| `/generate` | POST | Regenerate maps from CSV |
| `/reset` | POST | Reset to original state |
| `/health` | GET | Health check endpoint |
| `/diagnostics` | GET | System diagnostics |
| `/debug/csv` | GET | View current CSV content |
| `/debug/logs` | GET | View debug logs |
| `/debug/clear` | GET | Clear debug logs |
| `/region_swapped_data.csv` | GET | Download current CSV data |
| `/outputs/<filename>` | GET | Access generated maps |
| `/<path:filename>` | GET | Static files (logo, etc.) |

---

## 🐛 Troubleshooting

### **Maps Don't Update**
- Check `/debug/logs` endpoint for execution traces
- Verify R package installation: `require(tmap)`, `require(sf)`, `require(dplyr)`
- Ensure `generate_map_from_swaps.R` has execute permissions
- Check outputs/ directory permissions (chmod 755)

### **Thana Move Fails**
- Use `/debug/csv` to verify CSV updates are saved
- Check browser console for errors
- Verify district adjacency in CSV data

### **PDF Won't Open**
- Ensure PDF.js library is loaded (check browser console)
- Clear browser cache: Ctrl+Shift+Delete
- Try Full View button
- Check `/outputs/` directory for generated files

### **Logo Missing from PDFs/PNGs**
- Confirm `zaytoon-logo.png` exists (8KB+)
- Run manually: `python apply_logos_manually.py`
- Check console for Unicode encoding errors on Windows
- Verify pypdf, pillow, reportlab installed

### **Debug Endpoints for Production Issues**
- `/health` - Check if server is running
- `/diagnostics` - System status and file checks
- `/debug/csv` - View current CSV content
- `/debug/logs` - See execution logs (R script, logo application)
- `/debug/clear` - Reset logs for fresh diagnosis

---

## 🎨 Logo System

All generated maps automatically include the Zaytoon Business Solutions logo:

**Automatic Application:**
- Triggered after every map generation
- Embeds logo in all PDFs (lower-right corner)
- Embeds logo in all PNGs (lower-right corner)
- No manual intervention required

**Manual Application:**
```bash
python apply_logos_manually.py
```

**Troubleshooting:**
- Requires `zaytoon-logo.png` in project root
- Dependencies: pypdf >= 4.0.0, pillow >= 10.0.0, reportlab >= 4.0.0
- Windows users: UTF-8 encoding configured automatically

For detailed documentation, see `LOGO_SYSTEM_GUIDE.md`

---

## 📈 Map Statistics

**Geographic Coverage:**
- **10 Regions** - Administrative divisions of Bangladesh
- **64 Districts** - Zila (district) level coverage
- **544 Thanas** - Upazila (sub-district) level - 100% mapped and matched

**Quality Metrics:**
- **Match Rate**: 544/544 thanas (100%)
- **Border Accuracy**: ±10 meters (limited by shapefile resolution)
- **Map Generation Speed**: ~15-30 seconds for full regeneration (all 14 maps)
- **Logo Application**: Automatic on all PDF/PNG outputs

---

## 👥 Author & License

**Developed by:** Zaytoon Business Solutions

**Repository:** https://github.com/tanbhir-ahamed-shuvo/vdb-map

**License:** [Your License Here]

---

## 📞 Support

For issues or questions:
1. Check this README
2. Review GitHub Issues
3. Contact Zaytoon Business Solutions

---

## 🗓️ Version History

**v2.1** (Current)
- ✅ 10 region-wise maps with dynamic generation
- ✅ Automatic Zaytoon logo embedding on all PDFs/PNGs
- ✅ Reset to original functionality with backup system
- ✅ Color-coded region system with legend
- ✅ PDF viewer with navigation
- ✅ Debug endpoints for production troubleshooting
- ✅ Render.com deployment with auto-build
- ✅ Full thana management (544 thanas, 100% matched)
- ✅ Comprehensive documentation (README, deployment guides)

**v2.0**
- Regional decomposition
- Drag-and-drop interface
- Interactive web UI

**v1.0**
- Basic mapping functionality

---

**Last Updated:** February 10, 2026

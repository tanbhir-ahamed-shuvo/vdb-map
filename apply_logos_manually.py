#!/usr/bin/env python3
"""
Manual Logo Application Script
Run this if logos are not showing up on maps
"""

import subprocess
import sys
from pathlib import Path

def main():
    print("=" * 70)
    print("MANUAL LOGO APPLICATION - Zaytoon Business Solutions")
    print("=" * 70)
    print("\nThis script will add logos to all PDF and PNG maps in outputs/\n")
    
    base_dir = Path(__file__).parent
    
    # Check if logo file exists
    logo_file = base_dir / "zaytoon-logo.png"
    if not logo_file.exists():
        print("❌ ERROR: zaytoon-logo.png not found!")
        return 1
    
    print(f"✓ Logo file found: {logo_file}")
    print(f"✓ Python executable: {sys.executable}\n")
    
    # Run PDF logo script
    print("\n" + "=" * 70)
    print("STEP 1: Adding logos to PDFs...")
    print("=" * 70)
    pdf_script = base_dir / "add_logo_to_pdfs.py"
    result = subprocess.run([sys.executable, str(pdf_script)], cwd=str(base_dir))
    
    if result.returncode != 0:
        print(f"⚠ PDF logo addition returned code: {result.returncode}")
    
    # Run PNG logo script
    print("\n" + "=" * 70)
    print("STEP 2: Adding logos to PNGs...")
    print("=" * 70)
    png_script = base_dir / "add_logo_to_pngs.py"
    result = subprocess.run([sys.executable, str(png_script)], cwd=str(base_dir))
    
    if result.returncode != 0:
        print(f"⚠ PNG logo addition returned code: {result.returncode}")
    
    print("\n" + "=" * 70)
    print("✅ LOGO APPLICATION COMPLETE!")
    print("=" * 70)
    print("\nCheck your outputs/ folder for updated maps with logos.")
    print("If logos still don't appear, check that:")
    print("  1. pypdf, pillow, and reportlab are installed")
    print("  2. zaytoon-logo.png is a valid PNG file")
    print("  3. Map files exist in outputs/ directory\n")
    
    return 0

if __name__ == "__main__":
    sys.exit(main())

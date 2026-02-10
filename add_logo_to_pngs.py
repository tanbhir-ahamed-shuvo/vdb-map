#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Add Zaytoon logo to PNG map images
"""

import sys
from pathlib import Path
from PIL import Image

# Fix Windows console encoding
if sys.platform == 'win32':
    try:
        sys.stdout.reconfigure(encoding='utf-8')
    except:
        pass

def add_logo_to_png(logo_path, png_path, output_path):
    """Add logo to PNG image"""
    try:
        # Open the logo and the PNG
        logo = Image.open(logo_path)
        png_img = Image.open(png_path)
        
        # Calculate logo size (4% of image height)
        logo_height = int(png_img.height * 0.04)
        aspect_ratio = logo.width / logo.height
        logo_width = int(logo_height * aspect_ratio)
        
        # Resize logo
        logo_resized = logo.resize((logo_width, logo_height), Image.Resampling.LANCZOS)
        
        # Convert to RGBA if needed
        if png_img.mode != 'RGBA':
            png_img = png_img.convert('RGBA')
        
        # Create a copy to paste on
        result = png_img.copy()
        
        # Position logo at top-left (20 pixels from edges)
        x_pos = 20
        y_pos = 20
        
        # Paste logo with transparency
        if logo_resized.mode == 'RGBA':
            result.paste(logo_resized, (x_pos, y_pos), logo_resized)
        else:
            result.paste(logo_resized, (x_pos, y_pos))
        
        # Save result
        result.save(output_path, 'PNG', optimize=True)
        return True
        
    except Exception as e:
        print(f"  Error: {e}")
        return False

def main():
    logo_path = Path("zaytoon-logo.png")
    outputs_dir = Path("outputs")
    
    print("=" * 60)
    print("Adding Zaytoon Logo to PNG Maps")
    print("=" * 60)
    
    if not logo_path.exists():
        print("⚠ Logo file not found!")
        return
    
    print(f"\n✓ Logo file found: {logo_path}")
    
    # Find PNG files (full maps only, not region maps)
    png_files = [
        outputs_dir / "bangladesh_districts_updated_from_swaps.png",
        outputs_dir / "bangladesh_thanas_updated_from_swaps.png"
    ]
    
    existing_pngs = [p for p in png_files if p.exists()]
    
    if not existing_pngs:
        print("⚠ No PNG files found!")
        return
    
    print(f"\nFound {len(existing_pngs)} PNG files")
    print("\nAdding logo to PNG files...")
    
    for png_path in existing_pngs:
        output_path = png_path.parent / f"{png_path.stem}_temp_logo.png"
        print(f"  {png_path.name}...", end=" ")
        if add_logo_to_png(logo_path, png_path, output_path):
            # Replace original with logo version
            output_path.replace(png_path)
            print("✓")
        else:
            # Clean up temp file if it exists
            if output_path.exists():
                output_path.unlink()
            print("✗ (failed)")
    
    print("\n✓ PNG logo insertion complete!")

if __name__ == "__main__":
    main()

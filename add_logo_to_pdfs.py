#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Add Zaytoon logo to top of all PDF maps
Requires: pip install pillow pypdf
"""

import os
import sys
from pathlib import Path
import subprocess

# Fix Windows console encoding
if sys.platform == 'win32':
    try:
        sys.stdout.reconfigure(encoding='utf-8')
    except:
        pass

try:
    from PIL import Image
    from pypdf import PdfReader, PdfWriter
    from reportlab.pdfgen import canvas
    from reportlab.lib.utils import ImageReader
    import io
    HAS_PYPDF = True
except ImportError:
    HAS_PYPDF = False

def add_logo_with_pypdf(logo_path, pdf_path, output_path):
    """Use PyPDF to add logo overlay to existing PDF"""
    try:
        # Load the logo
        logo_img = Image.open(logo_path)
        
        # Read the existing PDF
        reader = PdfReader(pdf_path)
        writer = PdfWriter()
        
        # Get first page dimensions
        first_page = reader.pages[0]
        page_width = float(first_page.mediabox.width)
        page_height = float(first_page.mediabox.height)
        
        # Calculate logo dimensions (very small - 4% of page height)
        logo_height = page_height * 0.04  # 4% of page height
        aspect_ratio = logo_img.width / logo_img.height
        logo_width = logo_height * aspect_ratio
        
        # Maximum width check
        max_logo_width = page_width * 0.25  # Max 25% of page width
        if logo_width > max_logo_width:
            logo_width = max_logo_width
            logo_height = logo_width / aspect_ratio
        
        # Create logo overlay
        packet = io.BytesIO()
        can = canvas.Canvas(packet, pagesize=(page_width, page_height))
        
        # Position logo at very top left corner
        x_pos = 20  # 20 points from left edge
        y_pos = page_height - logo_height - 5  # 5 points from top edge
        
        can.drawImage(ImageReader(logo_img), x_pos, y_pos, 
                     width=logo_width, height=logo_height, 
                     preserveAspectRatio=True, mask='auto')
        can.save()
        
        # Move to beginning of StringIO buffer
        packet.seek(0)
        logo_pdf = PdfReader(packet)
        
        # Merge logo with each page
        for page_num in range(len(reader.pages)):
            page = reader.pages[page_num]
            page.merge_page(logo_pdf.pages[0])
            writer.add_page(page)
        
        # Write output
        with open(output_path, 'wb') as output_file:
            writer.write(output_file)
        
        return True
    except Exception as e:
        print(f"  Error: {e}")
        return False

def check_imagemagick():
    """Check if ImageMagick is installed"""
    try:
        result = subprocess.run(["convert.exe", "-version"], capture_output=True, text=True)
        return "ImageMagick" in result.stdout
    except:
        return False

def check_ghostscript():
    """Check if GhostScript is installed"""
    try:
        result = subprocess.run(["gswin64c", "-version"], capture_output=True, text=True)
        return True
    except:
        try:
            result = subprocess.run(["gswin32c", "-version"], capture_output=True, text=True)
            return True
        except:
            return False

def add_logo_with_imagemagick(logo_path, pdf_path, output_path):
    """Use ImageMagick to add logo to PDF"""
    try:
        cmd = [
            "convert.exe",
            "-density", "300",
            "-background", "white",
            "-page", "+30+50",
            str(logo_path),
            str(pdf_path),
            "-composite",
            "-density", "300",
            "-quality", "95",
            str(output_path)
        ]
        subprocess.run(cmd, check=True, capture_output=True)
        return True
    except Exception as e:
        print(f"  Error: {e}")
        return False

def main():
    outputs_dir = Path("outputs")
    logo_path = Path("zaytoon-logo.png")
    
    print("=" * 60)
    print("Zaytoon Logo PDF Insertion Tool")
    print("=" * 60)
    
    if not logo_path.exists() or logo_path.stat().st_size < 1000:
        print("\n⚠ WARNING: Logo file is missing or invalid!")
        print(f"  Expected: {logo_path} (valid image file)")
        print(f"  Current size: {logo_path.stat().st_size if logo_path.exists() else 0} bytes")
        print("\nPlease provide the Zaytoon Business Solutions logo in PNG format.")
        print("Note: Top margin (12%) is already reserved in all PDFs for the logo.")
        return
    
    print(f"\n✓ Logo file found: {logo_path}")
    
    has_imagemagick = check_imagemagick()
    has_ghostscript = check_ghostscript()
    
    print(f"✓ ImageMagick installed: {has_imagemagick}")
    print(f"✓ GhostScript installed: {has_ghostscript}")
    print(f"✓ PyPDF available: {HAS_PYPDF}")
    
    if not has_imagemagick and not has_ghostscript and not HAS_PYPDF:
        print("\n⚠ No PDF processing tools found!")
        print("  Install one of these options:")
        print("  1. Python libraries: pip install pypdf pillow reportlab")
        print("  2. ImageMagick: choco install imagemagick")
        print("  3. GhostScript: choco install ghostscript")
        return
    
    pdfs = sorted(outputs_dir.glob("*.pdf"))
    print(f"\nFound {len(pdfs)} PDF files")
    
    if HAS_PYPDF:
        print("\nAdding logo to PDFs using PyPDF...")
        for pdf_path in pdfs:
            output_path = pdf_path.parent / f"{pdf_path.stem}_temp_logo.pdf"
            print(f"  {pdf_path.name}...", end=" ")
            if add_logo_with_pypdf(logo_path, pdf_path, output_path):
                # Replace original with logo version
                output_path.replace(pdf_path)
                print("✓")
            else:
                # Clean up temp file if it exists
                if output_path.exists():
                    output_path.unlink()
                print("✗ (failed)")
    elif has_imagemagick:
        print("\nAdding logo to PDFs using ImageMagick...")
        for pdf_path in pdfs:
            output_path = pdf_path.parent / f"{pdf_path.stem}_temp_logo.pdf"
            print(f"  {pdf_path.name}...", end=" ")
            if add_logo_with_imagemagick(logo_path, pdf_path, output_path):
                # Replace original with logo version
                output_path.replace(pdf_path)
                print("✓")
            else:
                # Clean up temp file if it exists
                if output_path.exists():
                    output_path.unlink()
                print("✗ (failed)")
    else:
        print("\n⚠ Manual method:")
        print("  Use this ImageMagick command for each PDF:")
        print("  convert -density 300 -page +30+50 zaytoon_logo.png map.pdf -composite output.pdf")

if __name__ == "__main__":
    main()


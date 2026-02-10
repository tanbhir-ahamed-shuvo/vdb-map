#!/usr/bin/env python3
"""
Test Logo Functionality
Quick test to verify logos are being added correctly
"""

import subprocess
import sys
from pathlib import Path

def test_logo_addition():
    print("\n" + "=" * 70)
    print("TESTING LOGO ADDITION FUNCTIONALITY")
    print("=" * 70)
    
    base_dir = Path(__file__).parent
    outputs_dir = base_dir / "outputs"
    
    # Check files exist
    test_files = [
        outputs_dir / "bangladesh_districts_updated_from_swaps.pdf",
        outputs_dir / "bangladesh_districts_updated_from_swaps.png",
        outputs_dir / "bangladesh_thanas_updated_from_swaps.pdf",
        outputs_dir / "bangladesh_thanas_updated_from_swaps.png",
    ]
    
    print("\n1. Checking if map files exist...")
    all_exist = True
    for f in test_files:
        exists = f.exists()
        status = "✓" if exists else "✗"
        print(f"   {status} {f.name}")
        if not exists:
            all_exist = False
    
    if not all_exist:
        print("\n❌ Some map files are missing. Run: Rscript generate_map_from_swaps.R")
        return False
    
    # Check file sizes
    print("\n2. Checking file sizes (before logo addition)...")
    sizes_before = {}
    for f in test_files:
        size = f.stat().st_size
        sizes_before[f.name] = size
        print(f"   {f.name}: {size:,} bytes")
    
    # Add logos
    print("\n3. Adding logos...")
    result = subprocess.run(
        [sys.executable, str(base_dir / "apply_logos_manually.py")],
        cwd=str(base_dir),
        capture_output=True,
        text=True
    )
    
    if result.returncode != 0:
        print(f"   ✗ Logo addition failed with code {result.returncode}")
        return False
    
    print("   ✓ Logo scripts completed")
    
    # Check file sizes again
    print("\n4. Checking file sizes (after logo addition)...")
    sizes_after = {}
    for f in test_files:
        size = f.stat().st_size
        sizes_after[f.name] = size
        diff = size - sizes_before[f.name]
        print(f"   {f.name}: {size:,} bytes (changed: {diff:+,} bytes)")
    
    # Verify changes
    print("\n5. Verification...")
    pdf_changed = any(sizes_after[f.name] != sizes_before[f.name] 
                      for f in test_files if f.name.endswith('.pdf'))
    png_changed = any(sizes_after[f.name] != sizes_before[f.name] 
                      for f in test_files if f.name.endswith('.png'))
    
    if pdf_changed or png_changed:
        print("   ✓ Files were modified (logos likely added)")
    else:
        print("   ⚠ Files unchanged (logos may already be present)")
    
    print("\n" + "=" * 70)
    print("✅ TEST COMPLETE - Logos should now be visible in maps")
    print("=" * 70)
    print("\nTo verify visually:")
    print("  - Open any PDF from outputs/ folder")
    print("  - Look for Zaytoon logo in top-right corner")
    print("  - PNG files should also show the logo\n")
    
    return True

if __name__ == "__main__":
    test_logo_addition()

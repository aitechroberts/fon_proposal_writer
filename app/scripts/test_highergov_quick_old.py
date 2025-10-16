#!/usr/bin/env python3
"""
Quick test script for HigherGov integration.

Usage:
    python scripts/test_highergov_quick.py <opportunity_id>
"""

import sys
import os
from pathlib import Path
import dotenv

dotenv.load_dotenv()

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent.parent))

def test_api_key():
    """Test 1: Check API key configuration."""
    print("=" * 60)
    print("Test 1: API Key Configuration")
    print("=" * 60)
    
    api_key = os.getenv("HIGHERGOV_API_KEY")
    
    if not api_key:
        print("❌ HIGHERGOV_API_KEY not set")
        print("\nFix: Add to .env file:")
        print("  HIGHERGOV_API_KEY=your-key-here")
        return False
    
    print(f"✓ API key configured: {api_key[:10]}...{api_key[-5:]}")
    return True


def test_import():
    """Test 2: Import integration module."""
    print("\n" + "=" * 60)
    print("Test 2: Module Import")
    print("=" * 60)
    
    try:
        from src.integrations.highergov import (
            get_opportunity_preview,
            ingest_highergov_opportunity
        )
        print("✓ Module imported successfully")
        return True
    except ImportError as e:
        print(f"❌ Import failed: {e}")
        print("\nFix: Ensure src/integrations/highergov.py exists")
        return False


def test_preview(opportunity_id: str):
    """Test 3: Preview opportunity."""
    print("\n" + "=" * 60)
    print("Test 3: Preview Opportunity")
    print("=" * 60)
    
    try:
        from src.integrations.highergov import get_opportunity_preview
        
        print(f"Fetching preview for: {opportunity_id}")
        preview = get_opportunity_preview(opportunity_id)
        
        print("\n✓ Preview successful!\n")
        print(f"  Title:      {preview['title']}")
        print(f"  Agency:     {preview['agency']}")
        print(f"  Posted:     {preview['posted']}")
        print(f"  Due Date:   {preview['due']}")
        print(f"  NAICS:      {preview['naics']}")
        print(f"  Set-Aside:  {preview['set_aside']}")
        print(f"  Documents:  {preview['docs']} attachments")
        
        return True, preview
        
    except Exception as e:
        print(f"❌ Preview failed: {e}")
        print("\nPossible causes:")
        print("  - Invalid opportunity ID")
        print("  - API key doesn't have access")
        print("  - Opportunity not found")
        return False, None


def test_download(opportunity_id: str):
    """Test 4: Download documents."""
    print("\n" + "=" * 60)
    print("Test 4: Download Documents")
    print("=" * 60)
    
    response = input("\nDownload documents? This will save files to disk. (y/n): ")
    
    if response.lower() != 'y':
        print("⏭️  Skipping download test")
        return True
    
    try:
        from src.integrations.highergov import ingest_highergov_opportunity
        
        print(f"\nDownloading documents for: {opportunity_id}")
        files = ingest_highergov_opportunity(opportunity_id)
        
        print(f"\n✓ Downloaded {len(files)} file(s):\n")
        
        for file_path in files:
            file_size_mb = file_path.stat().st_size / (1024 * 1024)
            print(f"  - {file_path.name} ({file_size_mb:.2f} MB)")
        
        print(f"\n✓ Files saved to: data/inputs/{opportunity_id}/")
        
        return True
        
    except Exception as e:
        print(f"❌ Download failed: {e}")
        
        error_str = str(e).lower()
        if "expired" in error_str or "60 min" in error_str:
            print("\nℹ️  Download URLs expired. This is normal after 60 minutes.")
            print("   Solution: Run the test again to fetch fresh URLs.")
        
        return False


def main():
    """Run all tests."""
    if len(sys.argv) < 2:
        print("Usage: python scripts/test_highergov_quick.py <opportunity_id>")
        print("\nExample:")
        print("  python scripts/test_highergov_quick.py abc123xyz")
        print("\nGet opportunity IDs from:")
        print("  - HigherGov URL: https://www.highergov.com/opportunity/federal/{ID}")
        print("  - SAM.gov notice IDs also work")
        sys.exit(1)
    
    opportunity_id = sys.argv[1]
    
    print("\n🧪 HigherGov Integration Quick Test")
    print("=" * 60)
    print(f"Opportunity ID: {opportunity_id}")
    print("=" * 60)
    
    results = []
    
    # Test 1: API key
    results.append(("API Key", test_api_key()))
    if not results[0][1]:
        print("\n❌ Cannot continue without API key")
        sys.exit(1)
    
    # Test 2: Import
    results.append(("Import Module", test_import()))
    if not results[1][1]:
        print("\n❌ Cannot continue without module")
        sys.exit(1)
    
    # Test 3: Preview
    test_name = "Preview Opportunity"
    success, preview = test_preview(opportunity_id)
    results.append((test_name, success))
    
    if not success:
        print("\n❌ Cannot continue without valid opportunity")
        sys.exit(1)
    
    # Test 4: Download (optional)
    results.append(("Download Documents", test_download(opportunity_id)))
    
    # Summary
    print("\n" + "=" * 60)
    print("Test Summary")
    print("=" * 60)
    
    for test_name, success in results:
        status = "✓ PASS" if success else "❌ FAIL"
        print(f"  {status}: {test_name}")
    
    passed = sum(1 for _, success in results if success)
    total = len(results)
    
    print(f"\n{passed}/{total} tests passed")
    
    if passed >= 3:  # At least through preview
        print("\n✅ Integration is working!")
        print("\nNext steps:")
        print("  1. Run: streamlit run app.py")
        print("  2. Check 'Use HigherGov Opportunity ID'")
        print(f"  3. Enter: {opportunity_id}")
        print("  4. Click 'Preview' to see details")
        print("  5. Click 'Extract Requirements' to process")
    else:
        print("\n❌ Integration has issues. Review error messages above.")


if __name__ == "__main__":
    main()
"""
Upload Monthly Cache to Hugging Face Space
"""

import os
from pathlib import Path

try:
    from huggingface_hub import HfApi, upload_folder
    print("✓ huggingface_hub is installed")
except ImportError:
    print("✗ huggingface_hub not installed")
    print("\nInstalling...")
    os.system("pip install huggingface_hub")
    from huggingface_hub import HfApi, upload_folder

# Configuration
SPACE_NAME = "princegh410/Crop_price"  # Your HF Space name (note: capital C)
TOKEN = None  # Will prompt for token if not set

def upload_monthly_cache():
    """Upload the monthly_cache folder to HF Space."""
    
    print("="*70)
    print(" UPLOAD MONTHLY CACHE TO HUGGING FACE SPACE")
    print("="*70)
    
    # Check if monthly_cache exists
    cache_dir = Path("monthly_cache")
    if not cache_dir.exists():
        print("✗ Error: monthly_cache folder not found!")
        print("  Run 'python quick_cache_csv_only.py' first to generate it.")
        return
    
    # Count files
    files = list(cache_dir.glob("**/*.json"))
    print(f"\nFound {len(files)} cache files to upload")
    
    # Get token
    token = TOKEN
    if not token:
        print("\n" + "="*70)
        print("HUGGING FACE TOKEN REQUIRED")
        print("="*70)
        print("1. Go to: https://huggingface.co/settings/tokens")
        print("2. Create a token with 'write' access")
        print("3. Paste it below:")
        token = input("\nEnter your HF token: ").strip()
    
    if not token:
        print("✗ No token provided. Aborting.")
        return
    
    # Initialize API
    api = HfApi()
    
    print(f"\n{'='*70}")
    print(f"Uploading to: {SPACE_NAME}")
    print(f"{'='*70}\n")
    
    try:
        # Upload the entire monthly_cache folder (creates a PR instead of direct commit)
        print("Note: Creating a Pull Request (your token doesn't have direct commit access)")
        pr_url = api.upload_folder(
            folder_path="monthly_cache",
            path_in_repo="monthly_cache",
            repo_id=SPACE_NAME,
            repo_type="space",
            token=token,
            commit_message="Update monthly cache (February 2026)",
            create_pr=True  # Create a Pull Request instead of direct commit
        )
        
        print("\n" + "="*70)
        print("✅ PULL REQUEST CREATED!")
        print("="*70)
        print(f"\nCreated PR with {len(files)} cache files to {SPACE_NAME}")
        print(f"\nPull Request URL: {pr_url}")
        print("\nNext steps:")
        print("1. Go to the PR URL above")
        print("2. Review the changes")
        print("3. Click 'Merge Pull Request'")
        print("4. Your Space will rebuild automatically")
        print("\nAll districts should work after merging! 🎉")
        
    except Exception as e:
        print(f"\n✗ Upload failed: {e}")
        print("\nManual upload instructions:")
        print("1. Go to: https://huggingface.co/spaces/{SPACE_NAME}/tree/main")
        print("2. Click 'Add file' → 'Upload files'")
        print("3. Drag and drop the entire 'monthly_cache' folder")
        print("4. Click 'Commit changes to main'")

if __name__ == "__main__":
    upload_monthly_cache()

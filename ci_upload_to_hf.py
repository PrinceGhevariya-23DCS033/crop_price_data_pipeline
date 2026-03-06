"""
CI Upload Script — Upload files to Hugging Face Space
Used by GitHub Actions workflow (.github/workflows/monthly-cache-update.yml)

Reads HF_TOKEN from environment (set as GitHub secret).
Supports two upload modes:
1. Cache-only update (default): Only uploads monthly_cache/
2. Full deployment: Uploads all necessary files including app.py, src/, etc.
"""

import os
import sys
from pathlib import Path
from datetime import datetime

# ─── Config ────────────────────────────────────────────────────────────────────
HF_SPACE_ID = "princegh410/Crop_price"   # <username>/<space-name>  (must match exact case on HF)

# Files/directories to include in full deployment
DEPLOYMENT_FILES = {
    'required': [
        'monthly_cache',     # Cached data (prices, rainfall, NDVI)
        'app.py',            # Main Gradio application
        'src',               # Source code directory
        'district_latlon.csv',  # District coordinates
    ],
    'optional': [
        'production_model',  # Trained models (large, only on force deploy)
        'processed',         # Historical data CSVs (large, only on force deploy)
        'README.md',         # Documentation
        'requirements.txt',  # Python dependencies
    ]
}
# ───────────────────────────────────────────────────────────────────────────────


def check_file_exists(file_path: str) -> bool:
    """Check if file or directory exists."""
    return Path(file_path).exists()


def get_file_size(file_path: str) -> int:
    """Get total size of file or directory in bytes."""
    path = Path(file_path)
    if path.is_file():
        return path.stat().st_size
    elif path.is_dir():
        return sum(f.stat().st_size for f in path.rglob('*') if f.is_file())
    return 0


def format_size(bytes_size: int) -> str:
    """Format bytes to human readable size."""
    for unit in ['B', 'KB', 'MB', 'GB']:
        if bytes_size < 1024.0:
            return f"{bytes_size:.1f} {unit}"
        bytes_size /= 1024.0
    return f"{bytes_size:.1f} TB"


def upload_cache_only(api, token: str) -> None:
    """
    Upload only the monthly_cache directory.
    This is the default mode for monthly updates.
    """
    cache_dir = "monthly_cache"
    
    if not check_file_exists(cache_dir):
        print(f"❌  {cache_dir}/ not found. Run update_monthly_cache.py first.")
        sys.exit(1)
    
    # Count files
    cache_path = Path(cache_dir)
    json_files = list(cache_path.glob("**/*.json"))
    cache_size = get_file_size(cache_dir)
    
    print(f"📦  Cache statistics:")
    print(f"    • Files: {len(json_files)} JSON files")
    print(f"    • Size: {format_size(cache_size)}")
    
    print(f"\n🚀  Uploading {cache_dir}/ → {HF_SPACE_ID} (cache-only mode)")
    
    try:
        commit_url = api.upload_folder(
            folder_path=cache_dir,
            path_in_repo=cache_dir,
            repo_id=HF_SPACE_ID,
            repo_type="space",
            token=token,
            commit_message=f"Update cache: {datetime.now().strftime('%Y-%m-%d')}",
            delete_patterns=None,  # Don't delete files not present locally
        )
        print(f"✅  Cache upload complete!")
        print(f"    Commit: {commit_url}")
        
    except Exception as e:
        print(f"❌  Upload failed: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)


def upload_full_deployment(api, token: str, force: bool = False) -> None:
    """
    Upload all necessary files for a complete deployment.
    Use this for initial deployment or major updates.
    """
    print(f"📦  Preparing full deployment to {HF_SPACE_ID}")
    print(f"    Force mode: {force}")
    
    # Check required files
    missing_required = []
    for item in DEPLOYMENT_FILES['required']:
        if not check_file_exists(item):
            missing_required.append(item)
    
    if missing_required:
        print(f"\n⚠️  Missing required files:")
        for item in missing_required:
            print(f"    • {item}")
        print(f"\n❌  Cannot proceed with deployment. Ensure all files exist.")
        sys.exit(1)
    
    # Check optional files
    print(f"\n📋  Checking files:")
    total_size = 0
    files_to_upload = []
    
    for item in DEPLOYMENT_FILES['required']:
        if check_file_exists(item):
            size = get_file_size(item)
            total_size += size
            files_to_upload.append(item)
            print(f"    ✓ {item} ({format_size(size)})")
    
    for item in DEPLOYMENT_FILES['optional']:
        if check_file_exists(item):
            size = get_file_size(item)
            # Include large files only if force mode is enabled
            if force or size < 100 * 1024 * 1024:  # 100MB threshold
                total_size += size
                files_to_upload.append(item)
                print(f"    ✓ {item} ({format_size(size)})")
            else:
                print(f"    ⊘ {item} ({format_size(size)}) - skipped (use force mode to include)")
        else:
            print(f"    ⊘ {item} - not found")
    
    print(f"\n📊  Total upload size: {format_size(total_size)}")
    
    if total_size > 50 * 1024 * 1024 * 1024:  # 50GB
        print(f"⚠️  Warning: Upload size exceeds 50GB - this may fail on Hugging Face")
    
    # Upload each item separately for better error handling
    print(f"\n🚀  Starting upload to {HF_SPACE_ID}")
    
    failed_uploads = []
    
    for item in files_to_upload:
        try:
            print(f"\n   Uploading {item}...")
            
            path = Path(item)
            if path.is_file():
                api.upload_file(
                    path_or_fileobj=item,
                    path_in_repo=item,
                    repo_id=HF_SPACE_ID,
                    repo_type="space",
                    token=token,
                )
            else:
                api.upload_folder(
                    folder_path=item,
                    path_in_repo=item,
                    repo_id=HF_SPACE_ID,
                    repo_type="space",
                    token=token,
                    delete_patterns=None,
                )
            
            print(f"   ✓ {item} uploaded successfully")
            
        except Exception as e:
            print(f"   ❌ Failed to upload {item}: {e}")
            failed_uploads.append(item)
    
    # Summary
    print(f"\n" + "="*70)
    if failed_uploads:
        print(f"⚠️  Deployment completed with errors")
        print(f"   Failed uploads: {', '.join(failed_uploads)}")
        sys.exit(1)
    else:
        print(f"✅  Full deployment complete!")
        print(f"    Space: https://huggingface.co/spaces/{HF_SPACE_ID}")
        print(f"    Note: Hugging Face may take 2-5 minutes to rebuild and restart")


def main():
    # Get HF token
    token = os.environ.get("HF_TOKEN")
    if not token:
        print("❌  HF_TOKEN environment variable not set.")
        print("    Add it as a GitHub secret: Settings → Secrets → HF_TOKEN")
        sys.exit(1)
    
    # Get deployment mode from environment
    force_deploy = os.environ.get("FORCE_DEPLOY", "false").lower() == "true"
    cache_only = not force_deploy
    
    # Import huggingface_hub
    try:
        from huggingface_hub import HfApi
    except ImportError:
        print("❌  huggingface_hub not installed. Run: pip install huggingface_hub")
        sys.exit(1)
    
    # Initialize API
    api = HfApi()
    
    print("="*70)
    print("📦  Hugging Face Space Deployment")
    print("="*70)
    print(f"Space ID: {HF_SPACE_ID}")
    print(f"Mode: {'Cache-only update' if cache_only else 'Full deployment'}")
    print(f"Time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("="*70)
    
    try:
        if cache_only:
            upload_cache_only(api, token)
        else:
            upload_full_deployment(api, token, force=force_deploy)
        
        print("\n" + "="*70)
        print("✅  Deployment successful!")
        print(f"🌐  View your space: https://huggingface.co/spaces/{HF_SPACE_ID}")
        print("="*70)
        
    except KeyboardInterrupt:
        print("\n\n⚠️  Upload interrupted by user")
        sys.exit(1)
    except Exception as e:
        print(f"\n❌  Unexpected error: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    main()

"""
Verify Files for GitHub Upload
Run this before pushing to GitHub to ensure all required files are present.
"""

import os
from pathlib import Path
from typing import List, Tuple

# Color codes for terminal  
GREEN = "\033[92m"
RED = "\033[91m"
YELLOW = "\033[93m"
BLUE = "\033[94m"
RESET = "\033[0m"

# Required files and folders
REQUIRED_FILES = {
    "Workflow": [
        ".github/workflows/monthly-cache-update.yml"
    ],
    "Source Code": [
        "src/__init__.py",
        "src/api.py",
        "src/cached_fetcher.py",
        "src/config.py",
        "src/confidence.py",
        "src/data_fetchers.py",
        "src/inference.py",
        "src/monthly_cache.py"
    ],
    "Models": [
        "production_model/crop_price_model.pkl",
        "production_model/commodity_encoder.pkl",
        "production_model/district_encoder.pkl",
        "production_model/crop_horizon.pkl",
        "production_model/feature_columns.pkl",
        "production_model/model_metadata.pkl"
    ],
    "Scripts": [
        "update_monthly_cache.py",
        "ci_upload_to_hf.py",
        "app.py"
    ],
    "Data": [
        "NDVI/gujarat_monthly_ndvi_clean_2005_2024_final.csv",
        "district_latlon.csv"
    ],
    "Config": [
        "requirements.txt",
        "requirements_hf.txt",
        "README_HF.md",
        ".gitignore"
    ]
}

REQUIRED_FOLDERS = {
    "Processed Data": "processed",
    "Expected files": "46 CSV files (ajwan_final.csv, tomato_final.csv, etc.)"
}

SHOULD_NOT_EXIST_IN_GIT = [
    "monthly_cache",
    "__pycache__",
    ".env"
]


def check_file_exists(filepath: str) -> Tuple[bool, str]:
    """Check if file exists and return status."""
    if os.path.exists(filepath):
        size = os.path.getsize(filepath)
        return True, f"{size:,} bytes"
    return False, "Missing"


def check_folder_files(folder: str, pattern: str = "*.csv") -> Tuple[bool, int]:
    """Check folder and count files matching pattern."""
    if not os.path.exists(folder):
        return False, 0
    
    from pathlib import Path
    files = list(Path(folder).glob(pattern))
    return True, len(files)


def format_status(exists: bool, info: str = "") -> str:
    """Format status with color."""
    if exists:
        return f"{GREEN}✓{RESET} {info}"
    else:
        return f"{RED}✗ {info}{RESET}"


def main():
    """Run verification."""
    print("="*80)
    print(f"{BLUE}📋 GitHub Upload Verification{RESET}")
    print("="*80)
    print()
    
    total_checked = 0
    total_found = 0
    missing_files = []
    
    # Check required files
    for category, files in REQUIRED_FILES.items():
        print(f"\n{BLUE}{category}:{RESET}")
        for file in files:
            exists, info = check_file_exists(file)
            print(f"  {format_status(exists, file)} {info if exists else ''}")
            total_checked += 1
            if exists:
                total_found += 1
            else:
                missing_files.append(file)
    
    # Check processed folder
    print(f"\n{BLUE}Processed Data:{RESET}")
    exists, count = check_folder_files("processed", "*_final.csv")
    status = f"{count} CSV files found"
    if count >= 40:
        print(f"  {GREEN}✓{RESET} processed/ folder: {status}")
        total_found += 1
    elif count > 0:
        print(f"  {YELLOW}⚠{RESET} processed/ folder: {status} (expected ~46)")
    else:
        print(f"  {RED}✗{RESET} processed/ folder: Not found or empty")
        missing_files.append("processed/*.csv files")
    total_checked += 1
    
    # Check files that should NOT be in git
    print(f"\n{BLUE}Files to Exclude (should NOT be present):{RESET}")
    excluded_found = []
    for item in SHOULD_NOT_EXIST_IN_GIT:
        if os.path.exists(item):
            print(f"  {YELLOW}⚠{RESET} {item}/ exists (should be in .gitignore)")
            excluded_found.append(item)
        else:
            print(f"  {GREEN}✓{RESET} {item}/ not present (good)")
    
    # Check .gitignore
    print(f"\n{BLUE}Checking .gitignore:{RESET}")
    if os.path.exists(".gitignore"):
        with open(".gitignore", "r") as f:
            gitignore_content = f.read()
        
        important_ignores = ["monthly_cache", "__pycache__", ".env"]
        for pattern in important_ignores:
            if pattern in gitignore_content:
                print(f"  {GREEN}✓{RESET} {pattern} is ignored")
            else:
                print(f"  {YELLOW}⚠{RESET} {pattern} NOT in .gitignore")
    else:
        print(f"  {RED}✗{RESET} .gitignore not found")
    
    # Summary
    print("\n" + "="*80)
    print(f"{BLUE}📊 Summary:{RESET}")
    print("="*80)
    
    percentage = (total_found / total_checked * 100) if total_checked > 0 else 0
    
    print(f"\nFiles checked: {total_checked}")
    print(f"Files found: {GREEN}{total_found}{RESET}")
    print(f"Files missing: {RED}{len(missing_files)}{RESET}")
    print(f"Completion: {percentage:.1f}%")
    
    if missing_files:
        print(f"\n{RED}Missing files:{RESET}")
        for file in missing_files:
            print(f"  • {file}")
    
    if excluded_found:
        print(f"\n{YELLOW}Files/folders that should be excluded:{RESET}")
        for item in excluded_found:
            print(f"  • {item} (add to .gitignore)")
    
    # Final verdict
    print("\n" + "="*80)
    if percentage >= 95 and not excluded_found:
        print(f"{GREEN}✅ READY TO UPLOAD!{RESET}")
        print("\nNext steps:")
        print("  1. git add .")
        print("  2. git commit -m 'Initial commit: Monthly cache workflow'")
        print("  3. git push origin main")
        print("  4. Add GitHub secrets: HF_TOKEN and DATA_GOV_API_KEY")
    elif percentage >= 95:
        print(f"{YELLOW}⚠️  ALMOST READY{RESET}")
        print("\nFix excluded files first:")
        for item in excluded_found:
            print(f"  • Ensure {item} is in .gitignore")
    else:
        print(f"{RED}❌ NOT READY{RESET}")
        print("\nFix missing files first.")
    print("="*80)
    
    return 0 if percentage >= 95 else 1


if __name__ == "__main__":
    import sys
    sys.exit(main())

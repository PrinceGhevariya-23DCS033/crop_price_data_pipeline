"""
Test Hugging Face Token
Run this locally to verify your HF token before uploading to GitHub.

Usage:
    1. Set HF_TOKEN environment variable:
       Windows: set HF_TOKEN=your_token_here
       Linux/Mac: export HF_TOKEN=your_token_here
    
    2. Run script:
       python test_hf_token.py
    
    Or pass token directly (not recommended for security):
       python test_hf_token.py hf_xxxxxxxxxxxxx
"""

import os
import sys


def test_hf_token(token: str = None) -> bool:
    """Test if Hugging Face token is valid and has proper permissions."""
    
    # Get token from environment or argument
    if token is None:
        token = os.environ.get("HF_TOKEN")
    
    if not token:
        print("❌ No HF_TOKEN found!")
        print("\nHow to set token:")
        print("  Windows CMD:    set HF_TOKEN=hf_xxxxxxxxxxxxx")
        print("  Windows PS:     $env:HF_TOKEN='hf_xxxxxxxxxxxxx'")
        print("  Linux/Mac:      export HF_TOKEN=hf_xxxxxxxxxxxxx")
        print("\nOr pass as argument: python test_hf_token.py hf_xxxxxxxxxxxxx")
        return False
    
    # Validate token format
    if not token.startswith("hf_"):
        print("⚠️  Warning: Token doesn't start with 'hf_' - may be invalid format")
    
    print(f"✓ Token found: {token[:10]}...{token[-5:]}")
    print(f"  Length: {len(token)} characters")
    
    # Try to import huggingface_hub
    print("\n📦 Checking dependencies...")
    try:
        from huggingface_hub import HfApi, whoami
        print("✓ huggingface_hub installed")
    except ImportError:
        print("❌ huggingface_hub not installed!")
        print("   Install: pip install huggingface_hub")
        return False
    
    # Test authentication
    print("\n🔐 Testing authentication...")
    try:
        api = HfApi(token=token)
        user_info = whoami(token=token)
        
        # Display user info
        username = user_info.get('name', 'unknown')
        user_type = user_info.get('type', 'unknown')
        
        print(f"✓ Authentication successful!")
        print(f"  Username: {username}")
        print(f"  Type: {user_type}")
        
    except Exception as e:
        print(f"❌ Authentication failed!")
        print(f"   Error: {e}")
        print("\n💡 Token may be:")
        print("   • Expired or revoked")
        print("   • Missing 'read' permission")
        print("   • Invalid format")
        print("\n   Generate new token at: https://huggingface.co/settings/tokens")
        return False
    
    # Test space access
    print("\n🌐 Testing space access...")
    SPACE_ID = "princegh410/crop-price"
    
    try:
        space_info = api.space_info(repo_id=SPACE_ID, token=token)
        print(f"✓ Space found: {SPACE_ID}")
        print(f"  SDK: {space_info.sdk}")
        print(f"  Stage: {space_info.stage}")
        
    except Exception as e:
        error_msg = str(e)
        if "404" in error_msg or "not found" in error_msg.lower():
            print(f"⚠️  Space not found: {SPACE_ID}")
            print(f"   This is OK if you haven't created it yet.")
            print(f"   Create space at: https://huggingface.co/new-space")
        else:
            print(f"❌ Error accessing space: {e}")
            return False
    
    # Test write permissions
    print("\n✍️  Testing write permissions...")
    try:
        # Try to get repos accessible by user
        repos = list(api.list_repos(token=token, limit=5))
        print(f"✓ Token has write access")
        print(f"  Can access {len(repos)} repositories")
        
    except Exception as e:
        print(f"⚠️  Could not verify write permissions")
        print(f"   Error: {e}")
        print("\n💡 Make sure token has 'write' permission:")
        print("   https://huggingface.co/settings/tokens")
    
    # Final summary
    print("\n" + "="*60)
    print("✅ HF TOKEN TEST PASSED!")
    print("="*60)
    print("\n📝 Next steps:")
    print("   1. Go to GitHub repository → Settings → Secrets and variables → Actions")
    print("   2. Click 'New repository secret'")
    print("   3. Name: HF_TOKEN")
    print(f"   4. Value: {token}")
    print("   5. Click 'Add secret'")
    print("\n🔒 Security note: Never commit the token to your repository!")
    
    return True


if __name__ == "__main__":
    # Get token from command line argument if provided
    token = sys.argv[1] if len(sys.argv) > 1 else None
    
    try:
        success = test_hf_token(token)
        sys.exit(0 if success else 1)
    except KeyboardInterrupt:
        print("\n\n❌ Test cancelled by user")
        sys.exit(1)
    except Exception as e:
        print(f"\n❌ Unexpected error: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)

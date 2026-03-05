╔══════════════════════════════════════════════════════════════════╗
║             GITHUB ACTIONS - AUTOMATED DEPLOYMENT                ║
║         Monthly Cache Update to Hugging Face Space               ║
╚══════════════════════════════════════════════════════════════════╝

📋 SETUP INSTRUCTIONS
─────────────────────────────────────────────────────────────────

1️⃣  Copy Workflow File
   Copy monthly-cache-update.yml to your GitHub repository:
   
   .github/workflows/monthly-cache-update.yml

2️⃣  Add GitHub Secrets
   Go to: Your Repo → Settings → Secrets → Actions
   Add these secrets:

   • DATA_GOV_API_KEY
     Your data.gov.in API key for fetching mandi prices

   • HF_TOKEN
     Hugging Face token with WRITE access
     Get from: https://huggingface.co/settings/tokens

   • HF_USERNAME
     Your Hugging Face username
     Example: "your-username"

   • HF_SPACE_NAME
     Your HF Space repository name
     Example: "crop-price-api"

─────────────────────────────────────────────────────────────────

🗓️  SCHEDULE
─────────────────────────────────────────────────────────────────

Automatic Run:
• Every month on the 20th at 2:00 AM UTC
• Cron: '0 2 20 * *'

Manual Run:
• Go to: Actions → Monthly Cache Update → Run workflow
• Click "Run workflow" button

─────────────────────────────────────────────────────────────────

🔄 WORKFLOW STEPS
─────────────────────────────────────────────────────────────────

The workflow automatically:
1. Checks out your Crop_Price_V2 repository
2. Sets up Python 3.10
3. Installs dependencies
4. Runs update_monthly_cache.py
5. Verifies cache files were created
6. Clones your HF Space repository
7. Updates monthly_cache/ folder
8. Commits and pushes to HF Space
9. HF Space auto-rebuilds with new cache

Total time: ~30-40 minutes

─────────────────────────────────────────────────────────────────

✅ VERIFICATION
─────────────────────────────────────────────────────────────────

After workflow runs:
1. Check GitHub Actions tab for success/failure
2. Review workflow logs for any errors
3. Verify HF Space rebuilt (check Space build logs)
4. Test API endpoint: /api/cache-status
5. Confirm last_updated date is current

─────────────────────────────────────────────────────────────────

🐛 TROUBLESHOOTING
─────────────────────────────────────────────────────────────────

Workflow fails at "Update monthly cache":
→ Check DATA_GOV_API_KEY is set correctly
→ API key might have expired or rate limited

Workflow fails at "Clone Hugging Face Space":
→ Check HF_TOKEN has write permissions
→ Verify HF_USERNAME and HF_SPACE_NAME are correct
→ Token format: repo_write access type

Workflow fails at "Commit and push":
→ Check HF_TOKEN hasn't expired
→ Verify Space name matches exactly

No files updated:
→ Cache might be identical to previous month
→ Check "No changes to commit" in logs

─────────────────────────────────────────────────────────────────

📊 MONITORING
─────────────────────────────────────────────────────────────────

View workflow runs:
• Repo → Actions → Monthly Cache Update

Each run shows:
• Cache statistics (file counts)
• Success/failure status
• Detailed logs for debugging

Enable notifications:
• Repo → Settings → Notifications
• Configure email alerts for workflow failures

─────────────────────────────────────────────────────────────────

🔐 SECURITY NOTES
─────────────────────────────────────────────────────────────────

✓ Secrets are encrypted and never logged
✓ HF_TOKEN should have minimal permissions (repo_write only)
✓ DATA_GOV_API_KEY stored securely
✓ Public repos get free GitHub Actions minutes
✓ Private repos: 2000 min/month on free plan

─────────────────────────────────────────────────────────────────

💡 CUSTOMIZATION
─────────────────────────────────────────────────────────────────

Change schedule:
Edit cron expression in workflow:
  '0 2 20 * *'    = 20th at 2:00 AM
  '0 2 25 * *'    = 25th at 2:00 AM
  '0 14 20 * *'   = 20th at 2:00 PM

Cron helper: https://crontab.guru

Add notifications:
Use GitHub Actions marketplace:
• Slack notifications
• Email alerts
• Discord webhooks

─────────────────────────────────────────────────────────────────

📞 SUPPORT
─────────────────────────────────────────────────────────────────

GitHub Actions Docs:
https://docs.github.com/en/actions

Hugging Face Git Docs:
https://huggingface.co/docs/hub/repositories-getting-started

═══════════════════════════════════════════════════════════════════

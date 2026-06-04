#!/bin/bash

# Deploy to Render with persistent disk fix
# This script commits and pushes the changes to enable data persistence

echo "🚀 Deploying Hospital Management System to Render..."
echo ""

# Check if there are changes to commit
if [[ -n $(git status -s) ]]; then
    echo "📝 Changes detected. Committing..."
    git add render.yaml Dockerfile
    git commit -m "Fix: Add persistent disk for database storage on Render"
    echo "✅ Changes committed"
else
    echo "ℹ️  No changes to commit"
fi

echo ""
echo "📤 Pushing to GitHub..."
git push origin main

echo ""
echo "✅ Deployment initiated!"
echo ""
echo "📋 Next steps:"
echo "1. Go to your Render dashboard: https://dashboard.render.com"
echo "2. Wait for deployment to complete (2-3 minutes)"
echo "3. Check logs for: '✅ Added 5 doctors successfully'"
echo "4. Visit your app and test OPD registration"
echo ""
echo "🔍 Verify persistent disk:"
echo "   - Go to your service → Disks tab"
echo "   - Should see 'hospital-data' mounted at /data"
echo ""

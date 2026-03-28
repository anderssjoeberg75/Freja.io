#!/bin/bash
# scripts/deploy_remote.sh
# Remote deployment script for Freja.io on freja.andrix.se

# --- CONFIGURATION ---
REMOTE_HOST="freja.andrix.se"
REMOTE_USER="root"
REMOTE_DIR="/opt/Freja.io"
REPO_URL="https://github.com/anderssjoeberg75/Freja.io.git"

echo "🚀 Starting remote deployment to $REMOTE_HOST..."

# 1. Update GitHub with local changes
echo "📤 Pushing local changes to GitHub..."
bash ./update_git.sh

if [ $? -ne 0 ]; then
    echo "❌ Local push failed. Aborting deployment."
    exit 1
fi

# 2. Update the remote server and restart services
echo "📡 Connecting to $REMOTE_HOST via SSH..."
ssh "$REMOTE_USER@$REMOTE_HOST" <<EOF
    echo "📂 Navigating to $REMOTE_DIR..."
    cd "$REMOTE_DIR" || { echo "❌ Directory $REMOTE_DIR not found!"; exit 1; }

    echo "📥 Pulling latest changes from main..."
    git pull origin main

    echo "📦 Updating dependencies (backend)..."
    if [ -d "venv" ]; then
        ./venv/bin/pip install -r requirements.txt
    else
        python3 -m venv venv
        ./venv/bin/pip install -r requirements.txt
    fi

    echo "📦 Updating dependencies (frontend)..."
    cd client && npm install && npm run build
    cd ..

    echo "🔄 Restarting Freja services..."
    systemctl daemon-reload
    systemctl restart freja.service
    systemctl restart freja-vault-unseal.service

    echo "✅ Remote update complete!"
EOF

if [ $? -eq 0 ]; then
    echo "-------------------------------------------------------"
    echo "✨ DEPLOYMENT SUCCESSFUL!"
    echo "🌍 App should be live at: http://$REMOTE_HOST"
    echo "-------------------------------------------------------"
else
    echo "❌ Deployment failed during remote execution."
    exit 1
fi

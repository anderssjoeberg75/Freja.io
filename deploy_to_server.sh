#!/bin/bash
set -e

SERVER_IP="192.168.107.17"
TARGET_DIR="/opt/mainframe"
USER="root" # Change this if you use 'ubuntu' or another user

echo "🚀 Deploying DAA Mainframe to $SERVER_IP:$TARGET_DIR..."

# Ensure target directory exists
echo "📁 Creating target directory..."
ssh $USER@$SERVER_IP "mkdir -p $TARGET_DIR"

# Transfer Files
# Transfer Files
echo "📦 Syncing Mainframe (Backend)..."
rsync -avz --exclude 'venv' --exclude '__pycache__' --exclude 'client' --exclude '.git' --exclude 'logs' --exclude 'temp_repos' ./ $USER@$SERVER_IP:$TARGET_DIR/mainframe/

echo "⚛️ Syncing Client (Frontend)..."
rsync -avz --exclude 'node_modules' --exclude 'dist' ./client/ $USER@$SERVER_IP:$TARGET_DIR/client/

echo "📜 Syncing Setup Scripts..."
scp setup_mainframe.sh $USER@$SERVER_IP:$TARGET_DIR/
scp mainframe.service $USER@$SERVER_IP:$TARGET_DIR/

echo "✅ Transfer Complete!"
echo "👉 Now SSH into the server and run:"
echo "   ssh $USER@$SERVER_IP"
echo "   cd $TARGET_DIR"
echo "   ./setup_mainframe.sh"

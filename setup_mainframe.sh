#!/bin/bash
set -e

echo "🚀 Initializing DAA Mainframe..."

# 1. System Dependencies
echo "📦 Installing System Dependencies..."
if command -v apt-get &> /dev/null; then
    sudo apt-get update && sudo apt-get install -y python3-venv python3-pip python3-full npm ffmpeg
fi

# 2. Mainframe (Backend) Setup
echo "🐍 Setting up Mainframe Backend..."
cd mainframe

# Force remove old/broken venv
if [ -d "venv" ]; then
    echo "Filesystem venv detected. Removing to ensure clean state..."
    rm -rf venv
fi

echo "Creating virtual environment..."
# Explicitly use python3 to create the venv
python3 -m venv venv

# Activate and install
source venv/bin/activate
echo "Upgrading pip..."
pip install --upgrade pip

echo "Installing dependencies..."
pip install -r requirements.txt
cd ..

# 3. Client (Frontend) Setup
echo "⚛️ Setting up Client Frontend..."
cd client
if [ ! -d "node_modules" ]; then
    npm install
fi
cd ..

echo "✅ DAA Mainframe Setup Complete!"
echo "👉 To start backend: cd mainframe && source venv/bin/activate && python main.py"
echo "👉 To start frontend: cd client && npm run dev"

#!/bin/bash
set -e

# --- 1. CONFIGURATION ---
PROJECT_DIR="/opt/Freja.io"
REPO_URL="https://github.com/anderssjoeberg75/freja.io.git"
SERVER_IP=$(curl -s ifconfig.me)

# Attempt to detect the IP address you are connecting from via SSH
USER_IP=$(last -i -1 -F | awk 'NR==1 {print $3}')

echo "🌟 Starting total installation in $PROJECT_DIR"
echo "🖥️ Server IP: $SERVER_IP"
echo "🏠 Detected User IP: $USER_IP"

# --- 2. PREPARE DIRECTORIES & GIT CLONE ---
echo "📂 Preparing directories and cloning project..."
sudo mkdir -p /opt
cd /opt
if [ -d "$PROJECT_DIR" ]; then
    echo "⚠️ Directory already exists. Updating existing code..."
    cd "$PROJECT_DIR" && git pull
else
    sudo git clone "$REPO_URL" "$PROJECT_DIR"
fi

# --- 3. SYSTEM PACKAGES ---
echo "📦 Installing dependencies..."
sudo apt-get update && sudo apt-get upgrade -y -f
sudo apt-get install -y python3-venv python3-pip python3-full npm ffmpeg gpg curl lsb-release ufw

# --- 4. HASHICORP VAULT ---
echo "🔐 Configuring Vault..."
if ! command -v vault &> /dev/null; then
    curl -fsSL https://apt.releases.hashicorp.com/gpg | sudo gpg --dearmor -o /usr/share/keyrings/hashicorp-archive-keyring.gpg
    echo "deb [signed-by=/usr/share/keyrings/hashicorp-archive-keyring.gpg] https://apt.releases.hashicorp.com $(lsb_release -cs) main" | sudo tee /etc/apt/sources.list.d/hashicorp.list
    sudo apt update && sudo apt install -y vault
fi

# Configure Vault for HTTP (tls_disable = 1)
sudo mkdir -p /opt/vault/data
sudo chown -R vault:vault /opt/vault/data
sudo cat <<EOF > /etc/vault.d/vault.hcl
storage "file" { path = "/opt/vault/data" }
listener "tcp" {
  address     = "127.0.0.1:8200"
  tls_disable = "1"
}
ui = true
disable_mlock = true
EOF

sudo systemctl restart vault
export VAULT_ADDR='http://127.0.0.1:8200'

# --- 5. BACKEND SETUP ---
echo "🐍 Setting up Python environment..."
cd "$PROJECT_DIR"
chmod +x setup_mainframe.sh
./setup_mainframe.sh

# Create .env with correct origins for your IP
cat <<EOF > .env
GOOGLE_API_KEY=
OPENAI_API_KEY=
ADMIN_API_TOKEN=freja_admin_pass
ALLOWED_ORIGINS=http://localhost:5173,http://127.0.0.1:5173,http://$SERVER_IP:5173,http://$USER_IP:5173
VAULT_URL=http://127.0.0.1:8200
VAULT_TOKEN=
EOF

# --- 6. FRONTEND SETUP ---
echo "⚛️ Installing Frontend..."
cd client
npm install

# Point frontend to the correct API address
cat <<EOF > src/config.js
export const API_BASE_URL = "http://$SERVER_IP:8000";
EOF

# Allow external connections to Vite (--host)
sed -i 's/"dev": "vite"/"dev": "vite --host 0.0.0.0"/g' package.json
cd ..

# --- 7. FIREWALL & SYSTEMD ---
echo "🛡️ Configuring firewall and services..."
sudo ufw allow ssh
sudo ufw allow 5173/tcp
sudo ufw allow 8000/tcp
echo "y" | sudo ufw enable

# Update paths in systemd service files
sed -i "s|/home/netadmin/freja.io|$PROJECT_DIR|g" freja.service
sed -i "s|/home/netadmin/freja.io|$PROJECT_DIR|g" freja-vault-unseal.service

sudo cp freja.service /etc/systemd/system/
sudo cp freja-vault-unseal.service /etc/systemd/system/
sudo systemctl daemon-reload

echo ""
echo "-------------------------------------------------------"
echo "✅ TOTAL INSTALLATION COMPLETE!"
echo "-------------------------------------------------------"
echo "HOW TO MANUALLY CHANGE YOUR USER IP:"
echo "If the detection was incorrect or if you change networks:"
echo "1. Open .env: nano $PROJECT_DIR/.env"
echo "2. Find ALLOWED_ORIGINS and add your IP (e.g., ,http://1.2.3.4:5173)"
echo "3. Save (Ctrl+O) and Exit (Ctrl+X)."
echo "4. Run: sudo systemctl restart freja"
echo "-------------------------------------------------------"
echo "NEXT STEPS:"
echo "1. Run: export VAULT_ADDR='http://127.0.0.1:8200'"
echo "2. Run: vault operator init"
echo "3. IMPORTANT: Save the Root Token and Unseal Keys!"
echo "-------------------------------------------------------"

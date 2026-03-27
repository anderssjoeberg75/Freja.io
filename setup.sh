#!/bin/bash
set -e

# --- 1. CONFIGURATION ---
PROJECT_DIR="/opt/Freja.io"
REPO_URL="https://github.com/anderssjoeberg75/freja.io.git"
SERVER_IP=$(curl -s ifconfig.me)

# Detect the IP address you are connecting from via SSH
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
    cd "$PROJECT_DIR" && sudo git pull
else
    sudo git clone "$REPO_URL" "$PROJECT_DIR"
fi

# --- 3. SYSTEM PACKAGES ---
echo "📦 Installing system dependencies..."
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

# --- 5. BACKEND SETUP (Integrated setup_mainframe logic) ---
echo "🐍 Setting up Backend environment..."
cd "$PROJECT_DIR"

# Ensure a clean virtual environment
if [ -d "venv" ]; then
    echo "Removing old venv..."
    sudo rm -rf venv
fi

echo "Creating virtual environment..."
python3 -m venv venv

echo "Installing Python dependencies..."
source venv/bin/activate
pip install --upgrade pip
pip install -r requirements.txt

# Create .env with correct origins for your detected IP
cat <<EOF > .env
GOOGLE_API_KEY=
OPENAI_API_KEY=
ADMIN_API_TOKEN=freja_admin_pass
ALLOWED_ORIGINS=http://localhost:5173,http://127.0.0.1:5173,http://$SERVER_IP:5173,http://$USER_IP:5173
VAULT_URL=http://127.0.0.1:8200
VAULT_TOKEN=
EOF

# --- 6. FRONTEND SETUP ---
echo "⚛️ Installing Frontend dependencies..."
cd client
npm install

# Point frontend configuration to the server's public IP
cat <<EOF > src/config.js
export const API_BASE_URL = "http://$SERVER_IP:8000";
EOF

# Configure Vite to allow external connections (--host)
sed -i 's/"dev": "vite"/"dev": "vite --host 0.0.0.0"/g' package.json
cd ..

# --- 7. FIREWALL & SYSTEMD SERVICE CREATION ---
echo "🛡️ Configuring firewall and creating systemd services..."
sudo ufw allow ssh
sudo ufw allow 5173/tcp
sudo ufw allow 8000/tcp
echo "y" | sudo ufw enable

# Create Freja Main Service
sudo cat <<EOF > /etc/systemd/system/freja.service
[Unit]
Description=Freja.io Backend and Frontend Service
After=network.target

[Service]
Type=simple
User=root
WorkingDirectory=$PROJECT_DIR
ExecStart=/bin/bash $PROJECT_DIR/start.sh
Restart=always
RestartSec=10
KillSignal=SIGTERM

[Install]
WantedBy=multi-user.target
EOF

# Create Vault Auto-Unseal Service
sudo cat <<EOF > /etc/systemd/system/freja-vault-unseal.service
[Unit]
Description=Freja Auto-Unseal for HashiCorp Vault
After=vault.service
BindsTo=vault.service

[Service]
Type=oneshot
ExecStart=/bin/bash $PROJECT_DIR/scripts/auto_unseal.sh
RemainAfterExit=true
User=root
Environment="VAULT_ADDR=http://127.0.0.1:8200"

[Install]
WantedBy=vault.service
EOF

sudo systemctl daemon-reload

echo ""
echo "-------------------------------------------------------"
echo "✅ TOTAL INSTALLATION COMPLETE!"
echo "-------------------------------------------------------"
echo "MANUAL IP CONFIGURATION (If needed):"
echo "If your home IP changes, update it here:"
echo "1. Edit .env: nano $PROJECT_DIR/.env"
echo "2. Add your new IP to ALLOWED_ORIGINS (e.g., ,http://1.2.3.4:5173)"
echo "3. Restart: sudo systemctl restart freja"
echo "-------------------------------------------------------"
echo "NEXT STEPS:"
echo "1. Run: export VAULT_ADDR='http://127.0.0.1:8200'"
echo "2. Run: vault operator init"
echo "3. IMPORTANT: Save your Root Token and Unseal Keys!"
echo "-------------------------------------------------------"

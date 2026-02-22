#!/bin/bash
# Auto-unseal script for local development/home server convenience.
# Security notice: Storing unseal keys in plaintext on the same disk 
# bypasses Vault's protection against physical disk theft.

export VAULT_ADDR='https://127.0.0.1:8200'

# Wait a few seconds to ensure Vault is fully up and listening
sleep 5

# Unseal using 3 of the 5 Shamir shares
/usr/bin/vault operator unseal -tls-skip-verify SXtzDXzaraHJeOA3eBVgtuw/ypqB37K++h7L1LC6xmsu
/usr/bin/vault operator unseal -tls-skip-verify oY+IlSpFXYJl/fgJEgdqsonIfG91sN8vNDPLuI/LaVoH
/usr/bin/vault operator unseal -tls-skip-verify lUiSaONXizoVaVPMGDrFxFcPUQW2TY8BtULVUeSdDLPt

echo "Vault should now be unsealed."

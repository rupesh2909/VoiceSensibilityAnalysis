#!/bin/bash

set -e

echo "========================================"
echo "Voice Sensibility Analysis - Startup"
echo "========================================"

# SSH runtime directory
mkdir -p /run/sshd
chmod 755 /run/sshd

# Generate missing SSH host keys
ssh-keygen -A

# Root SSH directory
mkdir -p /root/.ssh
chmod 700 /root/.ssh

# Restore authorized SSH keys from persistent storage
AUTHORIZED_KEYS_SOURCE="/workspace/VoiceSensibilityAnalysis/scripts/runpod_authorized_keys"

if [ -f "$AUTHORIZED_KEYS_SOURCE" ]; then
    cp "$AUTHORIZED_KEYS_SOURCE" /root/.ssh/authorized_keys
    chmod 600 /root/.ssh/authorized_keys
    echo "SSH authorized keys restored"
else
    echo "WARNING: Persistent authorized keys file not found"
fi

# Start SSH daemon
if pgrep -x sshd >/dev/null 2>&1; then
    echo "SSH daemon already running"
else
    echo "Starting SSH daemon..."
    /usr/sbin/sshd
    echo "SSH daemon started"
fi

# Verify SSH
if ss -lnt 2>/dev/null | grep -q ':22 '; then
    echo "SSH is listening on port 22"
else
    echo "ERROR: SSH is NOT listening on port 22"
    exit 1
fi

echo "========================================"
echo "Startup completed successfully"
echo "========================================"

# Keep the container alive
exec tail -f /dev/null

#!/bin/bash

echo "=== Alchemia Auto Hunt Setup ==="

# Update packages
pkg update -y
pkg upgrade -y

# Install dependencies
echo "Installing dependencies..."
pkg install -y python python-pip android-tools tesseract opencv-python
pkg install -y libjpeg-turbo libpng libwebp

# Install Python packages
echo "Installing Python packages..."
pip install --upgrade pip
pip install -r requirements.txt

# Create directories
echo "Creating directories..."
mkdir -p config/templates/monsters
mkdir -p config/templates/buttons
mkdir -p data/screenshots
mkdir -p data/logs

# Create empty files
touch data/learned_positions.json
echo "{}" > data/learned_positions.json

# Setup ADB
echo "Starting ADB..."
adb kill-server
adb start-server

echo ""
echo "=== Setup Complete ==="
echo "Sekarang:"
echo "1. Aktifkan Wireless Debugging di HP"
echo "2. adb pair IP:PAIRING_PORT"
echo "3. adb connect IP:CONNECT_PORT"
echo "4. Edit config/settings.yaml"
echo "5. Capture template monster"
echo "6. bash run.sh"

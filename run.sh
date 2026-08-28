#!/bin/bash

echo "=== Alchemia Auto Hunt ==="

# Check ADB
adb devices

# Run
python main.py

# Show log kalau error
if [ $? -ne 0 ]; then
    echo "Error! Cek log:"
    tail -30 data/logs/hunter.log
fi

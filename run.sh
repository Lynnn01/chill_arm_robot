#!/bin/bash
# Navigate to the project directory regardless of where the script was launched from
cd "$(dirname "$0")"

echo "=========================================="
echo "  Starting Chill Arm Robot..."
echo "=========================================="

echo "[1/2] Updating latest code from Git..."
git pull

echo "[2/2] Launching Application (main.py)..."
if command -v python3 &>/dev/null; then
    python3 main.py
else
    python main.py
fi

# If exited with error, keep terminal open to view error messages
if [ $? -ne 0 ]; then
    echo ""
    echo "[!] Application exited with an error."
    read -p "Press [Enter] to close..."
fi
#!/bin/bash
echo "Installing PrivatePeer Chat..."
sudo apt-get update
sudo apt-get install -y python3 python3-pip python3-venv tor

python3 -m venv ppchat-env
source ppchat-env/bin/activate

pip install -r requirements.txt

echo "Configuring Tor..."
sudo systemctl restart tor
echo "Installation complete!"
echo "Run with: source ppchat-env/bin/activate && python3 src/privatepeer_chat.py"
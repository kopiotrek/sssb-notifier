#!/bin/bash
export GMAIL_USER=""
export RECEIVING_USER=""
export GMAIL_PASSWORD=""

# Activate the virtual environment
source ~/Documents/sssb-notifier/sssb_venv/bin/activate

# Run the Python script
python3 ~/Documents/sssb-notifier/v2-sssb-notifier.py

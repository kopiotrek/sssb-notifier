#!/bin/bash
export GMAIL_USER="kopiotrek@gmail.com"
export RECEIVING_USER="kopiotrek@gmail.com"
export GMAIL_PASSWORD="wlqbvipuflnkyugp"

# Activate the virtual environment
source ~/Documents/sssb-notifier/sssb_venv/bin/activate

# Run the Python script
python3 ~/Documents/sssb-notifier/v2-sssb-notifier.py

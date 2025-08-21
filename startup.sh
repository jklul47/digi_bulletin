#!/bin/bash
# Startup script for Digital Bulletin Board

# Navigate to the project directory
cd /home/jklul/dev/digi_bulletin

# Countdown timer before starting
echo "Starting Digital Bulletin Board in 5 seconds..."
sleep 5

# Start the bulletin board
python run.py

# Exit the script and shut down after 12 hours
sleep 43200
sudo shutdown now

# NOTES
#
# Make it executable
# sudo chmod +x /usr/local/bin/my-startup-script.sh
#
# Put service file in /etc/systemd/system/
#
# Reload systemd to recognize new service
# sudo systemctl daemon-reload
# 
# Enable service to start on boot
# sudo systemctl enable my-startup-script.service
# 
# Start service immediately (optional, for testing)
# sudo systemctl start my-startup-script.service
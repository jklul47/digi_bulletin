#!/bin/bash
PROJECT_DIR="/home/nljk/dev/digi_bulletin"

# Logging function
log() {
    echo "$(date '+%Y-%m-%d %H:%M:%S') - $1" | tee -a /var/log/bulletin-board.log
}

log "=== Digital Bulletin Board Startup ==="

# Ensure script has full PATH
export PATH="/usr/local/sbin:/usr/local/bin:/usr/sbin:/usr/bin:/sbin:/bin"
export DISPLAY=:0
export XAUTHORITY=/home/nljk/.Xauthority

# Basic setup
cd "$PROJECT_DIR" || { log "ERROR: Cannot find project directory $PROJECT_DIR"; exit 1; }

# Additional wait for system stability
log "Waiting for system to stabilize... (1/2)"
sleep 10

log "Waiting for system to stabilize... (2/2)"
sleep 10

log "Starting bulletin board with 6-hour timeout..."

# Use timeout command to automatically kill after 6 hours
# timeout sends SIGTERM, then SIGKILL if needed
if timeout 60 python3 run.py; then      # Testing purposes
# if timeout 21600 python3 run.py; then
    log "Bulletin board completed normally"
    exit 0
else
    exit_code=$?
    if [ $exit_code -eq 124 ]; then
        log "6 hours completed - timeout reached (this is normal)"
        exit 0  # Normal completion, don't restart
    else
        log "Bulletin board failed with exit code $exit_code"
        exit 1  # Actual failure, allow restart
    fi
fi

log "Shutting down system"
sudo shutdown now

### LOG NOTES
# Application logs
# tail -f bulletin.log
# 
# System startup logs  
# tail -f /var/log/bulletin-board.log
# 
# Systemd service logs
# journalctl -u startup.service -f
# 
# All bulletin-board related systemd logs
# journalctl -t bulletin-board -f
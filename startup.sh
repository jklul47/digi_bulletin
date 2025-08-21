#!/bin/bash
# Digital Bulletin Board Startup Script - Ultimate Simple Version

PROJECT_DIR="/home/nljk/dev/digi_bulletin"

# Logging function
log() {
    echo "$(date '+%Y-%m-%d %H:%M:%S') - $1" | tee -a /var/log/bulletin-board.log
}

log "=== Digital Bulletin Board Startup ==="

# Basic setup
cd "$PROJECT_DIR" || { log "ERROR: Cannot find project directory"; exit 1; }
export DISPLAY=:0
export XAUTHORITY=/home/nljk/.Xauthority

log "Waiting for system to stabilize..."
sleep 10

log "Starting bulletin board with 6-hour timeout..."

# Use timeout command to automatically kill after 6 hours
# timeout sends SIGTERM, then SIGKILL if needed
if timeout 60 python3 run.py; then      # Testing purposees
# if timeout 21600 python3 run.py; then
    log "Bulletin board completed normally"
else
    exit_code=$?
    if [ $exit_code -eq 124 ]; then
        log "6 hours completed - timeout reached"
    else
        log "Bulletin board failed with exit code $exit_code"
    fi
fi

log "Shutting down system"
# sudo shutdown now
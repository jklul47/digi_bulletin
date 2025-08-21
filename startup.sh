#!/bin/bash
PROJECT_DIR="/home/nljk/dev/digi_bulletin"

# Logging function
log() {
    echo "$(date '+%Y-%m-%d %H:%M:%S') - $1" | tee -a /var/log/bulletin-board.log
}

log "=== Digital Bulletin Board Startup ==="

# Ensure script has full PATH
export PATH="/usr/local/sbin:/usr/local/bin:/usr/sbin:/usr/bin:/sbin:/bin"

# Basic setup
cd "$PROJECT_DIR" || { log "ERROR: Cannot find project directory $PROJECT_DIR"; exit 1; }

# Wait for X11 to be fully ready
log "Waiting for X11 display to be ready..."
timeout=30
while [ $timeout -gt 0 ]; do
    if xset q >/dev/null 2>&1; then
        log "X11 display is ready"
        break
    fi
    sleep 1
    timeout=$((timeout - 1))
done

if [ $timeout -eq 0 ]; then
    log "ERROR: X11 display not available after 30 seconds"
    exit 1
fi

# Additional wait for system stability
log "Waiting for system to stabilize..."
sleep 10

log "Starting bulletin board with 6-hour timeout..."

# Use timeout command to automatically kill after 6 hours
# timeout sends SIGTERM, then SIGKILL if needed
if timeout 60 python3 run.py; then      # Testing purposes
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
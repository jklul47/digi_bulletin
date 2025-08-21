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

# Wait for X11 to be fully ready (non-blocking check)
log "Checking X11 display availability..."
if xset q >/dev/null 2>&1; then
    log "X11 display is ready"
else
    log "WARNING: xset command failed, but continuing anyway (X11 might still work)"
    log "This can happen due to permission issues with xset command"
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
# sudo shutdown now
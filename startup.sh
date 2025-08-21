#!/bin/bash
# Give time for system to stabilize
sleep 15

PROJECT_DIR="/home/nljk/dev/digi_bulletin"
LOG_FILE="/var/log/bulletin-board.log"

# Ensure log file exists and has proper permissions
sudo touch "$LOG_FILE"
sudo chown nljk:nljk "$LOG_FILE"
sudo chmod 644 "$LOG_FILE"

# Logging function with immediate flush
log() {
    local message="$(date '+%Y-%m-%d %H:%M:%S') - $1"
    echo "$message" | tee -a "$LOG_FILE"
    # Force flush to ensure immediate write
    sync
}

log "=== Digital Bulletin Board Startup ==="

# Ensure script has full PATH
export PATH="/usr/local/sbin:/usr/local/bin:/usr/sbin:/usr/bin:/sbin:/bin"
export DISPLAY=:0
export XAUTHORITY=/home/nljk/.Xauthority

# Wait a moment to ensure log file is ready
sleep 1

# Open a log terminal with better options
log "Opening log terminal window..."
lxterminal \
    --geometry=100x30+10+10 \
    --title="Bulletin Board Logs - Live Feed" \
    --command="bash -c 'echo \"=== Bulletin Board Log Feed ===\"; echo \"Waiting for logs...\"; tail -f \"$LOG_FILE\"'" &

# Give the terminal time to open and start tail
sleep 3

# Basic setup
cd "$PROJECT_DIR" || { 
    log "ERROR: Cannot find project directory $PROJECT_DIR"
    exit 1
}

# Log system info for debugging
log "Current working directory: $(pwd)"
log "Current user: $(whoami)"
log "Display: $DISPLAY"

# Additional wait for system stability
log "Waiting for system to stabilize... "
sleep 15

log "Starting bulletin board with 6-hour timeout..."

# Use timeout command to automatically kill after 6 hours
# Redirect stderr to ensure all output goes to our log
if timeout 21600 python3 run.py 2>&1 | while IFS= read -r line; do log "APP: $line"; done; then
    log "Bulletin board completed normally"
    exit_code=0
else
    exit_code=$?
    if [ $exit_code -eq 124 ]; then
        log "6 hours completed - timeout reached (this is normal)"
    else
        log "Bulletin board failed with exit code $exit_code"
        log "Waiting 3 minutes before shutdown..."
        sleep 180
    fi
fi

log "Shutting down system in 1 minute"
sleep 60
log "Initiating system shutdown..."
sudo shutdown now
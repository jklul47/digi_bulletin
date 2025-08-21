#!/bin/bash
# Digital Bulletin Board Startup Script

# Set script directory and project path
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" &> /dev/null && pwd)"
PROJECT_DIR="/home/nljk/dev/digi_bulletin"

# Logging function
log() {
    echo "$(date '+%Y-%m-%d %H:%M:%S') - $1" | tee -a /var/log/bulletin-board.log
}

# Error handling
set -e
trap 'log "ERROR: Script failed at line $LINENO"' ERR

log "=== Digital Bulletin Board Startup ==="

# Verify project directory exists
if [ ! -d "$PROJECT_DIR" ]; then
    log "ERROR: Project directory not found: $PROJECT_DIR"
    exit 1
fi

# Change to project directory
cd "$PROJECT_DIR"
log "Changed to project directory: $(pwd)"

# Verify run.py exists
if [ ! -f "run.py" ]; then
    log "ERROR: run.py not found in project directory"
    exit 1
fi

# Wait for display to be available (important for GUI apps)
log "Waiting for display to be available..."
while [ -z "$DISPLAY" ] && [ ! -f /tmp/.X11-unix/X0 ]; do
    sleep 2
    DISPLAY=:0
    export DISPLAY
done
log "Display available: $DISPLAY"

# Set up environment for GUI applications
export DISPLAY=:0
export XAUTHORITY=/home/jklul/.Xauthority

# Optional: Wait a bit longer for system to stabilize
log "Waiting 10 seconds for system to stabilize..."
sleep 10

# Start the bulletin board application
log "Starting Digital Bulletin Board application..."
if python3 run.py; then
    log "Digital Bulletin Board application completed successfully"
else
    log "ERROR: Digital Bulletin Board application failed with exit code $?"
    exit 1
fi

# Auto-shutdown after 6 hours (21600 seconds)
log "Scheduling shutdown in 6 hours..."
sleep 21600
log "Initiating shutdown after 6 hours of operation"
sudo shutdown now

log "=== Digital Bulletin Board Startup Complete ==="
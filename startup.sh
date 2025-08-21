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

# Start the bulletin board application in background and run for 6 hours
log "Starting Digital Bulletin Board application..."

# Start the application in background
DISPLAY=:0 python3 run.py &
APP_PID=$!

log "Digital Bulletin Board started with PID: $APP_PID"
log "Application will run for 6 hours (21600 seconds) then shutdown"

# Function to cleanup and shutdown
cleanup_and_shutdown() {
    log "6 hours completed - stopping application and shutting down"
    
    # Gracefully terminate the application
    if kill -0 $APP_PID 2>/dev/null; then
        log "Sending TERM signal to application (PID: $APP_PID)"
        kill -TERM $APP_PID
        
        # Wait up to 10 seconds for graceful shutdown
        for i in {1..10}; do
            if ! kill -0 $APP_PID 2>/dev/null; then
                log "Application terminated gracefully"
                break
            fi
            sleep 1
        done
        
        # Force kill if still running
        if kill -0 $APP_PID 2>/dev/null; then
            log "Force killing application (PID: $APP_PID)"
            kill -KILL $APP_PID
        fi
    else
        log "Application already stopped"
    fi
    
    log "Initiating system shutdown"
    sudo shutdown now
}

# Set up signal handlers for cleanup
trap cleanup_and_shutdown SIGTERM SIGINT

# Wait for 6 hours (21600 seconds) or until application exits
# timeout_duration=21600
timeout_duration=60     # For testing
elapsed=0
check_interval=30

while [ $elapsed -lt $timeout_duration ]; do
    # Check if application is still running
    if ! kill -0 $APP_PID 2>/dev/null; then
        log "ERROR: Digital Bulletin Board application stopped unexpectedly after $elapsed seconds"
        exit 1
    fi
    
    # Sleep for check interval
    sleep $check_interval
    elapsed=$((elapsed + check_interval))
    
    # Log progress every hour
    if [ $((elapsed % 3600)) -eq 0 ]; then
        hours_elapsed=$((elapsed / 3600))
        hours_remaining=$(((timeout_duration - elapsed) / 3600))
        log "Progress: $hours_elapsed hours elapsed, $hours_remaining hours remaining"
    fi
done

# Time's up - cleanup and shutdown
cleanup_and_shutdown

log "=== Digital Bulletin Board Startup Complete ==="
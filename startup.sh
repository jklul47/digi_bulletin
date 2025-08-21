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

og "Starting bulletin board with terminal display..."

# Open terminal with the application
if command -v lxterminal >/dev/null 2>&1; then
    lxterminal --title="Digital Bulletin Board" --geometry=80x30 -e bash -c "
        echo 'Digital Bulletin Board Starting...'
        echo 'Press Ctrl+C to stop, ESC in app to quit'
        echo '========================================'
        cd '$PROJECT_DIR'
        timeout 60 python3 run.py 2>&1 | tee -a bulletin.log
        echo 'Session ended. Press Enter to continue shutdown...'
        read
    "
    # Wait for terminal to close
    wait
    log "Terminal session completed"
else
    # Fallback to original method if no terminal available
    log "No terminal available, running in background..."
    if timeout 60 python3 run.py; then
        log "Bulletin board completed normally"
        exit 0
    else
        exit_code=$?
        if [ $exit_code -eq 124 ]; then
            log "60 seconds completed - timeout reached (this is normal for testing)"
        else
            log "Bulletin board failed with exit code $exit_code"
            sleep 180
        fi
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
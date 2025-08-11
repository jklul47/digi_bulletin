#!/bin/bash

# Digital Bulletin Board Runner Script
# Installs dependencies and runs the bulletin board application

set -e  # Exit on any error

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Function to print colored output
print_status() {
    echo -e "${BLUE}[INFO]${NC} $1"
}

print_success() {
    echo -e "${GREEN}[SUCCESS]${NC} $1"
}

print_warning() {
    echo -e "${YELLOW}[WARNING]${NC} $1"
}

print_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

# Function to check if command exists
command_exists() {
    command -v "$1" >/dev/null 2>&1
}

# Function to install system dependencies for Raspberry Pi
install_system_deps() {
    print_status "Checking system dependencies..."
    
    # Update package list
    sudo apt update
    
    # Install required system packages
    PACKAGES="python3 python3-pip python3-venv"
    
    # Additional packages needed for pygame and PIL on Raspberry Pi
    PACKAGES="$PACKAGES libsdl2-dev libsdl2-image-dev libsdl2-mixer-dev libsdl2-ttf-dev"
    PACKAGES="$PACKAGES libjpeg-dev zlib1g-dev libfreetype6-dev liblcms2-dev"
    PACKAGES="$PACKAGES libwebp-dev tcl8.6-dev tk8.6-dev python3-tk"
    
    print_status "Installing system packages: $PACKAGES"
    sudo apt install -y $PACKAGES
    
    print_success "System dependencies installed"
}

# Function to create and activate virtual environment
setup_venv() {
    print_status "Setting up Python virtual environment..."
    
    if [ ! -d "venv" ]; then
        python3 -m venv venv
        print_success "Virtual environment created"
    else
        print_status "Virtual environment already exists"
    fi
    
    # Activate virtual environment
    source venv/bin/activate
    print_success "Virtual environment activated"
}

# Function to install Python dependencies
install_python_deps() {
    print_status "Installing Python dependencies..."
    
    # Upgrade pip first
    pip install --upgrade pip
    
    # Install requirements
    if [ -f "requirements.txt" ]; then
        pip install -r requirements.txt
        print_success "Python dependencies installed from requirements.txt"
    else
        print_error "requirements.txt not found!"
        exit 1
    fi
}

# Function to check configuration
check_config() {
    print_status "Checking configuration..."
    
    if [ ! -f "config.json" ]; then
        print_error "config.json not found!"
        print_error "Please create config.json with your Google Drive settings"
        exit 1
    fi
    
    # Check if service account file exists (if Google Drive is enabled)
    if grep -q '"enabled": true' config.json; then
        SERVICE_ACCOUNT_FILE=$(python3 -c "import json; print(json.load(open('config.json'))['google_drive']['service_account_file'])" 2>/dev/null || echo "")
        if [ ! -f "$SERVICE_ACCOUNT_FILE" ]; then
            print_warning "Google Drive service account file not found: $SERVICE_ACCOUNT_FILE"
            print_warning "Google Drive sync will be disabled"
        else
            print_success "Configuration looks good"
        fi
    else
        print_status "Google Drive sync is disabled in config"
    fi
}

# Function to run image fetcher
run_image_fetcher() {
    print_status "Running image fetcher to sync images..."
    
    # Check if Google Drive is enabled and configured
    if python3 -c "import json; config=json.load(open('config.json')); exit(0 if config['google_drive']['enabled'] and config['google_drive']['service_account_file'] else 1)" 2>/dev/null; then
        if python3 image_fetcher.py; then
            print_success "Image sync completed successfully"
        else
            print_warning "Image sync failed, but continuing with existing images"
        fi
    else
        print_status "Google Drive sync not configured, skipping image fetch"
    fi
}

# Function to run bulletin board
run_bulletin() {
    print_status "Starting Digital Bulletin Board..."
    print_status "Press ESC or Q to quit, SPACE for next image, R to rescan"
    print_status "Use LEFT/RIGHT arrows to navigate manually"
    
    python3 bulletin.py
}

# Function to cleanup on exit
cleanup() {
    print_status "Cleaning up..."
    if [ -f "venv/bin/activate" ]; then
        deactivate 2>/dev/null || true
    fi
}

# Set trap to cleanup on exit
trap cleanup EXIT

# Main execution
main() {
    print_status "Starting Digital Bulletin Board Setup and Execution"
    print_status "=================================================="
    
    # Check if running as root (not recommended for this script)
    if [ "$EUID" -eq 0 ]; then
        print_warning "Running as root. This script should normally be run as a regular user."
        read -p "Continue anyway? (y/N): " -n 1 -r
        echo
        if [[ ! $REPLY =~ ^[Yy]$ ]]; then
            exit 1
        fi
    fi
    
    # Check basic requirements
    if ! command_exists python3; then
        print_error "Python3 not found. Installing system dependencies..."
        install_system_deps
    fi
    
    # Install system dependencies if needed
    if ! dpkg -l | grep -q libsdl2-dev; then
        print_status "Installing system dependencies for Raspberry Pi..."
        install_system_deps
    fi
    
    # Setup virtual environment
    setup_venv
    
    # Install Python dependencies
    install_python_deps
    
    # Check configuration
    check_config
    
    # Run image fetcher first
    run_image_fetcher
    
    # Run the bulletin board
    run_bulletin
    
    print_success "Digital Bulletin Board session completed"
}

# Run main function
main "$@"
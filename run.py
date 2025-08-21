#!/usr/bin/env python3
"""
Digital Bulletin Board Runner Script
Handles setup, dependency installation, and execution of the bulletin board system

arguments:
--setup: Install system and Python dependencies (required for first run)
--update-system: Updates system packages (Linux/Raspberry Pi only)
--force-deps: Force reinstall Python dependencies
--version: Show version information
--help: Show help message

# First run (install dependencies)
python3 run.py --setup

# Regular runs (default - just run the application)
python3 run.py

# Update system packages and force reinstall dependencies
python3 run.py --setup --update-system --force-deps
"""

import argparse
import json
import subprocess
import sys
import venv
from pathlib import Path
import platform
import shutil


class Colors:
    """ANSI color codes for terminal output"""
    RED = '\033[0;31m'
    GREEN = '\033[0;32m'
    YELLOW = '\033[1;33m'
    BLUE = '\033[0;34m'
    NC = '\033[0m'  # No Color


class BulletinRunner:
    def __init__(self):
        self.project_dir = Path(__file__).parent
        self.venv_dir = self.project_dir / ".venv"
        self.config_file = self.project_dir / "config.json"
        self.requirements_file = self.project_dir / "requirements.txt"
        
    def print_status(self, message):
        """Print status message in blue"""
        print(f"{Colors.BLUE}[INFO]{Colors.NC} {message}")
        
    def print_success(self, message):
        """Print success message in green"""
        print(f"{Colors.GREEN}[SUCCESS]{Colors.NC} {message}")
        
    def print_warning(self, message):
        """Print warning message in yellow"""
        print(f"{Colors.YELLOW}[WARNING]{Colors.NC} {message}")
        
    def print_error(self, message):
        """Print error message in red"""
        print(f"{Colors.RED}[ERROR]{Colors.NC} {message}")
    
    def command_exists(self, command):
        """Check if a command exists in the system PATH"""
        return shutil.which(command) is not None
    
    def run_command(self, command, check=True, shell=False):
        """Run a system command with error handling"""
        try:
            if isinstance(command, str) and not shell:
                command = command.split()
            
            result = subprocess.run(
                command, 
                check=check, 
                capture_output=True, 
                text=True,
                shell=shell
            )
            return result
        except subprocess.CalledProcessError as e:
            self.print_error(f"Command failed: {' '.join(command) if isinstance(command, list) else command}")
            self.print_error(f"Error: {e.stderr}")
            raise
    
    def is_raspberry_pi(self):
        """Check if running on Raspberry Pi"""
        try:
            with open('/proc/cpuinfo', 'r') as f:
                cpuinfo = f.read()
            return 'BCM' in cpuinfo or 'Raspberry Pi' in cpuinfo
        except FileNotFoundError:
            return False
    
    def is_first_run(self):
        """Check if this is the first time running the script"""
        return not self.venv_dir.exists()
    
    def check_dependencies_installed(self):
        """Check if Python dependencies are installed in venv"""
        if not self.venv_dir.exists():
            return False
        
        # Get the python executable path in the venv
        if platform.system() == "Windows":
            venv_python = self.venv_dir / "Scripts" / "python.exe"
        else:
            venv_python = self.venv_dir / "bin" / "python"
        
        if not venv_python.exists():
            return False
        
        try:
            # Try to import key dependencies
            result = self.run_command([
                str(venv_python), "-c", 
                "import pygame, PIL, googleapiclient"
            ], check=False)
            return result.returncode == 0
        except:
            return False
    
    def update_system(self):
        """Update system packages"""
        if not self.is_raspberry_pi() and platform.system() != 'Linux':
            self.print_warning("System update only supported on Linux/Raspberry Pi")
            return
            
        self.print_status("Updating system packages...")
        try:
            self.run_command("sudo apt update")
            self.run_command("sudo apt upgrade -y")
            self.print_success("System packages updated")
        except subprocess.CalledProcessError:
            self.print_error("Failed to update system packages")
            raise
    
    def install_system_dependencies(self):
        """Install required system packages for Raspberry Pi/Linux"""
        if not self.is_raspberry_pi() and platform.system() != 'Linux':
            self.print_status("Skipping system dependencies (not on Linux)")
            return
            
        self.print_status("Installing system dependencies...")
        
        # Base packages
        packages = [
            "python3", "python3-pip", "python3-venv", "python3-dev"
        ]
        
        # SDL2 packages for pygame
        packages.extend([
            "libsdl2-dev", "libsdl2-image-dev", 
            "libsdl2-mixer-dev", "libsdl2-ttf-dev"
        ])
        
        # Image processing packages for PIL
        packages.extend([
            "libjpeg-dev", "zlib1g-dev", "libfreetype6-dev", 
            "liblcms2-dev", "libwebp-dev", "tcl8.6-dev", 
            "tk8.6-dev", "python3-tk"
        ])
        
        try:
            # Update package list first
            self.run_command("sudo apt update")
            
            # Install packages
            install_cmd = ["sudo", "apt", "install", "-y"] + packages
            self.run_command(install_cmd)
            
            self.print_success("System dependencies installed")
        except subprocess.CalledProcessError:
            self.print_error("Failed to install system dependencies")
            raise
    
    def setup_virtual_environment(self):
        """Create and setup Python virtual environment"""
        self.print_status("Setting up Python virtual environment...")
        
        if not self.venv_dir.exists():
            self.print_status("Creating virtual environment...")
            venv.create(self.venv_dir, with_pip=True)
            self.print_success("Virtual environment created")
        else:
            self.print_status("Virtual environment already exists")
        
        # Get the python executable path in the venv
        if platform.system() == "Windows":
            self.venv_python = self.venv_dir / "Scripts" / "python.exe"
            self.venv_pip = self.venv_dir / "Scripts" / "pip.exe"
        else:
            self.venv_python = self.venv_dir / "bin" / "python"
            self.venv_pip = self.venv_dir / "bin" / "pip"
            
        self.print_success("Virtual environment ready")
    
    def install_python_dependencies(self, force_reinstall=False):
        """Install Python packages from requirements.txt"""
        self.print_status("Installing Python dependencies...")
        
        if not self.requirements_file.exists():
            self.print_error("requirements.txt not found!")
            raise FileNotFoundError("requirements.txt is required")
        
        try:
            # Upgrade pip first
            self.run_command([str(self.venv_pip), "install", "--upgrade", "pip"])
            
            # Install requirements
            install_cmd = [str(self.venv_pip), "install", "-r", str(self.requirements_file)]
            if force_reinstall:
                install_cmd.append("--force-reinstall")
                
            self.run_command(install_cmd)
            self.print_success("Python dependencies installed")
            
        except subprocess.CalledProcessError:
            self.print_error("Failed to install Python dependencies")
            raise
    
    def check_configuration(self):
        """Validate configuration file"""
        self.print_status("Checking configuration...")
        
        if not self.config_file.exists():
            self.print_error("config.json not found!")
            self.print_error("Please create config.json with your Google Drive settings")
            raise FileNotFoundError("config.json is required")
        
        try:
            with open(self.config_file, 'r') as f:
                config = json.load(f)
            
            # Check Google Drive configuration if enabled
            if config.get('google_drive', {}).get('enabled', False):
                service_account_file = config['google_drive'].get('service_account_file', '')
                service_account_path = Path(service_account_file)
                
                if not service_account_path.exists():
                    self.print_warning(f"Google Drive service account file not found: {service_account_file}")
                    self.print_warning("Google Drive sync will be disabled")
                else:
                    self.print_success("Google Drive configuration looks good")
            else:
                self.print_status("Google Drive sync is disabled in config")
                
            self.print_success("Configuration validated")
            
        except json.JSONDecodeError as e:
            self.print_error(f"Invalid JSON in config.json: {e}")
            raise
        except Exception as e:
            self.print_error(f"Error reading config.json: {e}")
            raise
    
    def run_image_fetcher(self):
        """Run the image fetcher to sync images from Google Drive"""
        self.print_status("Running image fetcher to sync images...")
        
        image_fetcher_script = self.project_dir / "image_fetcher.py"
        if not image_fetcher_script.exists():
            self.print_error("image_fetcher.py not found!")
            raise FileNotFoundError("image_fetcher.py is required")
        
        try:
            # Check if Google Drive is configured
            with open(self.config_file, 'r') as f:
                config = json.load(f)
            
            if config.get('google_drive', {}).get('enabled', False):
                result = self.run_command([
                    str(self.venv_python), 
                    str(image_fetcher_script)
                ], check=False)
                
                if result.returncode == 0:
                    self.print_success("Image sync completed successfully")
                else:
                    self.print_warning("Image sync failed, but continuing with existing images")
            else:
                self.print_status("Google Drive sync not configured, skipping image fetch")
                
        except Exception as e:
            self.print_warning(f"Image fetcher failed: {e}")
            self.print_warning("Continuing with existing images")
    
    def run_bulletin_board(self):
        """Run the main bulletin board application"""
        self.print_status("Starting Digital Bulletin Board...")
        self.print_status("Press ESC or Q to quit, SPACE for next image, R to rescan")
        self.print_status("Use LEFT/RIGHT arrows to navigate manually")
        
        bulletin_script = self.project_dir / "bulletin.py"
        if not bulletin_script.exists():
            self.print_error("bulletin.py not found!")
            raise FileNotFoundError("bulletin.py is required")
        
        try:
            # Run bulletin board (this will block until the application exits)
            self.run_command([str(self.venv_python), str(bulletin_script)])
            self.print_success("Digital Bulletin Board session completed")
            
        except subprocess.CalledProcessError as e:
            if e.returncode != 0:
                self.print_error("Bulletin board application failed")
                raise
        except KeyboardInterrupt:
            self.print_status("Bulletin board interrupted by user")
    
    def run(self, setup=False, update_system=False, force_deps=False):
        """Main execution function"""
        self.print_status("Starting Digital Bulletin Board")
        self.print_status("=" * 50)
        
        try:
            # Check if this is first run and setup not requested
            first_run = self.is_first_run()
            deps_installed = self.check_dependencies_installed()
            
            if first_run and not setup:
                self.print_error("First run detected! Dependencies need to be installed.")
                self.print_error("Please run: python3 run.py --setup")
                sys.exit(1)
            
            if not deps_installed and not setup:
                self.print_error("Python dependencies not found in virtual environment!")
                self.print_error("Please run: python3 run.py --setup")
                sys.exit(1)
            
            # Setup dependencies if requested
            if setup:
                self.print_status("Setup mode - installing dependencies")
                
                # Update system if requested
                if update_system:
                    self.update_system()
                
                # Install system dependencies
                self.install_system_dependencies()
                
                # Install Python dependencies
                self.install_python_dependencies(force_reinstall=force_deps)
            
            # Always setup virtual environment (lightweight operation)
            self.setup_virtual_environment()
            
            # Check configuration
            self.check_configuration()
            
            # Run image fetcher
            self.run_image_fetcher()
            
            # Run bulletin board
            self.run_bulletin_board()
            
        except KeyboardInterrupt:
            self.print_status("Operation interrupted by user")
            sys.exit(1)
        except Exception as e:
            self.print_error(f"Failed to run bulletin board: {e}")
            sys.exit(1)


def main():
    """Main entry point with argument parsing"""
    parser = argparse.ArgumentParser(
        description="Digital Bulletin Board Runner - Setup and execute the bulletin board system"
    )
    
    parser.add_argument(
        "--setup", 
        action="store_true",
        help="Install system and Python dependencies (required for first run)"
    )
    
    parser.add_argument(
        "--update-system", 
        action="store_true",
        help="Update system packages before running (Linux/Raspberry Pi only, requires --setup)"
    )
    
    parser.add_argument(
        "--force-deps",
        action="store_true", 
        help="Force reinstall Python dependencies (requires --setup)"
    )
    
    parser.add_argument(
        "--version",
        action="version",
        version="Digital Bulletin Board Runner 1.0"
    )
    
    args = parser.parse_args()
    
    # Validate argument combinations
    if (args.update_system or args.force_deps) and not args.setup:
        print("Error: --update-system and --force-deps require --setup flag")
        sys.exit(1)
    
    # Check Python version
    if sys.version_info < (3, 7):
        print("Error: Python 3.7 or higher is required")
        sys.exit(1)
    
    # Create and run the bulletin runner
    runner = BulletinRunner()
    runner.run(
        setup=args.setup,
        update_system=args.update_system,
        force_deps=args.force_deps
    )


if __name__ == "__main__":
    main()
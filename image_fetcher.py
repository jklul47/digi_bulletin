#!/usr/bin/env python3
"""
Google Drive synchronization for Digital Bulletin Board
Downloads images from a specified Google Drive folder
"""

import os
import io
import time
import logging
from pathlib import Path
from googleapiclient.discovery import build
from googleapiclient.http import MediaIoBaseDownload
from google.oauth2 import service_account

class GoogleDriveSync:
    def __init__(self, config):
        """Initialize Google Drive sync with configuration"""
        self.config = config['google_drive']
        self.image_directory = Path(config['image_directory'])
        self.supported_formats = [fmt.lower() for fmt in config['supported_formats']]
        self.logger = logging.getLogger(__name__)
        
        # Create images directory if it doesn't exist
        self.image_directory.mkdir(parents=True, exist_ok=True)
        
        # Initialize Google Drive service
        self.service = self._authenticate()
        self.last_sync = 0
    
    def _authenticate(self):
        """Authenticate with Google Drive API using service account"""
        try:
            credentials = service_account.Credentials.from_service_account_file(
                self.config['service_account_file'],
                scopes=['https://www.googleapis.com/auth/drive.readonly']
            )
            service = build('drive', 'v3', credentials=credentials)
            self.logger.info("Google Drive authentication successful")
            return service
        except Exception as e:
            self.logger.error(f"Failed to authenticate with Google Drive: {e}")
            return None
    
    def is_supported_image(self, filename):
        """Check if file is a supported image format"""
        return any(filename.lower().endswith(fmt) for fmt in self.supported_formats)
    
    def list_folder_files(self):
        """List all files in the specified Google Drive folder"""
        if not self.service:
            return []
        
        try:
            query = f"'{self.config['folder_id']}' in parents and trashed=false"
            results = self.service.files().list(
                q=query,
                fields="files(id, name, modifiedTime)"
            ).execute()
            
            files = results.get('files', [])
            # Filter for supported image formats
            image_files = [f for f in files if self.is_supported_image(f['name'])]
            
            self.logger.info(f"Found {len(image_files)} images in Google Drive folder")
            return image_files
            
        except Exception as e:
            self.logger.error(f"Error listing Google Drive files: {e}")
            return []
    
    def download_file(self, file_info):
        """Download a single file from Google Drive"""
        try:
            file_id = file_info['id']
            filename = file_info['name']
            local_path = self.image_directory / filename
            
            # Skip if file already exists and is newer
            if local_path.exists():
                local_mtime = local_path.stat().st_mtime
                drive_mtime = time.mktime(
                    time.strptime(file_info['modifiedTime'], '%Y-%m-%dT%H:%M:%S.%fZ')
                )
                if local_mtime >= drive_mtime:
                    return True
            
            # Download file
            request = self.service.files().get_media(fileId=file_id)
            file_io = io.BytesIO()
            downloader = MediaIoBaseDownload(file_io, request)
            
            done = False
            while done is False:
                status, done = downloader.next_chunk()
            
            # Save to local file
            with open(local_path, 'wb') as f:
                f.write(file_io.getvalue())
            
            self.logger.info(f"Downloaded: {filename}")
            return True
            
        except Exception as e:
            self.logger.error(f"Error downloading {file_info['name']}: {e}")
            return False
    
    def cleanup_local_files(self, drive_files):
        """Remove local files that no longer exist in Google Drive"""
        drive_filenames = {f['name'] for f in drive_files}
        
        for local_file in self.image_directory.iterdir():
            if (local_file.is_file() and 
                self.is_supported_image(local_file.name) and 
                local_file.name not in drive_filenames):
                
                try:
                    local_file.unlink()
                    self.logger.info(f"Removed local file: {local_file.name}")
                except Exception as e:
                    self.logger.error(f"Error removing {local_file.name}: {e}")
    
    def sync(self, force=False):
        """Synchronize images from Google Drive"""
        if not self.service:
            self.logger.error("Google Drive service not available")
            return False
        
        current_time = time.time()
        
        # Check if sync is needed
        if not force and (current_time - self.last_sync) < self.config['sync_interval']:
            return True
        
        self.logger.info("Starting Google Drive sync...")
        
        # Get list of files from Google Drive
        drive_files = self.list_folder_files()
        if not drive_files:
            self.logger.warning("No images found in Google Drive folder")
            return False
        
        # Download new/updated files
        success_count = 0
        for file_info in drive_files:
            if self.download_file(file_info):
                success_count += 1
        
        # Clean up local files that no longer exist in Drive
        self.cleanup_local_files(drive_files)
        
        self.last_sync = current_time
        self.logger.info(f"Sync completed: {success_count}/{len(drive_files)} files")
        
        return success_count > 0
    
    def should_sync(self):
        """Check if it's time to sync based on interval"""
        if not self.service:
            return False
        
        current_time = time.time()
        return (current_time - self.last_sync) >= self.config['sync_interval']
    
    def run(self):
        """Run a complete sync operation with status reporting"""
        if not self.service:
            self.logger.error("Google Drive service not available. Check authentication.")
            return False
        
        self.logger.info("="*50)
        self.logger.info("Starting Google Drive Image Sync")
        self.logger.info("="*50)
        
        try:
            # Get folder info
            folder_info = self.service.files().get(fileId=self.config['folder_id']).execute()
            self.logger.info(f"Syncing from folder: {folder_info['name']}")
            
            # Perform sync
            success = self.sync(force=True)
            
            if success:
                self.logger.info("="*50)
                self.logger.info("Sync completed successfully!")
                
                # Report final status
                local_files = list(self.image_directory.glob('*'))
                image_files = [f for f in local_files if self.is_supported_image(f.name)]
                self.logger.info(f"Local images directory: {self.image_directory}")
                self.logger.info(f"Total images downloaded: {len(image_files)}")
                
                if image_files:
                    self.logger.info("Downloaded files:")
                    for img_file in sorted(image_files):
                        size_mb = img_file.stat().st_size / (1024 * 1024)
                        self.logger.info(f"  - {img_file.name} ({size_mb:.2f} MB)")
                
                self.logger.info("="*50)
                return True
            else:
                self.logger.error("Sync failed!")
                return False
                
        except Exception as e:
            self.logger.error(f"Error during sync operation: {e}")
            return False


def load_config(config_file):
    """Load configuration from JSON file"""
    import json
    
    default_config = {
        "image_directory": "./images",
        "google_drive": {
            "enabled": True,
            "folder_id": "",
            "service_account_file": "",
            "sync_interval": 300
        },
        "supported_formats": [".jpg", ".jpeg", ".png", ".gif", ".bmp"]
    }
    
    try:
        with open(config_file, 'r') as f:
            user_config = json.load(f)
            config = {**default_config, **user_config}
            return config
    except FileNotFoundError:
        print(f"Config file not found: {config_file}")
        print("Please create a config.json file with your Google Drive settings.")
        return None
    except json.JSONDecodeError as e:
        print(f"Error reading config file: {e}")
        return None


def main():
    """Main entry point for standalone Google Drive sync"""
    import sys
    import argparse
    
    # Set up argument parser
    parser = argparse.ArgumentParser(description='Google Drive Image Sync for Digital Bulletin Board')
    parser.add_argument('--config', '-c', 
                       default='config.json',
                       help='Path to config file (default: config.json)')
    parser.add_argument('--folder-id', '-f',
                       help='Google Drive folder ID (overrides config)')
    parser.add_argument('--service-account', '-s',
                       help='Path to service account key file (overrides config)')
    parser.add_argument('--output-dir', '-o',
                       help='Output directory for images (overrides config)')
    parser.add_argument('--verbose', '-v', 
                       action='store_true',
                       help='Enable verbose logging')
    
    args = parser.parse_args()
    
    # Set up logging
    log_level = logging.DEBUG if args.verbose else logging.INFO
    logging.basicConfig(
        level=log_level,
        format='%(asctime)s - %(levelname)s - %(message)s',
        handlers=[logging.StreamHandler()]
    )
    
    logger = logging.getLogger(__name__)
    
    # Load configuration
    config = load_config(args.config)
    if not config:
        sys.exit(1)
    
    # Override config with command line arguments
    if args.folder_id:
        config['google_drive']['folder_id'] = args.folder_id
    if args.service_account:
        config['google_drive']['service_account_file'] = args.service_account
    if args.output_dir:
        config['image_directory'] = args.output_dir
    
    # Validate required settings
    if not config['google_drive']['folder_id']:
        logger.error("Google Drive folder ID not specified. Use --folder-id or set in config.json")
        sys.exit(1)
    
    if not config['google_drive']['service_account_file']:
        logger.error("Service account file not specified. Use --service-account or set in config.json")
        sys.exit(1)
    
    if not os.path.exists(config['google_drive']['service_account_file']):
        logger.error(f"Service account file not found: {config['google_drive']['service_account_file']}")
        sys.exit(1)
    
    try:
        # Create and run sync
        sync = GoogleDriveSync(config)
        success = sync.run()
        
        if success:
            logger.info("Image sync completed successfully!")
            sys.exit(0)
        else:
            logger.error("Image sync failed!")
            sys.exit(1)
            
    except KeyboardInterrupt:
        logger.info("Sync interrupted by user")
        sys.exit(1)
    except Exception as e:
        logger.error(f"Unexpected error: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
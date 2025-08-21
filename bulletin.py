#!/usr/bin/env python3
"""
Digital Bulletin Board for Raspberry Pi
Cycles through images in a directory and displays them fullscreen
"""

import pygame
import os
import sys
import time
import json
import random
from image_fetcher import GoogleDriveSync
from pathlib import Path
from PIL import Image, ImageOps
import logging

class DigitalBulletinBoard:
    def __init__(self, config_file=os.path.join(os.path.dirname(__file__), 'config.json')):
        """Initialize the bulletin board with configuration"""
        self.load_config(config_file)
        self.setup_logging()
        self.setup_pygame()
        self.image_list = []
        self.current_image_index = 0
        self.last_update_time = time.time()
        self.clock = pygame.time.Clock()
        
    def load_config(self, config_file):
        """Load configuration from JSON file"""
        default_config = {
            "image_directory": os.path.join(os.path.dirname(__file__), 'images'),
            "display_duration": 10,  # seconds
            "supported_formats": [".jpg", ".jpeg", ".png", ".gif", ".bmp"],
            "shuffle_images": False,
            "transition_enabled": True,
            "background_color": [0, 0, 0],  # RGB black
            "log_level": "INFO",
            "fullscreen": True,
            "screen_width": 1920,
            "screen_height": 1080
        }
        
        # Open and load config file, or create it if it doesn't exist
        try:
            with open(config_file, 'r') as f:
                user_config = json.load(f)
                self.config = {**default_config, **user_config}
        except FileNotFoundError:
            self.config = default_config
            self.save_config(config_file)
            print(f"Created default config file: {config_file}")
        except json.JSONDecodeError as e:
            print(f"Error reading config file: {e}")
            self.config = default_config
    
    def save_config(self, config_file):
        """Save current configuration to JSON file"""
        with open(config_file, 'w') as f:
            json.dump(self.config, f, indent=4)
    
    def setup_logging(self):
        """Setup logging configuration"""
        log_level = getattr(logging, self.config['log_level'].upper())
        logging.basicConfig(
            level=log_level,
            format='%(asctime)s - %(levelname)s - %(message)s',
            handlers=[
                logging.FileHandler('bulletin.log'),
                logging.StreamHandler()
            ]
        )
        self.logger = logging.getLogger(__name__)
    
    def setup_pygame(self):
        """Initialize pygame and create display surface"""
        pygame.init()
        pygame.mouse.set_visible(False)  # Hide mouse cursor
        
        if self.config['fullscreen']:
            # Get actual screen resolution
            info = pygame.display.Info()
            self.screen_width = info.current_w
            self.screen_height = info.current_h
            self.screen = pygame.display.set_mode((self.screen_width, self.screen_height), pygame.FULLSCREEN)
        else:
            self.screen_width = self.config['screen_width']
            self.screen_height = self.config['screen_height']
            self.screen = pygame.display.set_mode((self.screen_width, self.screen_height))
        
        pygame.display.set_caption("Digital Bulletin Board")
        self.logger.info(f"Display initialized: {self.screen_width}x{self.screen_height}")
    
    def scan_images(self):
        """Scan the image directory for supported image files"""
        image_dir = Path(self.config['image_directory'])
        
        if not image_dir.exists():
            try:
                image_dir.mkdir(parents=True, exist_ok=True)
                self.logger.info(f"Created image directory: {image_dir}")
            except Exception as e:
                self.logger.error(f"Failed to create image directory {image_dir}: {e}")
                return False
        
        self.image_list = []
        supported_formats = [fmt.lower() for fmt in self.config['supported_formats']]
        
        for file_path in image_dir.iterdir():
            if file_path.is_file() and file_path.suffix.lower() in supported_formats:
                self.image_list.append(str(file_path))
        
        if not self.image_list:
            self.logger.error(f"No supported images found in {image_dir}")
            return False
        
        if self.config['shuffle_images']:
            random.shuffle(self.image_list)
        
        self.logger.info(f"Found {len(self.image_list)} images")
        return True
    
    def load_and_scale_image(self, image_path):
        """Load and scale image to fit screen while maintaining aspect ratio"""
        try:
            # Use PIL to handle various formats and EXIF orientation
            with Image.open(image_path) as pil_image:
                # Auto-orient image based on EXIF data
                pil_image = ImageOps.exif_transpose(pil_image)
                
                # Convert to RGB if necessary
                if pil_image.mode != 'RGB':
                    pil_image = pil_image.convert('RGB')
                
                # Calculate scaling to fit screen while maintaining aspect ratio
                img_width, img_height = pil_image.size
                scale_x = self.screen_width / img_width
                scale_y = self.screen_height / img_height
                scale = min(scale_x, scale_y)
                
                new_width = int(img_width * scale)
                new_height = int(img_height * scale)
                
                # Resize image
                pil_image = pil_image.resize((new_width, new_height), Image.Resampling.LANCZOS)
                
                # Convert PIL image to pygame surface
                image_string = pil_image.tobytes()
                pygame_image = pygame.image.fromstring(image_string, pil_image.size, 'RGB')
                
                return pygame_image
                
        except Exception as e:
            self.logger.error(f"Error loading image {image_path}: {e}")
            return None
    
    def display_image(self, image_surface):
        """Display image centered on screen with smooth transition (no blinking)"""
        if image_surface is None:
            return
        
        # Clear and draw everything in the back buffer before displaying
        self.screen.fill(self.config['background_color'])
        
        # Center the image
        image_rect = image_surface.get_rect()
        screen_rect = self.screen.get_rect()
        image_rect.center = screen_rect.center
        
        # Blit image to screen (still in back buffer)
        self.screen.blit(image_surface, image_rect)
        
        # Only now flip to display everything at once
        pygame.display.flip()
        
        # Log image dimensions for debugging
        self.logger.debug(f"Screen: {self.screen_width}x{self.screen_height}, "
                        f"Image: {image_surface.get_width()}x{image_surface.get_height()}")

    
    def handle_events(self):
        """Handle pygame events"""
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                return False
            elif event.type == pygame.KEYDOWN:
                if event.key == pygame.K_ESCAPE or event.key == pygame.K_q:
                    return False
                elif event.key == pygame.K_SPACE:
                    # Manual advance to next image
                    self.advance_image()
                elif event.key == pygame.K_LEFT:
                    # Go to previous image
                    self.current_image_index = (self.current_image_index - 1) % len(self.image_list)
                    self.display_current_image()
                elif event.key == pygame.K_RIGHT:
                    # Go to next image
                    self.advance_image()
                elif event.key == pygame.K_r:
                    # Rescan images
                    self.logger.info("Rescanning images...")
                    self.scan_images()
        return True
    
    def advance_image(self):
        """Advance to the next image smoothly"""
        if not self.image_list:
            return
        
        self.current_image_index = (self.current_image_index + 1) % len(self.image_list)
        self.display_current_image()
        self.last_update_time = time.time()
    
    def display_current_image(self):
        """Display the current image"""
        if not self.image_list:
            return
        
        current_image_path = self.image_list[self.current_image_index]
        self.logger.info(f"Displaying: {Path(current_image_path).name}")
        
        image_surface = self.load_and_scale_image(current_image_path)
        self.display_image(image_surface)
    
    def run(self):
        """Main application loop"""
        self.logger.info("Starting Digital Bulletin Board")
        
        # Initial image scan
        if not self.scan_images():
            self.logger.error("No images found. Exiting.")
            return
        
        # Display first image
        self.display_current_image()
        
        running = True
        while running:
            # Handle events
            running = self.handle_events()
            
            # Check if it's time to advance to next image
            current_time = time.time()
            if current_time - self.last_update_time >= self.config['display_duration']:
                self.advance_image()
            
            # Limit frame rate to reduce CPU usage
            self.clock.tick(30)
        
        self.logger.info("Shutting down Digital Bulletin Board")
        pygame.quit()


def main():
    """Main entry point"""
    try:
        bulletin_board = DigitalBulletinBoard()
        bulletin_board.run()
    except KeyboardInterrupt:
        print("\nShutting down...")
    except Exception as e:
        print(f"Error: {e}")
        logging.error(f"Unexpected error: {e}", exc_info=True)
    finally:
        pygame.quit()
        sys.exit(0)


if __name__ == "__main__":
    main()
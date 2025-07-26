"""
Main Web Form Automation System
"""

import logging
import sys
import time
from pathlib import Path
from typing import Optional, List
from config import Config
from data_handler import DataHandler
from web_driver_manager import WebDriverManager
from form_filler import FormFiller
import click

class VotingAutomationSystem:
    """Main automation system orchestrating all components"""
    
    def __init__(self, csv_path: str, url: str = None, headless: bool = None, timeout: int = None):
        self.csv_path = csv_path
        self.url = url
        self.headless = headless if headless is not None else Config.HEADLESS_MODE
        self.timeout = timeout or Config.WEBDRIVER_TIMEOUT
        
        # Initialize components
        self.data_handler = DataHandler(csv_path)
        self.webdriver_manager = None
        self.form_filler = None
        
        # Setup logging
        self._setup_logging()
        
        self.logger = logging.getLogger(__name__)
        
    def _setup_logging(self):
        """Setup logging configuration"""
        # Create logs directory if it doesn't exist
        logs_dir = Path("logs")
        logs_dir.mkdir(exist_ok=True)
        
        # Configure logging
        logging.basicConfig(
            level=getattr(logging, Config.LOG_LEVEL),
            format=Config.LOG_FORMAT,
            handlers=[
                logging.FileHandler(logs_dir / Config.LOG_FILE),
                logging.StreamHandler(sys.stdout)
            ]
        )
        
        # Set specific logger levels
        logging.getLogger("selenium").setLevel(logging.WARNING)
        logging.getLogger("urllib3").setLevel(logging.WARNING)
    
    def run_automation(self) -> bool:
        """
        Run the complete automation process
        
        Returns:
            bool: True if successful, False otherwise
        """
        try:
            self.logger.info("Starting web form automation system")
            
            # Step 1: Load and validate CSV data
            if not self._load_data():
                return False
            
            # Step 2: Setup WebDriver
            if not self._setup_webdriver():
                return False
            
            # Step 3: Navigate to URL if provided
            if self.url and not self._navigate_to_url():
                return False
            
            # Step 4: Process data in batches
            if not self._process_data_batches():
                return False
            
            self.logger.info("Automation completed successfully")
            return True
            
        except KeyboardInterrupt:
            self.logger.info("Automation interrupted by user")
            return False
        except Exception as e:
            self.logger.error(f"Automation failed: {e}")
            return False
        finally:
            self._cleanup()
    
    def _load_data(self) -> bool:
        """Load and validate CSV data"""
        self.logger.info("Loading CSV data...")
        
        if not self.data_handler.load_csv_data():
            self.logger.error("Failed to load CSV data")
            return False
        
        # Display data info
        data_info = self.data_handler.get_data_info()
        self.logger.info(f"Data loaded: {data_info}")
        
        # Show preview
        preview = self.data_handler.preview_data(3)
        self.logger.info(f"Data preview (first 3 rows): {preview}")
        
        return True
    
    def _setup_webdriver(self) -> bool:
        """Setup WebDriver and form filler"""
        self.logger.info("Setting up WebDriver...")
        
        self.webdriver_manager = WebDriverManager(
            headless=self.headless,
            timeout=self.timeout
        )
        
        if not self.webdriver_manager.setup_driver():
            self.logger.error("Failed to setup WebDriver")
            return False
        
        self.form_filler = FormFiller(self.webdriver_manager)
        return True
    
    def _navigate_to_url(self) -> bool:
        """Navigate to the target URL"""
        self.logger.info(f"Navigating to URL: {self.url}")
        
        if not self.webdriver_manager.navigate_to_url(self.url):
            self.logger.error("Failed to navigate to URL")
            return False
        
        return True
    
    def _process_data_batches(self) -> bool:
        """Process all data batches"""
        # Split data into batches
        batches = self.data_handler.split_data_into_batches()
        
        if not batches:
            self.logger.error("No data batches to process")
            return False
        
        self.logger.info(f"Processing {len(batches)} batches...")
        
        for batch_index, batch in enumerate(batches):
            self.logger.info(f"Processing batch {batch_index + 1}/{len(batches)} ({len(batch)} sets)")
            
            if not self._process_single_batch(batch, batch_index, len(batches)):
                self.logger.error(f"Failed to process batch {batch_index + 1}")
                return False
            
            self.logger.info(f"Batch {batch_index + 1} completed successfully")
            
            # Pause between batches if not the last one
            if batch_index < len(batches) - 1:
                self.logger.info("Pausing between batches...")
                time.sleep(2)
        
        return True
    
    def _process_single_batch(self, batch_data: List[List[int]], batch_index: int, total_batches: int) -> bool:
        """
        Process a single batch of data
        
        Args:
            batch_data: List of sets for this batch
            batch_index: Current batch index
            total_batches: Total number of batches
            
        Returns:
            bool: True if successful, False otherwise
        """
        try:
            # Step 1: Fill the voting form
            self.logger.info(f"Filling form with {len(batch_data)} sets...")
            if not self.form_filler.fill_voting_form(batch_data):
                self.logger.error("Failed to fill voting form")
                return False
            
            # Step 2: Submit the form
            self.logger.info("Submitting form...")
            if not self.form_filler.submit_form():
                self.logger.error("Failed to submit form")
                return False
            
            # Step 3: Handle any alerts
            self.logger.info("Checking for alerts...")
            self.webdriver_manager.handle_alert(accept=True)
            
            # Step 4: Confirm submission if needed
            self.logger.info("Checking for confirmation...")
            self.form_filler.confirm_submission()
            
            # Step 5: Navigate to next form (if not the last batch)
            if batch_index < total_batches - 1:
                self.logger.info("Navigating to next form...")
                if not self.form_filler.navigate_to_next_form():
                    self.logger.error("Failed to navigate to next form")
                    return False
            
            return True
            
        except Exception as e:
            self.logger.error(f"Error processing batch: {e}")
            return False
    
    def _cleanup(self):
        """Cleanup resources"""
        self.logger.info("Cleaning up resources...")
        
        if self.webdriver_manager:
            self.webdriver_manager.quit_driver()
    
    def get_status(self) -> dict:
        """Get current automation status"""
        status = {
            "csv_path": self.csv_path,
            "url": self.url,
            "headless": self.headless,
            "timeout": self.timeout
        }
        
        if self.data_handler:
            status.update(self.data_handler.get_data_info())
        
        if self.form_filler:
            status.update(self.form_filler.get_form_status())
        
        return status
    
    def take_screenshot(self, filename: str = None) -> str:
        """Take a screenshot for debugging"""
        if self.webdriver_manager:
            return self.webdriver_manager.screenshot(filename)
        return ""

# CLI Interface
@click.command()
@click.option('--csv', required=True, help='Path to CSV file with voting data')
@click.option('--url', help='Target URL to navigate to')
@click.option('--headless', is_flag=True, help='Run browser in headless mode')
@click.option('--timeout', default=10, help='WebDriver timeout in seconds')
@click.option('--browser', default='chrome', help='Browser to use (chrome, firefox, edge)')
@click.option('--log-level', default='INFO', help='Logging level (DEBUG, INFO, WARNING, ERROR)')
def main(csv, url, headless, timeout, browser, log_level):
    """Web Form Automation System - Automate form filling with CSV data"""
    
    # Update config with CLI options
    Config.HEADLESS_MODE = headless
    Config.WEBDRIVER_TIMEOUT = timeout
    Config.BROWSER = browser
    Config.LOG_LEVEL = log_level
    
    # Validate CSV file exists
    csv_path = Path(csv)
    if not csv_path.exists():
        click.echo(f"Error: CSV file not found: {csv}")
        sys.exit(1)
    
    # Create and run automation system
    automation = VotingAutomationSystem(
        csv_path=str(csv_path),
        url=url,
        headless=headless,
        timeout=timeout
    )
    
    success = automation.run_automation()
    
    if success:
        click.echo("✅ Automation completed successfully!")
        sys.exit(0)
    else:
        click.echo("❌ Automation failed!")
        sys.exit(1)

if __name__ == "__main__":
    main()
"""
Enhanced Web Form Automation System with Action Recording and Playback
"""

import logging
import sys
import time
from pathlib import Path
from typing import Optional, List, Dict, Any
from enum import Enum

from config import Config
from data_handler import DataHandler
from web_driver_manager import WebDriverManager
from form_filler import FormFiller
from action_recorder import ActionRecorder
from action_player import ActionPlayer
from action_manager import ActionSequence, ActionFileManager, load_or_create_sample_actions
from toto_round_selector import TotoRoundSelector
import click

logger = logging.getLogger(__name__)

class AutomationMode(Enum):
    """Automation operation modes"""
    RECORD = "record"
    EXECUTE = "execute"
    BASIC = "basic"  # Original functionality without actions

class EnhancedAutomationSystem:
    """Enhanced automation system with action recording and playback"""
    
    def __init__(self, mode: AutomationMode, csv_path: str = None, 
                 action_file: str = None, url: str = None, 
                 headless: bool = None, timeout: int = None):
        self.mode = mode
        self.csv_path = csv_path
        self.action_file = action_file
        self.url = url
        self.headless = headless if headless is not None else Config.HEADLESS_MODE
        self.timeout = timeout or Config.WEBDRIVER_TIMEOUT
        
        # Initialize components
        self.data_handler = None
        self.webdriver_manager = None
        self.form_filler = None
        self.action_recorder = None
        self.action_player = None
        self.action_file_manager = ActionFileManager()
        self.round_selector = None
        
        # Batch data (can be set externally)
        self.batch_data = None
        
        # Processing state
        self.current_batch = 0
        self.total_batches = 0
        self.form_input_ready = False  # Flag to control form input start
        self.voting_page_reached = False
        
        # Progress callback function (optional)
        self.progress_callback = None
        
        # Error recovery settings
        self.max_retries = 3
        self.retry_delay = 5  # seconds
        self.error_recovery_enabled = True
        
        self.processing_stats = {
            "total_sets": 0,
            "processed_sets": 0,
            "successful_batches": 0,
            "failed_batches": 0,
            "retry_attempts": 0,
            "recovered_errors": 0,
            "start_time": 0,
            "end_time": 0
        }
        
        # Setup logging
        self._setup_logging()
        self.logger = logging.getLogger(__name__)
        
    def _setup_logging(self):
        """Setup logging configuration"""
        logs_dir = Path("logs")
        logs_dir.mkdir(exist_ok=True)
        
        logging.basicConfig(
            level=getattr(logging, Config.LOG_LEVEL),
            format=Config.LOG_FORMAT,
            handlers=[
                logging.FileHandler(logs_dir / f"enhanced_automation_{int(time.time())}.log"),
                logging.StreamHandler(sys.stdout)
            ]
        )
        
        # Set specific logger levels
        logging.getLogger("selenium").setLevel(logging.WARNING)
        logging.getLogger("urllib3").setLevel(logging.WARNING)
    
    def set_batch_data(self, batch_data: List[List[int]]):
        """
        Set specific batch data to process instead of loading from CSV
        
        Args:
            batch_data: List of sets (each set is a list of 13 values)
        """
        self.batch_data = batch_data
        self.logger.info(f"Batch data set: {len(batch_data)} sets")
    
    def set_progress_callback(self, callback):
        """
        Set progress callback function for real-time progress updates
        
        Args:
            callback: Function that accepts (current_batch, total_batches, current_set, total_sets, stage)
        """
        self.progress_callback = callback
    
    def _attempt_error_recovery(self):
        """Attempt to recover from errors by taking diagnostic actions"""
        try:
            self.logger.info("🚑 Attempting error recovery...")
            
            # Take screenshot for debugging
            if self.webdriver_manager and self.webdriver_manager.driver:
                try:
                    screenshot_path = f"logs/error_recovery_{int(time.time())}.png"
                    self.webdriver_manager.driver.save_screenshot(screenshot_path)
                    self.logger.info(f"📸 Error recovery screenshot saved: {screenshot_path}")
                except Exception as e:
                    self.logger.warning(f"Failed to take recovery screenshot: {e}")
                
                # Check if we're still on a valid page
                try:
                    current_url = self.webdriver_manager.driver.current_url
                    page_title = self.webdriver_manager.driver.title
                    self.logger.info(f"🔍 Current page: {current_url}")
                    self.logger.info(f"🔍 Page title: {page_title}")
                    
                    # Handle any alerts that might be blocking
                    alert_handled = self.webdriver_manager.handle_alert(accept=True)
                    if alert_handled:
                        self.logger.info("✅ Alert handled during recovery")
                    
                    # Check for modal dialogs and handle them
                    if self.round_selector:
                        self.round_selector._handle_modal_dialogs()
                        self.logger.info("✅ Modal dialogs handled during recovery")
                    
                    # If we're not on the voting page, try to navigate back
                    if 'PGSPSL00001MoveSingleVoteSheet' not in current_url:
                        self.logger.info("🔄 Not on voting page, attempting recovery navigation...")
                        if self.round_selector and self.current_batch > 1:
                            # Try to navigate back to voting page
                            if self.round_selector.click_round_link_on_addition_page():
                                self.logger.info("✅ Recovery navigation: clicked round link")
                                if self.round_selector.click_single_button():
                                    self.logger.info("✅ Recovery navigation: clicked single button")
                                    return True
                
                except Exception as e:
                    self.logger.warning(f"Recovery check failed: {e}")
            
            self.logger.info("🚑 Error recovery completed")
            return True
            
        except Exception as e:
            self.logger.error(f"❌ Error recovery failed: {e}")
            return False
    
    def start_form_input(self):
        """Signal that form input can begin"""
        self.form_input_ready = True
        self.logger.info("Form input authorized - processing will continue")
    
    def is_voting_page_ready(self) -> bool:
        """Check if voting page is reached and ready for input"""
        return self.voting_page_reached
    
    def is_form_input_ready(self) -> bool:
        """Check if form input is authorized to start"""
        return self.form_input_ready
    
    def run_automation(self) -> bool:
        """
        Run automation based on selected mode
        
        Returns:
            bool: True if successful, False otherwise
        """
        try:
            self.logger.info(f"Starting enhanced automation system in {self.mode.value} mode")
            
            # Setup WebDriver
            if not self._setup_webdriver():
                return False
            
            if self.mode == AutomationMode.RECORD:
                return self._run_record_mode()
            elif self.mode == AutomationMode.EXECUTE:
                return self._run_execute_mode()
            elif self.mode == AutomationMode.BASIC:
                return self._run_basic_mode()
            else:
                self.logger.error(f"Unknown automation mode: {self.mode}")
                return False
                
        except KeyboardInterrupt:
            self.logger.info("Automation interrupted by user")
            return False
        except Exception as e:
            self.logger.error(f"Automation failed: {e}")
            return False
        finally:
            self._cleanup()
    
    def _run_record_mode(self) -> bool:
        """Run automation in record mode"""
        self.logger.info("Starting record mode")
        
        # Navigate to URL if provided
        if self.url and not self._navigate_to_url():
            return False
        
        # Initialize action recorder
        self.action_recorder = ActionRecorder(self.webdriver_manager)
        
        # Start recording session
        if not self.action_recorder.start_recording_session(self.url):
            self.logger.error("Failed to start recording session")
            return False
        
        # Interactive recording
        recorded_sequence = self.action_recorder.record_interactive_session()
        
        # Save recorded actions
        if not recorded_sequence.batch_actions:
            self.logger.warning("No actions recorded")
            return False
        
        # Generate filename if not provided
        action_filename = self.action_file or f"recorded_actions_{int(time.time())}.json"
        
        success = self.action_recorder.save_recorded_actions(action_filename)
        if success:
            self.logger.info(f"Actions recorded and saved to: {action_filename}")
            self.logger.info(f"Total actions recorded: {len(recorded_sequence.batch_actions)}")
            
            # Preview recorded actions
            self.action_recorder.preview_recorded_actions()
        
        return success
    
    def _run_execute_mode(self) -> bool:
        """Run automation in execute mode"""
        self.logger.info("Starting execute mode")
        
        # Validate required parameters
        if not self.csv_path:
            self.logger.error("CSV file path is required for execute mode")
            return False
        
        if not self.action_file:
            self.logger.error("Action file is required for execute mode")
            return False
        
        # Load data (from batch or CSV)
        if not self._load_data():
            return False
        
        # Load action sequence
        action_sequence = self._load_action_sequence()
        if not action_sequence:
            return False
        
        # Navigate to URL if provided
        if self.url and not self._navigate_to_url():
            return False
        
        # Initialize action player
        self.action_player = ActionPlayer(self.webdriver_manager)
        
        # Execute batch processing with actions
        return self._process_data_with_actions(action_sequence)
    
    def _run_basic_mode(self) -> bool:
        """Run automation in basic mode (original functionality)"""
        self.logger.info("Starting basic mode")
        
        if not self.csv_path and not self.batch_data:
            self.logger.error("CSV file path or batch data is required for basic mode")
            return False
        
        # Load data (from batch or CSV)
        if not self._load_data():
            return False
        
        # Navigate to URL if provided
        if self.url and not self._navigate_to_url():
            return False
        
        # Wait for user to navigate to correct voting page
        if not self._wait_for_voting_page():
            return False
        
        # Process data using original method
        return self._process_data_batches()
    
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
        
        # Initialize round selector
        self.round_selector = TotoRoundSelector(self.webdriver_manager.driver)
        self.logger.info("Round selector initialized")
        
        return True
    
    def _load_data(self) -> bool:
        """Load and validate data (from batch or CSV)"""
        if self.batch_data:
            self.logger.info(f"Using pre-loaded batch data: {len(self.batch_data)} sets")
            # Create a temporary data handler for validation
            if self.csv_path:
                self.data_handler = DataHandler(self.csv_path)
            self.processing_stats["total_sets"] = len(self.batch_data)
            return True
        
        if not self.csv_path:
            self.logger.error("No CSV path or batch data available")
            return False
        
        self.logger.info("Loading CSV data...")
        self.data_handler = DataHandler(self.csv_path)
        if not self.data_handler.load_csv_data():
            self.logger.error("Failed to load CSV data")
            return False
        
        # Display data info
        data_info = self.data_handler.get_data_info()
        self.logger.info(f"Data loaded: {data_info}")
        
        # Update processing stats
        self.processing_stats["total_sets"] = data_info["total_sets"]
        
        return True
    
    def _load_action_sequence(self) -> Optional[ActionSequence]:
        """Load action sequence from file"""
        self.logger.info(f"Loading action sequence from: {self.action_file}")
        
        action_sequence = self.action_file_manager.load_actions(self.action_file)
        if not action_sequence:
            self.logger.error("Failed to load action sequence")
            return None
        
        self.logger.info(f"Action sequence loaded: {len(action_sequence.batch_actions)} actions")
        
        # Display action info
        metadata = action_sequence.metadata
        self.logger.info(f"Action sequence info:")
        self.logger.info(f"  Name: {metadata.get('name', 'Unknown')}")
        self.logger.info(f"  Description: {metadata.get('description', 'No description')}")
        self.logger.info(f"  Site URL: {metadata.get('site_url', 'Unknown')}")
        
        return action_sequence
    
    def _navigate_to_url(self) -> bool:
        """Navigate to the target URL"""
        self.logger.info(f"Navigating to URL: {self.url}")
        
        if not self.webdriver_manager.navigate_to_url(self.url):
            self.logger.error("Failed to navigate to URL")
            return False
        
        return True
    
    def _process_data_with_actions(self, action_sequence: ActionSequence) -> bool:
        """Process CSV data with recorded actions"""
        self.logger.info("Starting enhanced batch processing with recorded actions")
        
        # Get data batches
        if self.batch_data:
            # Use pre-loaded batch data (single batch)
            batches = [self.batch_data]
            self.logger.info(f"Using pre-loaded batch data as single batch")
        else:
            # Split data into batches
            batches = self.data_handler.split_data_into_batches()
        
        if not batches:
            self.logger.error("No data batches to process")
            return False
        
        self.total_batches = len(batches)
        self.processing_stats["start_time"] = time.time()
        
        self.logger.info(f"Processing {len(batches)} batches with recorded actions...")
        
        for batch_index, batch in enumerate(batches):
            self.current_batch = batch_index + 1
            self.logger.info(f"Processing batch {self.current_batch}/{self.total_batches} ({len(batch)} sets)")
            
            # Fill form with batch data
            if not self._fill_form_batch(batch):
                self.logger.error(f"Failed to fill form for batch {self.current_batch}")
                self.processing_stats["failed_batches"] += 1
                return False
            
            # Execute recorded actions
            if not self._execute_batch_actions(action_sequence):
                self.logger.error(f"Failed to execute actions for batch {self.current_batch}")
                self.processing_stats["failed_batches"] += 1
                return False
            
            self.processing_stats["successful_batches"] += 1
            self.processing_stats["processed_sets"] += len(batch)
            
            self.logger.info(f"Batch {self.current_batch} completed successfully")
            
            # Pause between batches if not the last one
            if batch_index < len(batches) - 1:
                self.logger.info("Pausing between batches...")
                time.sleep(2)
        
        self.processing_stats["end_time"] = time.time()
        self._log_processing_summary()
        
        return True
    
    def _process_data_batches(self) -> bool:
        """Process data batches using original method (basic mode)"""
        # Determine data source priority: data_handler with data > batch_data > empty data_handler
        if self.data_handler and hasattr(self.data_handler, 'split_data_into_batches'):
            # Check if data handler actually has data
            data_info = self.data_handler.get_data_info()
            total_sets = data_info.get('total_sets', 0)
            
            if total_sets > 0:
                # Data handler has data - use it for multi-batch processing
                self.logger.info(f"🔍 DEBUG: Using data handler with {total_sets} sets, estimated {data_info.get('estimated_batches', 'unknown')} batches")
                batches = self.data_handler.split_data_into_batches()
                self.logger.info(f"✅ Data handler split into {len(batches)} batches with sizes: {[len(b) for b in batches]}")
                
                if self.batch_data:
                    self.logger.info(f"📝 Note: batch_data also set with {len(self.batch_data)} sets, but using data handler for multi-batch processing")
            else:
                # Data handler has no data - fall back to batch_data
                if self.batch_data:
                    batches = [self.batch_data]
                    self.logger.info(f"🔄 Data handler empty, using pre-loaded batch_data as single batch ({len(self.batch_data)} sets)")
                else:
                    self.logger.error("❌ Both data handler and batch_data are empty")
                    return False
        elif self.batch_data:
            # No data handler - use batch_data
            batches = [self.batch_data]
            self.logger.info(f"📦 Using pre-loaded batch_data as single batch ({len(self.batch_data)} sets)")
        else:
            self.logger.error("❌ No data source available - neither data handler nor batch data")
            return False
        
        if not batches:
            self.logger.error("No data batches to process")
            return False
        
        self.total_batches = len(batches)
        self.processing_stats["start_time"] = time.time()
        
        self.logger.info(f"Processing {len(batches)} batches in basic mode...")
        
        for batch_index, batch in enumerate(batches):
            self.current_batch = batch_index + 1
            self.logger.info(f"Processing batch {self.current_batch}/{self.total_batches} ({len(batch)} sets)")
            
            # Call progress callback if available
            if self.progress_callback:
                self.progress_callback(self.current_batch, self.total_batches, 0, len(batch), 'processing')
            
            # Attempt batch processing with retry mechanism
            batch_success = False
            retry_count = 0
            
            while not batch_success and retry_count <= self.max_retries:
                try:
                    if retry_count > 0:
                        self.logger.info(f"🔄 Retry attempt {retry_count}/{self.max_retries} for batch {self.current_batch}")
                        self.processing_stats["retry_attempts"] += 1
                        
                        # Update progress callback for retry
                        if self.progress_callback:
                            self.progress_callback(self.current_batch, self.total_batches, 0, len(batch), 'waiting')
                        
                        # Wait before retry
                        time.sleep(self.retry_delay)
                        
                        # Try to recover by taking screenshot and refreshing if needed
                        if self.error_recovery_enabled:
                            self._attempt_error_recovery()
                    
                    if self._process_single_batch_basic(batch):
                        batch_success = True
                        self.processing_stats["successful_batches"] += 1
                        self.processing_stats["processed_sets"] += len(batch)
                        self.logger.info(f"✅ Batch {self.current_batch} completed successfully")
                        
                        if retry_count > 0:
                            self.processing_stats["recovered_errors"] += 1
                            self.logger.info(f"🚑 Error recovery successful after {retry_count} retries")
                        
                        # Update progress callback for completion
                        if self.progress_callback:
                            self.progress_callback(self.current_batch, self.total_batches, len(batch), len(batch), 'completed')
                    else:
                        retry_count += 1
                        if retry_count <= self.max_retries:
                            self.logger.warning(f"⚠️ Batch {self.current_batch} failed, attempting retry {retry_count}/{self.max_retries}")
                        
                except Exception as e:
                    retry_count += 1
                    self.logger.error(f"❌ Batch {self.current_batch} failed with exception: {e}")
                    if retry_count <= self.max_retries:
                        self.logger.warning(f"⚠️ Attempting retry {retry_count}/{self.max_retries}")
            
            # Handle final failure
            if not batch_success:
                self.logger.error(f"❌ Batch {self.current_batch} failed after {self.max_retries} retries")
                self.processing_stats["failed_batches"] += 1
                
                # Update progress callback for final failure
                if self.progress_callback:
                    self.progress_callback(self.current_batch, self.total_batches, 0, len(batch), 'error')
            
            # Pause between batches
            if batch_index < len(batches) - 1:
                time.sleep(2)
        
        self.processing_stats["end_time"] = time.time()
        self._log_processing_summary()
        
        # Return success if at least one batch was processed successfully
        success = self.processing_stats["successful_batches"] > 0
        if success:
            self.logger.info(f"🎉 Batch processing completed: {self.processing_stats['successful_batches']}/{self.total_batches} successful")
        else:
            self.logger.error("❌ No batches were processed successfully")
        
        return success
    
    def _fill_form_batch(self, batch_data: List[List[int]]) -> bool:
        """Fill form with batch data"""
        self.logger.info(f"Filling form with {len(batch_data)} sets...")
        
        if not self.form_filler.fill_voting_form(batch_data):
            self.logger.error("Failed to fill voting form")
            return False
        
        return True
    
    def _execute_batch_actions(self, action_sequence: ActionSequence) -> bool:
        """Execute recorded actions after filling batch"""
        self.logger.info("Executing recorded actions for current batch...")
        
        if not self.action_player.execute_action_sequence(action_sequence):
            self.logger.error("Failed to execute action sequence")
            return False
        
        # Log execution stats
        stats = self.action_player.get_execution_stats()
        self.logger.info(f"Action execution stats: {stats}")
        
        return True
    
    def _process_single_batch_basic(self, batch_data: List[List[int]]) -> bool:
        """Process single batch using basic method with enhanced loop handling"""
        try:
            # For batches after the first, we need to navigate from addition page
            if self.current_batch > 1:
                self.logger.info("🔄 Navigating from voting addition page to single voting page...")
                
                # Update progress for navigation
                if self.progress_callback:
                    self.progress_callback(self.current_batch, self.total_batches, 0, len(batch_data), 'navigation')
                
                # Step 1: Click the round link on addition page
                if not self.round_selector.click_round_link_on_addition_page():
                    self.logger.error("❌ Failed to click round link on addition page")
                    return False
                self.logger.info("✅ Clicked round link on addition page")
                
                # Step 2: Click single button to go to voting page
                if not self.round_selector.click_single_button():
                    self.logger.error("❌ Failed to click single button")
                    return False
                self.logger.info("✅ Clicked single button - ready for voting")
            
            # Update progress for form input
            if self.progress_callback:
                self.progress_callback(self.current_batch, self.total_batches, 0, len(batch_data), 'input')
            
            # Fill the voting form
            if not self.form_filler.fill_voting_form(batch_data):
                return False
            
            # Update progress for cart addition
            if self.progress_callback:
                self.progress_callback(self.current_batch, self.total_batches, len(batch_data), len(batch_data), 'cart')
            
            # Submit the form
            if not self.form_filler.submit_form():
                return False
            
            # Handle any alerts
            self.webdriver_manager.handle_alert(accept=True)
            
            # For the last batch, no need to navigate back
            if self.current_batch == self.total_batches:
                self.logger.info("🏁 Last batch completed - no navigation needed")
            else:
                self.logger.info("🔄 Preparing for next batch (will handle navigation in next iteration)...")
            
            return True
            
        except Exception as e:
            self.logger.error(f"Error processing batch: {e}")
            return False
    
    def _log_processing_summary(self):
        """Log processing summary statistics"""
        stats = self.processing_stats
        duration = stats["end_time"] - stats["start_time"]
        
        self.logger.info("=== Processing Summary ===")
        self.logger.info(f"Total sets: {stats['total_sets']}")
        self.logger.info(f"Processed sets: {stats['processed_sets']}")
        self.logger.info(f"Successful batches: {stats['successful_batches']}")
        self.logger.info(f"Failed batches: {stats['failed_batches']}")
        self.logger.info(f"Total duration: {duration:.2f} seconds")
        
        if stats["processed_sets"] > 0:
            rate = stats["processed_sets"] / duration if duration > 0 else 0
            self.logger.info(f"Processing rate: {rate:.2f} sets/second")
        
        # Display completion message
        if stats["successful_batches"] > 0:
            self.logger.info("=" * 50)
            self.logger.info("🎉 ALL BATCH PROCESSING COMPLETED SUCCESSFULLY! 🎉")
            self.logger.info("=" * 50)
            self.logger.info(f"✅ Total batches processed: {stats['successful_batches']}")
            self.logger.info(f"✅ Total sets processed: {stats['processed_sets']}")
            if stats["failed_batches"] > 0:
                self.logger.warning(f"⚠️  Failed batches: {stats['failed_batches']}")
            self.logger.info("All items have been added to your cart!")
            self.logger.info("You can now proceed to checkout when ready.")
            self.logger.info("=" * 50)
        else:
            self.logger.warning("⚠️ No batches were processed successfully.")
    
    def _cleanup(self):
        """Cleanup resources"""
        self.logger.info("Cleaning up resources...")
        
        if self.webdriver_manager:
            self.webdriver_manager.quit_driver()
    
    def _wait_for_voting_page(self) -> bool:
        """Wait for user to navigate to the correct voting page"""
        self.logger.info("Waiting for navigation to voting page...")
        self.logger.info("Please manually navigate to the voting page:")
        self.logger.info("1. Login if needed")
        self.logger.info("2. Go through multi-input page")
        self.logger.info("3. Click to voting page (PGSPSL00001MoveSingleVoteSheet.form)")
        self.logger.info("4. Wait - automatic detection will start form filling")
        
        max_attempts = 60  # 60 seconds
        for attempt in range(max_attempts):
            try:
                current_url = self.webdriver_manager.driver.current_url
                
                # Check if we're on the voting page
                if "PGSPSL00001MoveSingleVoteSheet.form" in current_url:
                    self.logger.info(f"✅ Detected voting page: {current_url}")
                    self.logger.info("Waiting for page to fully load...")
                    time.sleep(5)  # Longer wait for full page load
                    
                    # Scroll down to ensure all 13 games are loaded
                    try:
                        self.webdriver_manager.driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
                        time.sleep(2)
                        self.webdriver_manager.driver.execute_script("window.scrollTo(0, 0);")
                        time.sleep(1)
                        self.logger.info("Page scrolled to ensure all elements are loaded")
                    except:
                        pass
                    
                    # Mark voting page as reached
                    self.voting_page_reached = True
                    self.logger.info("✅ Voting page ready - waiting for user to start form input via GUI...")
                    
                    # Wait for user to authorize form input via GUI
                    return self._wait_for_form_input_authorization()
                
                # Show current page info
                if attempt % 10 == 0:  # Every 10 seconds
                    self.logger.info(f"Current URL: {current_url}")
                    self.logger.info("⏳ Waiting for voting page...")
                
                time.sleep(1)
                
            except Exception as e:
                self.logger.error(f"Error checking page: {e}")
                
        self.logger.error("❌ Timeout waiting for voting page")
        return False
    
    def _wait_for_form_input_authorization(self) -> bool:
        """Wait for user to authorize form input via GUI"""
        self.logger.info("Waiting for user to click 'Start Form Input' button in GUI...")
        
        max_wait = 300  # 5 minutes max wait
        for _ in range(max_wait):
            if self.form_input_ready:
                self.logger.info("✅ Form input authorized - starting form filling...")
                return True
            time.sleep(1)
        
        self.logger.error("❌ Timeout waiting for form input authorization")
        return False
    
    def get_status(self) -> Dict[str, Any]:
        """Get current automation status"""
        status = {
            "mode": self.mode.value,
            "csv_path": self.csv_path,
            "action_file": self.action_file,
            "url": self.url,
            "current_batch": self.current_batch,
            "total_batches": self.total_batches,
            "processing_stats": self.processing_stats
        }
        
        if self.data_handler:
            status.update(self.data_handler.get_data_info())
        
        return status
    
    def take_screenshot(self, filename: str = None) -> str:
        """Take a screenshot for debugging"""
        if self.webdriver_manager:
            return self.webdriver_manager.screenshot(filename)
        return ""

# CLI Interface
@click.command()
@click.option('--mode', type=click.Choice(['record', 'execute', 'basic']), 
              required=True, help='Automation mode')
@click.option('--csv', help='Path to CSV file with voting data')
@click.option('--actions', help='Path to action file (JSON)')
@click.option('--url', help='Target URL to navigate to')
@click.option('--headless', is_flag=True, help='Run browser in headless mode')
@click.option('--timeout', default=10, help='WebDriver timeout in seconds')
@click.option('--browser', default='chrome', help='Browser to use (chrome, firefox, edge)')
@click.option('--log-level', default='INFO', help='Logging level (DEBUG, INFO, WARNING, ERROR)')
def main(mode, csv, actions, url, headless, timeout, browser, log_level):
    """Enhanced Web Form Automation System with Action Recording and Playback"""
    
    # Update config with CLI options
    Config.HEADLESS_MODE = headless
    Config.WEBDRIVER_TIMEOUT = timeout
    Config.BROWSER = browser
    Config.LOG_LEVEL = log_level
    
    # Validate mode-specific requirements
    automation_mode = AutomationMode(mode)
    
    if automation_mode in [AutomationMode.EXECUTE, AutomationMode.BASIC] and not csv:
        click.echo("Error: CSV file is required for execute and basic modes")
        sys.exit(1)
    
    if automation_mode == AutomationMode.EXECUTE and not actions:
        click.echo("Error: Action file is required for execute mode")
        sys.exit(1)
    
    # Validate file existence
    if csv and not Path(csv).exists():
        click.echo(f"Error: CSV file not found: {csv}")
        sys.exit(1)
    
    # Only check action file existence for execute mode (record mode creates new files)
    if actions and automation_mode == AutomationMode.EXECUTE and not Path(actions).exists():
        click.echo(f"Error: Action file not found: {actions}")
        sys.exit(1)
    
    # Create and run automation system
    automation = EnhancedAutomationSystem(
        mode=automation_mode,
        csv_path=csv,
        action_file=actions,
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
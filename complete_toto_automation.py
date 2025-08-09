#!/usr/bin/env python3
"""
Complete End-to-End Toto Automation Workflow
Combines: Navigation → Round Selection → Form Filling → Cart Addition
"""

import logging
import time
from typing import List, Dict, Optional
from pathlib import Path

from config import Config
from web_driver_manager import WebDriverManager
from toto_round_selector import TotoRoundSelector
from form_filler import FormFiller
from data_handler import DataHandler

logger = logging.getLogger(__name__)

class CompleteTotoAutomation:
    """Complete end-to-end toto automation workflow"""
    
    def __init__(self, headless: bool = False, timeout: int = 15, keep_browser_open: bool = True,
                 show_end: bool = False, username: Optional[str] = None, password: Optional[str] = None):
        self.headless = headless
        self.timeout = timeout
        self.keep_browser_open = keep_browser_open
        self.show_end = show_end
        self.username = username
        self.password = password
        
        # Components
        self.webdriver_manager = None
        self.round_selector = None
        self.form_filler = None
        self.data_handler = None
        
        # State
        self.current_round_info = None
        self.voting_page_ready = False
        
        # Statistics
        self.stats = {
            "total_batches": 0,
            "successful_batches": 0,
            "failed_batches": 0,
            "total_sets": 0,
            "start_time": 0,
            "end_time": 0
        }
    
    def initialize_system(self) -> bool:
        """Initialize all automation components"""
        try:
            logger.info("🚀 Initializing Complete Toto Automation System...")
            
            # Initialize WebDriver
            logger.info("📱 Setting up WebDriver...")
            self.webdriver_manager = WebDriverManager(
                headless=self.headless,
                timeout=self.timeout
            )
            
            if not self.webdriver_manager.setup_driver():
                logger.error("❌ Failed to setup WebDriver")
                return False
            
            logger.info("✅ WebDriver initialized successfully")
            
            # Initialize round selector
            logger.info("🎯 Initializing round selector...")
            self.round_selector = TotoRoundSelector(self.webdriver_manager.driver)
            logger.info("✅ Round selector initialized")
            
            # Initialize form filler
            logger.info("📝 Initializing form filler...")
            self.form_filler = FormFiller(self.webdriver_manager)
            logger.info("✅ Form filler initialized")
            
            logger.info("🎉 All components initialized successfully!")
            return True
            
        except Exception as e:
            logger.error(f"❌ System initialization failed: {e}")
            return False
    
    def execute_complete_workflow(self, csv_path: str, round_number: Optional[str] = None) -> bool:
        """
        Execute the complete automation workflow
        
        Args:
            csv_path: Path to CSV file with betting data
            round_number: Specific round to select (optional, will auto-select if None)
            
        Returns:
            bool: True if successful, False otherwise
        """
        try:
            logger.info("=" * 60)
            logger.info("🏁 STARTING COMPLETE TOTO AUTOMATION WORKFLOW")
            logger.info("=" * 60)
            
            # Store as int to satisfy strict typing of stats dict
            self.stats["start_time"] = int(time.time())
            
            # Step 1: Initialize system
            logger.info("📍 STEP 1: Initialize System")
            if not self.initialize_system():
                return False
            logger.info("✅ STEP 1 COMPLETED: System initialized")
            
            # Step 2: Load betting data
            logger.info("📍 STEP 2: Load Betting Data")
            if not self._load_betting_data(csv_path):
                return False
            logger.info("✅ STEP 2 COMPLETED: Data loaded")
            
            # Step 3: Navigate and select round
            logger.info("📍 STEP 3: Navigate and Select Round")
            if not self._navigate_and_select_round(round_number):
                return False
            logger.info("✅ STEP 3 COMPLETED: Round selected and voting page reached")
            
            # Step 4: Process all batches
            logger.info("📍 STEP 4: Process All Betting Batches")
            if not self._process_all_batches():
                return False
            logger.info("✅ STEP 4 COMPLETED: All batches processed")
            
            # Final summary
            self._log_final_summary()

            # Optionally open the final page in a visible browser with the same session
            try:
                if self.show_end:
                    self._show_end_in_visible_browser()
            except Exception as _end_err:
                logger.warning(f"Show-end step failed: {_end_err}")
            return True
            
        except Exception as e:
            logger.error(f"❌ Complete workflow failed: {e}")
            return False
        finally:
            self._cleanup()
    
    def _load_betting_data(self, csv_path: str) -> bool:
        """Load and validate betting data from CSV"""
        try:
            logger.info(f"📊 Loading betting data from: {csv_path}")
            
            if not Path(csv_path).exists():
                logger.error(f"❌ CSV file not found: {csv_path}")
                return False
            
            # Initialize data handler
            self.data_handler = DataHandler(csv_path)
            if not self.data_handler.load_csv_data():
                logger.error("❌ Failed to load CSV data")
                return False
            
            # Get data info
            data_info = self.data_handler.get_data_info()
            logger.info(f"📊 Data loaded: {data_info}")
            
            # Debug: Show detailed batch information
            batches = self.data_handler.split_data_into_batches()
            logger.info(f"🔍 DEBUG: Split into {len(batches)} batches:")
            for i, batch in enumerate(batches):
                logger.info(f"  Batch {i+1}: {len(batch)} sets")
            
            self.stats["total_sets"] = data_info["total_sets"]
            
            return True
            
        except Exception as e:
            logger.error(f"❌ Error loading betting data: {e}")
            return False
    
    def _navigate_and_select_round(self, round_number: Optional[str] = None) -> bool:
        """Navigate to toto site and select round"""
        try:
            logger.info("🧭 Starting navigation and round selection...")
            # Proactively close unexpected popups (quick scan) and log elapsed
            if self.webdriver_manager:
                try:
                    t0 = time.time()
                    closed = self.webdriver_manager.close_unexpected_popups()
                    dt = (time.time() - t0)
                    logger.debug(f"Popup quick-scan closed={closed}, elapsed={dt:.2f}s")
                except Exception as _e:
                    logger.debug(f"Popup quick-scan skipped: {_e}")

            # Ensure components are initialized (helps static analyzers and avoids None access)
            assert self.round_selector is not None, "Round selector not initialized"
            assert self.webdriver_manager is not None, "WebDriver manager not initialized"
            assert getattr(self.webdriver_manager, "driver", None) is not None, "WebDriver not initialized"

            # Validate session and auto-restart if needed
            try:
                if hasattr(self.webdriver_manager, "is_session_valid") and not self.webdriver_manager.is_session_valid():
                    logger.warning("WebDriver session invalid. Attempting restart...")
                    if not self.webdriver_manager.restart_driver():
                        logger.error("Failed to restart WebDriver session")
                        return False
                    # Recreate round selector with new driver
                    self.round_selector = TotoRoundSelector(self.webdriver_manager.driver)
                    logger.info("Reinitialized round selector after driver restart")
            except Exception as _serr:
                logger.debug(f"Session validation skipped: {_serr}")
            
            if round_number:
                logger.info(f"🎯 Target round: 第{round_number}回")
                
                # Manual navigation with specific round
                # Step 1: Navigate to start page
                if not self.round_selector.navigate_to_start_page(Config.START_URL):
                    logger.error("❌ Failed to navigate to start page")
                    return False
                # Clear any modals
                try:
                    self.webdriver_manager.close_unexpected_popups()
                except Exception:
                    pass

                # If login page appears, try automatic login when credentials are provided
                self._maybe_login()
                
                # Data: URL fallback after initial navigation
                try:
                    cur_url = getattr(getattr(self.webdriver_manager, 'driver', None), 'current_url', '')
                    logger.debug(f"Current URL after start page nav: {cur_url}")
                    if str(cur_url).startswith("data:"):
                        logger.info("Still at data:, retry navigating to START_URL...")
                        if not self.round_selector.navigate_to_start_page(Config.START_URL):
                            logger.error("Failed to leave data: URL state")
                            return False
                except Exception as _uerr:
                    logger.debug(f"Could not read current URL: {_uerr}")
                
                # Step 2: Detect rounds
                rounds = self.round_selector.detect_toto_rounds()
                if not rounds:
                    logger.error("❌ No rounds detected")
                    return False
                
                # Step 3: Select specific round
                if not self.round_selector.select_round_by_number(rounds, round_number):
                    logger.error(f"❌ Failed to select round {round_number}")
                    return False
                
                # Step 4: Click voting prediction button
                if not self.round_selector.click_voting_prediction_button():
                    logger.error("❌ Failed to click voting prediction button")
                    return False
                try:
                    self.webdriver_manager.close_unexpected_popups()
                except Exception:
                    pass
                self._maybe_login()
                
            else:
                logger.info("🤖 Using automatic navigation (will select latest round)")
                
                # Automatic navigation (selects latest round automatically)
                if not self.round_selector.navigate_to_voting_prediction():
                    logger.error("❌ Automatic navigation failed")
                    return False
                try:
                    self.webdriver_manager.close_unexpected_popups()
                except Exception:
                    pass
                self._maybe_login()
            
            # Verify we reached voting page
            drv = getattr(self.webdriver_manager, "driver", None)
            current_url = getattr(drv, "current_url", "")
            if "vote" in current_url.lower() or "PGSPSL00001MoveSingleVoteSheet" in current_url:
                logger.info("✅ Successfully reached voting prediction page")
                self.voting_page_ready = True
                
                # Store round info
                self.current_round_info = self.round_selector.get_selected_round_info()
                if self.current_round_info:
                    logger.info(f"🎯 Selected round: {self.current_round_info}")
                
                return True
            else:
                logger.error(f"❌ Did not reach voting page. Current URL: {current_url}")
                return False
            
        except Exception as e:
            logger.error(f"❌ Navigation and round selection failed: {e}")
            return False
    
    def _process_all_batches(self) -> bool:
        """Process all betting data batches"""
        try:
            if not self.voting_page_ready:
                logger.error("❌ Voting page not ready")
                return False
            
            # Ensure components are initialized before use
            assert self.data_handler is not None, "Data handler not initialized"
            assert self.form_filler is not None, "Form filler not initialized"
            assert self.round_selector is not None, "Round selector not initialized"
            assert self.webdriver_manager is not None, "WebDriver manager not initialized"

            # Get data batches
            batches = self.data_handler.split_data_into_batches()
            if not batches:
                logger.error("❌ No data batches available")
                return False
            
            self.stats["total_batches"] = len(batches)
            logger.info(f"📦 Processing {len(batches)} batches...")
            
            # Process each batch
            for batch_index, batch_data in enumerate(batches):
                batch_num = batch_index + 1
                logger.info(f"📦 Processing batch {batch_num}/{len(batches)} ({len(batch_data)} sets)")
                
                if self._process_single_batch(batch_data, batch_num, len(batches)):
                    self.stats["successful_batches"] += 1
                    logger.info(f"✅ Batch {batch_num} completed successfully")
                else:
                    self.stats["failed_batches"] += 1
                    logger.error(f"❌ Batch {batch_num} failed")
                    
                    # Ask user if they want to continue
                    logger.warning("⚠️ Batch failed. Continuing with next batch...")
                    # In a real scenario, you might want to stop or ask user
                
                # Pause between batches
                if batch_index < len(batches) - 1:
                    logger.info("⏳ Pausing between batches...")
                    time.sleep(2)
            
            # Check overall success
            if self.stats["successful_batches"] > 0:
                logger.info(f"🎉 Batch processing completed: {self.stats['successful_batches']}/{self.stats['total_batches']} successful")
                return True
            else:
                logger.error("❌ No batches were processed successfully")
                return False
            
        except Exception as e:
            logger.error(f"❌ Error processing batches: {e}")
            return False
    
    def _process_single_batch(self, batch_data: List[List[int]], batch_number: int, total_batches: int) -> bool:
        """Process a single batch of betting data with enhanced loop handling"""
        try:
            logger.info(f"🎯 Processing batch {batch_number}/{total_batches} with {len(batch_data)} sets")

            # If redirected to login at any point, try to log in
            self._maybe_login()
            
            # For batches after the first, ensure we're on the single voting page.
            # Prefer returning via the cart page's "totoの投票を追加する" to guarantee additive behavior.
        if batch_number > 1:
                logger.info("🔄 Ensuring we are on the single voting page for next input...")
                try:
            drv2 = getattr(self.webdriver_manager, "driver", None)
            current_url = getattr(drv2, "current_url", "")
                except Exception:
                    current_url = ""

                if "PGSPSL00001MoveSingleVoteSheet" not in current_url:
                    # Try cart-page guided navigation first (preferred)
                    try:
                        if self.form_filler and hasattr(self.form_filler, "_handle_cart_page_navigation") and self.form_filler._handle_cart_page_navigation():
                            logger.info("✅ Returned to single voting page via cart navigation")
                        else:
                            logger.info("ℹ️ Cart navigation did not succeed; falling back to round link → シングル")
                            # Fallback: existing method (round link then single)
                            if not (self.round_selector and self.round_selector.click_round_link_on_addition_page()):
                                logger.error("❌ Failed to click round link on addition page")
                                return False
                            if not (self.round_selector and self.round_selector.click_single_button()):
                                logger.error("❌ Failed to click single button")
                                return False
                    except Exception as nav_err:
                        logger.warning(f"Cart navigation attempt failed: {nav_err}. Falling back to round link → シングル")
                        if not (self.round_selector and self.round_selector.click_round_link_on_addition_page()):
                            logger.error("❌ Failed to click round link on addition page")
                            return False
                        if not (self.round_selector and self.round_selector.click_single_button()):
                            logger.error("❌ Failed to click single button")
                            return False
                if self.webdriver_manager:
                    try:
                        self.webdriver_manager.close_unexpected_popups()
                    except Exception:
                        pass
            
            # Fill form with batch data
            logger.info("📝 Filling voting form...")
            if not (self.form_filler and self.form_filler.fill_voting_form(batch_data)):
                logger.error("❌ Failed to fill voting form")
                return False
            
            logger.info("✅ Form filled successfully")
            if self.webdriver_manager:
                try:
                    self.webdriver_manager.close_unexpected_popups()
                except Exception:
                    pass
            
            # Submit form (add to cart)
            logger.info("🛒 Submitting form (adding to cart)...")
            if not (self.form_filler and self.form_filler.submit_form()):
                logger.error("❌ Failed to submit form")
                return False
            
            logger.info("✅ Form submitted successfully")
            if self.webdriver_manager:
                try:
                    self.webdriver_manager.close_unexpected_popups()
                except Exception:
                    pass
            
            # Handle any alerts
            if self.webdriver_manager:
                try:
                    logger.info("🔔 Handling any alerts...")
                    self.webdriver_manager.handle_alert(accept=True)
                except Exception as alert_error:
                    logger.debug(f"No alerts to handle: {alert_error}")
            
            # If more batches remain, proactively return via cart page to ensure additive behavior
            if batch_number < total_batches:
                logger.info("🔄 Preparing for next batch: returning via cart page's 'totoの投票を追加する'...")
                try:
                    if not (self.form_filler and hasattr(self.form_filler, "_handle_cart_page_navigation") and self.form_filler._handle_cart_page_navigation()):
                        logger.warning("Could not return via cart navigation now; next loop will attempt recovery")
                except Exception as post_nav_err:
                    logger.debug(f"Post-submit cart navigation error: {post_nav_err}")
            else:
                logger.info("🏁 Last batch completed - staying on current page")
            
            return True
            
        except Exception as e:
            logger.error(f"❌ Error processing batch {batch_number}: {e}")
            return False
    
    def _log_final_summary(self):
        """Log final automation summary"""
        # Store as int to satisfy strict typing of stats dict
        self.stats["end_time"] = int(time.time())
        duration = self.stats["end_time"] - self.stats["start_time"]

        logger.info("=" * 60)
        logger.info("📊 COMPLETE TOTO AUTOMATION SUMMARY")
        logger.info("=" * 60)

        if self.current_round_info:
            logger.info(f"🎯 Selected Round: {self.current_round_info['round_text']}")

        logger.info(f"📦 Total Batches: {self.stats['total_batches']}")
        logger.info(f"✅ Successful Batches: {self.stats['successful_batches']}")
        logger.info(f"❌ Failed Batches: {self.stats['failed_batches']}")
        logger.info(f"📊 Total Sets: {self.stats['total_sets']}")
        logger.info(f"⏱️ Duration: {duration:.2f} seconds")
        
        if self.stats["total_sets"] > 0 and duration > 0:
            rate = self.stats["total_sets"] / duration
            logger.info(f"🚀 Processing Rate: {rate:.2f} sets/second")
        
        if self.stats["successful_batches"] > 0:
            logger.info("=" * 60)
            logger.info("🎉 AUTOMATION COMPLETED SUCCESSFULLY! 🎉")
            logger.info("🛒 All items have been added to your cart!")
            logger.info("💳 You can now proceed to checkout when ready.")
            logger.info("=" * 60)
        else:
            logger.error("❌ AUTOMATION FAILED - No batches were processed successfully")
    
    def _cleanup(self):
        """Cleanup resources"""
        try:
            logger.info("🧹 Cleaning up resources...")
            if self.webdriver_manager:
                if self.keep_browser_open:
                    logger.info("ℹ️ Keeping browser open as requested (no quit)")
                else:
                    self.webdriver_manager.quit_driver()
            logger.info("✅ Cleanup completed")
        except Exception as e:
            logger.error(f"❌ Error during cleanup: {e}")
    
    def get_automation_stats(self) -> Dict:
        """Get current automation statistics"""
        return self.stats.copy()

    def _maybe_login(self) -> None:
        """Attempt automatic login if we're on a login page and credentials are provided."""
        try:
            if not self.username or not self.password:
                return
            if not self.webdriver_manager or not getattr(self.webdriver_manager, "driver", None):
                return
            ok = self.webdriver_manager.try_login_if_present(self.username, self.password)
            if ok is True:
                logger.info("🔐 Auto-login completed")
            elif ok is False:
                logger.warning("🔐 Auto-login attempted but may have failed")
            else:
                logger.debug("No login page detected; skipping auto-login")
        except Exception as e:
            logger.debug(f"Auto-login check failed: {e}")

    def _show_end_in_visible_browser(self) -> None:
        """Open the final page in a new visible browser and transfer session cookies."""
        try:
            if not self.webdriver_manager or not getattr(self.webdriver_manager, "driver", None):
                logger.warning("No active driver to transfer session from")
                return
            driver = self.webdriver_manager.driver
            current_url = driver.current_url
            try:
                cookies = driver.get_cookies()
            except Exception as e:
                logger.warning(f"Could not read cookies from headless session: {e}")
                cookies = []

            # Start a visible browser
            from urllib.parse import urlparse
            visible = WebDriverManager(headless=False, timeout=self.timeout)
            if not visible.setup_driver():
                logger.error("Could not start visible browser for show-end")
                return
            vdrv = visible.driver
            assert vdrv is not None

            # Navigate to base to set cookies
            parsed = urlparse(current_url)
            base = f"{parsed.scheme}://{parsed.netloc}"
            vdrv.get(base)

            # Import cookies (filter incompatible keys)
            imported = 0
            for c in cookies:
                try:
                    cd = {k: v for k, v in c.items() if k in ("name","value","domain","path","secure","expiry","httpOnly")}
                    # Domain must match or be parent; Selenium may adjust automatically
                    vdrv.add_cookie(cd)
                    imported += 1
                except Exception:
                    continue
            logger.info(f"Imported {imported} cookies into visible browser")

            # Go to final url
            vdrv.get(current_url)
            logger.info("✅ Final page opened in visible browser")

            # Optionally try auto-login again if redirected to login and creds available
            if self.username and self.password:
                try:
                    visible.try_login_if_present(self.username, self.password)
                except Exception:
                    pass

            # Keep visible browser open; do not close here
        except Exception as e:
            logger.warning(f"Show-end failed: {e}")

def main():
    """Main function for testing the complete workflow"""
    import sys
    
    # Setup logging
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s - %(levelname)s - %(message)s",
        handlers=[
            logging.StreamHandler(sys.stdout)
        ]
    )
    
    # Example usage
    csv_file = "sample_data.csv"  # Replace with actual CSV file
    round_number = None  # Will auto-select latest round, or specify like "1558"
    
    # Create and run automation
    automation = CompleteTotoAutomation(headless=False)
    success = automation.execute_complete_workflow(csv_file, round_number)
    
    if success:
        print("✅ Complete automation workflow finished successfully!")
        return 0
    else:
        print("❌ Complete automation workflow failed!")
        return 1

if __name__ == "__main__":
    import sys as _sys
    _sys.exit(main())
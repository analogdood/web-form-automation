"""
Form Filler for Web Form Automation System
"""

import logging
from selenium.webdriver.common.by import By
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import (
    TimeoutException, 
    NoSuchElementException,
    ElementNotInteractableException
)
from typing import List, Dict, Optional
from config import Config
from web_driver_manager import WebDriverManager
import time

logger = logging.getLogger(__name__)

class FormFiller:
    """Handles form filling operations with checkbox interactions"""
    
    def __init__(self, webdriver_manager: WebDriverManager):
        self.driver_manager = webdriver_manager
        self.driver = webdriver_manager.driver
        self.wait = webdriver_manager.wait
        
    def fill_voting_form(self, batch_data: List[List[int]]) -> bool:
        """
        Fill voting form with batch data
        
        Args:
            batch_data: List of sets, each set is a list of 13 values
            
        Returns:
            bool: True if successful, False otherwise
        """
        try:
            logger.info(f"Filling form with {len(batch_data)} sets")
            
            # Process by games (rows) first, then sets (columns)
            num_games = Config.MAX_GAMES_PER_SET
            num_sets = len(batch_data)
            
            logger.info(f"Configuration: MAX_GAMES_PER_SET = {num_games}, batch contains {num_sets} sets")
            logger.info(f"Will process games 0 to {num_games-1} (total: {num_games} games)")
            
            for game_index in range(num_games):
                logger.info(f"Processing game {game_index + 1}/{num_games}")
                
                for set_index in range(num_sets):
                    if set_index >= Config.MAX_SETS_PER_BATCH:
                        logger.warning(f"Reached maximum sets per batch ({Config.MAX_SETS_PER_BATCH})")
                        break
                    
                    # CSV: rows=sets, columns=games | Form: rows=games, columns=sets
                    # batch_data[set_index] = one CSV row (one set's 13 game values)
                    # We need: batch_data[set_index][game_index] but only for first 10 games
                    if game_index >= len(batch_data[set_index]):
                        logger.error(f"CSV doesn't have game {game_index + 1} (only {len(batch_data[set_index])} games)")
                        return False
                    
                    # Form supports 13 games as user confirmed
                        
                    csv_value = batch_data[set_index][game_index]
                    
                    # Convert CSV values to voting page values
                    # CSV: 1=ホーム勝ち, 0=引き分け, 2=アウェイ勝ち  
                    # Page: 0=ホーム勝ち, 1=引き分け, 2=アウェイ勝ち
                    if csv_value == 1:
                        vote_value = 0  # ホーム勝ち
                    elif csv_value == 0:
                        vote_value = 1  # 引き分け
                    elif csv_value == 2:
                        vote_value = 2  # アウェイ勝ち
                    else:
                        logger.error(f"Invalid CSV value: {csv_value}, expected 0, 1, or 2")
                        return False
                    
                    success = self._click_checkbox(game_index, set_index, vote_value)
                    if not success:
                        logger.error(f"Failed to click checkbox for game {game_index + 1}, set {set_index + 1}, value {vote_value}")
                        return False
                    
                    # Small delay between clicks
                    time.sleep(0.1)
                
                logger.info(f"Successfully filled game {game_index + 1}")
            
            logger.info("All games filled successfully")
            return True
            
        except Exception as e:
            logger.error(f"Error filling voting form: {e}")
            return False
    
    def _fill_single_set(self, set_data: List[int], set_index: int) -> bool:
        """
        Fill a single set of voting data
        
        Args:
            set_data: List of 13 values (0, 1, or 2)
            set_index: Index of the current set (0-based)
            
        Returns:
            bool: True if successful, False otherwise
        """
        try:
            if len(set_data) != Config.MAX_GAMES_PER_SET:
                logger.error(f"Invalid set data length: {len(set_data)}, expected {Config.MAX_GAMES_PER_SET}")
                return False
            
            # Process each game (row) for this set (column)
            for game_index, vote_value in enumerate(set_data):
                if vote_value not in Config.VALID_VALUES:
                    logger.error(f"Invalid vote value: {vote_value}, expected one of {Config.VALID_VALUES}")
                    return False
                
                success = self._click_checkbox(game_index, set_index, vote_value)
                if not success:
                    logger.error(f"Failed to click checkbox for game {game_index + 1}, set {set_index + 1}, value {vote_value}")
                    return False
                
                # Small delay between clicks
                time.sleep(0.2)
            
            return True
            
        except Exception as e:
            logger.error(f"Error filling single set: {e}")
            return False
    
    def _click_checkbox(self, game_index: int, set_index: int, vote_value: int) -> bool:
        """
        Click a specific checkbox based on game, set, and vote value
        
        Args:
            game_index: Game index (0-12)
            set_index: Set index (0-9)
            vote_value: Vote value (0, 1, or 2)
            
        Returns:
            bool: True if successful, False otherwise
        """
        try:
            # Determine checkbox name based on game index
            checkbox_name = self._get_checkbox_name(game_index, set_index, vote_value)
            
            # Find and click checkbox
            checkbox = self._find_checkbox_by_name(checkbox_name)
            if not checkbox:
                logger.error(f"Checkbox not found: {checkbox_name}")
                # Debug: Take screenshot and inspect page elements
                self._debug_page_elements(game_index, set_index, vote_value)
                return False
            
            # Click the checkbox
            success = self._safe_click_checkbox(checkbox, checkbox_name)
            if success:
                logger.debug(f"Clicked checkbox: {checkbox_name}")
            
            return success
            
        except Exception as e:
            logger.error(f"Error clicking checkbox: {e}")
            return False
    
    def _get_checkbox_name(self, game_index: int, set_index: int, vote_value: int) -> str:
        """
        Generate checkbox name based on game index, set index, and vote value
        
        Args:
            game_index: Game index (0-12)
            set_index: Set index (0-9)
            vote_value: Vote value (0, 1, or 2)
            
        Returns:
            str: Checkbox name attribute
        """
        # Correct pattern: chkbox_{set}_{game}_{value} (set and game were swapped!)
        return Config.CHECKBOX_PATTERNS['standard'].format(
            game=set_index,    # セット番号が最初
            set=game_index,    # 試合番号が2番目  
            value=vote_value
        )
    
    def _find_checkbox_by_name(self, checkbox_name: str) -> Optional[object]:
        """
        Find checkbox element by name attribute
        
        Args:
            checkbox_name: Name attribute of the checkbox
            
        Returns:
            WebElement if found, None otherwise
        """
        try:
            # Primary method: find by name attribute
            checkbox = self.driver.find_element(By.NAME, checkbox_name)
            return checkbox
            
        except NoSuchElementException:
            # Try alternative selectors
            alternative_selectors = [
                f"input[name='{checkbox_name}']",
                f"input[id='{checkbox_name}']",
                f"input[type='checkbox'][name='{checkbox_name}']"
            ]
            
            for selector in alternative_selectors:
                try:
                    checkbox = self.driver.find_element(By.CSS_SELECTOR, selector)
                    logger.debug(f"Found checkbox using alternative selector: {selector}")
                    return checkbox
                except NoSuchElementException:
                    continue
            
            logger.debug(f"Checkbox not found with any selector: {checkbox_name}")
            return None
        except Exception as e:
            logger.error(f"Error finding checkbox {checkbox_name}: {e}")
            return None
    
    def _safe_click_checkbox(self, checkbox_element: object, checkbox_name: str) -> bool:
        """
        Safely click a checkbox element
        
        Args:
            checkbox_element: WebElement to click
            checkbox_name: Name for logging purposes
            
        Returns:
            bool: True if successful, False otherwise
        """
        try:
            # Check if checkbox is already selected
            if checkbox_element.is_selected():
                logger.debug(f"Checkbox {checkbox_name} is already selected")
                return True
            
            # Scroll element into view first
            try:
                self.driver.execute_script("arguments[0].scrollIntoView({behavior: 'smooth', block: 'center'});", checkbox_element)
                time.sleep(0.2)  # Wait for scroll to complete
            except Exception as e:
                logger.debug(f"Scroll failed for {checkbox_name}: {e}")
            
            # Try direct click first (faster approach)
            try:
                checkbox_element.click()
                logger.debug(f"Direct click successful for {checkbox_name}")
                
                # Verify it was clicked
                if checkbox_element.is_selected():
                    return True
                else:
                    logger.warning(f"Checkbox {checkbox_name} direct click did not register")
                    
            except Exception as click_error:
                logger.debug(f"Direct click failed for {checkbox_name}: {click_error}")
                # Try JavaScript click immediately
                try:
                    self.driver.execute_script("arguments[0].click();", checkbox_element)
                    logger.debug(f"JavaScript click successful for {checkbox_name}")
                    
                    # Verify it was clicked
                    if checkbox_element.is_selected():
                        return True
                    else:
                        logger.warning(f"Checkbox {checkbox_name} JavaScript click did not register")
                        return False
                except Exception as js_error:
                    logger.debug(f"JavaScript click also failed for {checkbox_name}: {js_error}")
                    # Last resort: try with wait
                    try:
                        self.wait.until(EC.element_to_be_clickable(checkbox_element))
                        checkbox_element.click()
                        return checkbox_element.is_selected()
                    except:
                        return False
                
        except Exception as e:
            logger.error(f"All click methods failed for {checkbox_name}: {e}")
            return False
    
    def submit_form(self) -> bool:
        """
        Submit the voting form
        
        Returns:
            bool: True if successful, False otherwise
        """
        try:
            logger.info("Attempting to submit form")
            
            # Debug: Find all potential submit buttons
            all_buttons = self.driver.find_elements(By.CSS_SELECTOR, "button, input[type='submit'], input[type='button']")
            logger.info(f"Found {len(all_buttons)} potential submit buttons:")
            for i, btn in enumerate(all_buttons[:10]):
                btn_text = btn.get_attribute('value') or btn.text or 'no-text'
                btn_type = btn.get_attribute('type') or 'no-type'
                btn_onclick = btn.get_attribute('onclick') or 'no-onclick'
                logger.info(f"  Button {i}: text='{btn_text}', type='{btn_type}', onclick='{btn_onclick}'")
            
            success = self.driver_manager.click_element_safe(
                Config.SELECTORS['submit_button'], 
                "submit button"
            )
            
            if success:
                logger.info("Form submitted successfully")
                # Wait for page to process
                time.sleep(2)
                return True
            else:
                logger.error("Failed to submit form")
                return False
                
        except Exception as e:
            logger.error(f"Error submitting form: {e}")
            return False
    
    def navigate_to_next_form(self) -> bool:
        """
        Navigate to the next form page
        
        Returns:
            bool: True if successful, False otherwise
        """
        try:
            logger.info("Navigating to next form")
            
            success = self.driver_manager.click_element_safe(
                Config.SELECTORS['next_button'], 
                "next button"
            )
            
            if success:
                logger.info("Successfully navigated to next form")
                # Wait for new page to load
                self.driver_manager.wait_for_page_load()
                return True
            else:
                logger.error("Failed to navigate to next form")
                return False
                
        except Exception as e:
            logger.error(f"Error navigating to next form: {e}")
            return False
    
    def confirm_submission(self) -> bool:
        """
        Confirm form submission if required
        
        Returns:
            bool: True if successful, False otherwise
        """
        try:
            logger.info("Looking for confirmation checkbox")
            
            success = self.driver_manager.click_element_safe(
                Config.SELECTORS['confirm_checkbox'], 
                "confirmation checkbox"
            )
            
            if success:
                logger.info("Confirmation checkbox clicked")
                return True
            else:
                logger.info("No confirmation checkbox found or needed")
                return True  # Not finding confirmation is not necessarily an error
                
        except Exception as e:
            logger.error(f"Error with confirmation: {e}")
            return False
    
    def get_form_status(self) -> Dict[str, any]:
        """
        Get current form status and information
        
        Returns:
            dict: Form status information
        """
        try:
            status = {
                "page_title": self.driver.title,
                "current_url": self.driver.current_url,
                "page_loaded": self.driver.execute_script("return document.readyState") == "complete"
            }
            
            # Count checkboxes on current page
            checkboxes = self.driver.find_elements(By.CSS_SELECTOR, "input[type='checkbox']")
            status["total_checkboxes"] = len(checkboxes)
            status["selected_checkboxes"] = len([cb for cb in checkboxes if cb.is_selected()])
            
            return status
            
        except Exception as e:
            logger.error(f"Error getting form status: {e}")
            return {"error": str(e)}
    
    def _debug_page_elements(self, game_index: int, set_index: int, vote_value: int):
        """Debug function to inspect page elements when checkbox is not found"""
        try:
            # Take screenshot
            timestamp = int(time.time())
            screenshot_file = f"debug_checkbox_error_{timestamp}.png"
            self.driver.save_screenshot(screenshot_file)
            logger.info(f"Debug screenshot saved: {screenshot_file}")
            
            # Log page information
            logger.info(f"Current URL: {self.driver.current_url}")
            logger.info(f"Page title: {self.driver.title}")
            
            # Find all checkboxes on the page
            all_checkboxes = self.driver.find_elements(By.CSS_SELECTOR, "input[type='checkbox']")
            logger.info(f"Total checkboxes found on page: {len(all_checkboxes)}")
            
            # Find all unique game indices from checkbox names
            game_indices = set()
            for cb in all_checkboxes:
                name = cb.get_attribute('name') or 'no-name'
                if name.startswith('chkbox_'):
                    try:
                        parts = name.split('_')
                        if len(parts) >= 2:
                            game_index = int(parts[1])
                            game_indices.add(game_index)
                    except:
                        pass
            
            sorted_games = sorted(game_indices)
            logger.info(f"Actual game indices found on page: {sorted_games}")
            logger.info(f"Total games available: {len(sorted_games)}")
            
            # Check 390 checkboxes structure
            total_checkboxes = len(all_checkboxes)
            if total_checkboxes == 390:
                games_calculated = total_checkboxes // (3 * 10)  # 3 choices * 10 sets
                logger.info(f"Calculated games from 390 checkboxes: {games_calculated}")
            
            # Show sample checkboxes for each game found
            for game_idx in sorted_games[:5]:  # First 5 games
                sample_cb = self.driver.find_elements(By.CSS_SELECTOR, f"input[name^='chkbox_{game_idx}_']")
                logger.info(f"Game {game_idx}: found {len(sample_cb)} checkboxes")
            
            # Try to find checkboxes with similar patterns
            similar_patterns = [
                f"chkbox_{game_index}_{set_index}_{vote_value}",
                f"checkbox_{game_index}_{set_index}_{vote_value}", 
                f"chk_{game_index}_{set_index}_{vote_value}",
                f"game{game_index}_set{set_index}_val{vote_value}"
            ]
            
            # Search for any checkbox containing the game index
            logger.info(f"Searching for any checkbox containing game index {game_index}...")
            all_checkboxes_with_game = self.driver.find_elements(By.CSS_SELECTOR, f"input[type='checkbox'][name*='chkbox_{game_index}_']")
            logger.info(f"Found {len(all_checkboxes_with_game)} checkboxes with game index {game_index}")
            
            for i, cb in enumerate(all_checkboxes_with_game[:5]):
                name = cb.get_attribute('name') or 'no-name'
                logger.info(f"  Game {game_index} checkbox {i}: name='{name}'")
            
            for pattern in similar_patterns:
                elements = self.driver.find_elements(By.NAME, pattern)
                if elements:
                    logger.info(f"Found elements with pattern '{pattern}': {len(elements)}")
                    
        except Exception as debug_e:
            logger.error(f"Error in debug function: {debug_e}")
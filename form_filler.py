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
            
            for set_index, set_data in enumerate(batch_data):
                if set_index >= Config.MAX_SETS_PER_BATCH:
                    logger.warning(f"Reached maximum sets per batch ({Config.MAX_SETS_PER_BATCH})")
                    break
                
                success = self._fill_single_set(set_data, set_index)
                if not success:
                    logger.error(f"Failed to fill set {set_index + 1}")
                    return False
                
                logger.info(f"Successfully filled set {set_index + 1}/{len(batch_data)}")
            
            logger.info("All sets filled successfully")
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
            
            for game_index, vote_value in enumerate(set_data):
                if vote_value not in Config.VALID_VALUES:
                    logger.error(f"Invalid vote value: {vote_value}, expected one of {Config.VALID_VALUES}")
                    return False
                
                success = self._click_checkbox(game_index, set_index, vote_value)
                if not success:
                    logger.error(f"Failed to click checkbox for game {game_index + 1}, set {set_index + 1}, value {vote_value}")
                    return False
                
                # Small delay between clicks to avoid issues
                time.sleep(0.1)
            
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
        # Handle special cases for games 11 and 12 (indexes 10 and 11)
        if game_index <= 9:
            # Standard pattern: chkbox_{game}_{set}_{value}
            return Config.CHECKBOX_PATTERNS['standard'].format(
                game=game_index, 
                set=set_index, 
                value=vote_value
            )
        elif game_index == 10:
            # Game 11: chkbox_1_{set}_{value}
            return Config.CHECKBOX_PATTERNS['game_11'].format(
                set=set_index, 
                value=vote_value
            )
        elif game_index == 11:
            # Game 12: chkbox_2_{set}_{value}
            return Config.CHECKBOX_PATTERNS['game_12'].format(
                set=set_index, 
                value=vote_value
            )
        else:
            # Game 13 (index 12) - skip for now
            logger.warning(f"Game 13 (index {game_index}) not supported yet")
            return f"chkbox_unknown_{game_index}_{set_index}_{vote_value}"
    
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
            
            # Wait for element to be clickable
            self.wait.until(EC.element_to_be_clickable(checkbox_element))
            
            # Click the checkbox
            checkbox_element.click()
            
            # Verify it was clicked
            if checkbox_element.is_selected():
                return True
            else:
                logger.warning(f"Checkbox {checkbox_name} click did not register")
                return False
                
        except ElementNotInteractableException:
            # Try JavaScript click as fallback
            try:
                self.driver.execute_script("arguments[0].click();", checkbox_element)
                logger.debug(f"Used JavaScript click for {checkbox_name}")
                return checkbox_element.is_selected()
            except Exception as e:
                logger.error(f"JavaScript click failed for {checkbox_name}: {e}")
                return False
                
        except Exception as e:
            logger.error(f"Error clicking checkbox {checkbox_name}: {e}")
            return False
    
    def submit_form(self) -> bool:
        """
        Submit the voting form
        
        Returns:
            bool: True if successful, False otherwise
        """
        try:
            logger.info("Attempting to submit form")
            
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
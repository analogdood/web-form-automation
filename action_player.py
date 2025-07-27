"""
Action Player for executing recorded action sequences
"""

import logging
import time
from typing import List, Dict, Optional, Any
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import (
    TimeoutException, 
    NoSuchElementException,
    ElementNotInteractableException,
    UnexpectedAlertPresentException
)

from action_manager import ActionStep, ActionSequence, ActionType
from web_driver_manager import WebDriverManager

logger = logging.getLogger(__name__)

class ActionPlayer:
    """Executes recorded action sequences"""
    
    def __init__(self, webdriver_manager: WebDriverManager):
        self.driver_manager = webdriver_manager
        self.driver = webdriver_manager.driver
        self.wait = webdriver_manager.wait
        
        self.execution_stats = {
            "total_actions": 0,
            "successful_actions": 0,
            "failed_actions": 0,
            "skipped_actions": 0,
            "execution_time": 0.0
        }
        
    def execute_action_sequence(self, sequence: ActionSequence) -> bool:
        """
        Execute complete action sequence
        
        Args:
            sequence: ActionSequence to execute
            
        Returns:
            bool: True if sequence executed successfully, False otherwise
        """
        start_time = time.time()
        
        try:
            logger.info(f"Starting execution of action sequence: {sequence.metadata.get('name', 'Unknown')}")
            logger.info(f"Total actions to execute: {len(sequence.batch_actions)}")
            
            self.execution_stats["total_actions"] = len(sequence.batch_actions)
            self.execution_stats["successful_actions"] = 0
            self.execution_stats["failed_actions"] = 0
            self.execution_stats["skipped_actions"] = 0
            
            for i, action in enumerate(sequence.batch_actions, 1):
                logger.info(f"Executing action {i}/{len(sequence.batch_actions)}: {action.action}")
                
                success = self._execute_single_action(action)
                
                if success:
                    self.execution_stats["successful_actions"] += 1
                    logger.info(f"Action {i} completed successfully")
                elif action.optional:
                    self.execution_stats["skipped_actions"] += 1
                    logger.warning(f"Action {i} failed but marked as optional, continuing")
                else:
                    self.execution_stats["failed_actions"] += 1
                    logger.error(f"Action {i} failed and is required, stopping execution")
                    return False
            
            execution_time = time.time() - start_time
            self.execution_stats["execution_time"] = execution_time
            
            logger.info(f"Action sequence completed successfully in {execution_time:.2f} seconds")
            logger.info(f"Stats: {self.execution_stats}")
            
            return True
            
        except Exception as e:
            logger.error(f"Action sequence execution failed: {e}")
            return False
    
    def _execute_single_action(self, action: ActionStep) -> bool:
        """
        Execute a single action step with retry logic
        
        Args:
            action: ActionStep to execute
            
        Returns:
            bool: True if successful, False otherwise
        """
        # Wait before action if specified
        if action.wait_before > 0:
            logger.debug(f"Waiting {action.wait_before} seconds before action")
            time.sleep(action.wait_before)
        
        # Execute action with retries
        for attempt in range(action.retry_count):
            try:
                success = self._perform_action(action)
                
                if success:
                    # Wait after action if specified
                    if action.wait_after > 0:
                        logger.debug(f"Waiting {action.wait_after} seconds after action")
                        time.sleep(action.wait_after)
                    return True
                else:
                    logger.warning(f"Action attempt {attempt + 1} failed")
                    
            except Exception as e:
                logger.warning(f"Action attempt {attempt + 1} failed with exception: {e}")
            
            # Wait between retries
            if attempt < action.retry_count - 1:
                logger.debug(f"Retrying action in 1 second...")
                time.sleep(1)
        
        logger.error(f"Action failed after {action.retry_count} attempts")
        return False
    
    def _perform_action(self, action: ActionStep) -> bool:
        """
        Perform the actual action based on action type
        
        Args:
            action: ActionStep to perform
            
        Returns:
            bool: True if successful, False otherwise
        """
        action_type = action.action.lower()
        
        if action_type == ActionType.CLICK.value:
            return self._execute_click(action)
        elif action_type == ActionType.WAIT_FOR_ELEMENT.value:
            return self._execute_wait_for_element(action)
        elif action_type == ActionType.WAIT_FOR_URL_CHANGE.value:
            return self._execute_wait_for_url_change(action)
        elif action_type == ActionType.WAIT_FOR_ALERT.value:
            return self._execute_wait_for_alert(action)
        elif action_type == ActionType.INPUT_TEXT.value:
            return self._execute_input_text(action)
        elif action_type == ActionType.SCREENSHOT.value:
            return self._execute_screenshot(action)
        elif action_type == ActionType.SLEEP.value:
            return self._execute_sleep(action)
        elif action_type == ActionType.CONFIRM_CHECKBOX.value:
            return self._execute_confirm_checkbox(action)
        elif action_type == ActionType.SUBMIT_FORM.value:
            return self._execute_submit_form(action)
        else:
            logger.error(f"Unknown action type: {action_type}")
            return False
    
    def _execute_click(self, action: ActionStep) -> bool:
        """Execute click action"""
        try:
            element = self._find_element_safe(action.selector, action.timeout)
            if not element:
                return False
            
            # Wait for element to be clickable
            clickable_element = WebDriverWait(self.driver, action.timeout).until(
                EC.element_to_be_clickable(element)
            )
            
            clickable_element.click()
            logger.debug(f"Clicked element: {action.selector}")
            return True
            
        except ElementNotInteractableException:
            # Try JavaScript click as fallback
            try:
                element = self._find_element_safe(action.selector, action.timeout)
                if element:
                    self.driver.execute_script("arguments[0].click();", element)
                    logger.debug(f"Clicked element using JavaScript: {action.selector}")
                    return True
            except Exception as e:
                logger.error(f"JavaScript click failed: {e}")
                
        except Exception as e:
            logger.error(f"Click action failed: {e}")
            
        return False
    
    def _execute_wait_for_element(self, action: ActionStep) -> bool:
        """Execute wait for element action"""
        try:
            element = self._find_element_safe(action.selector, action.timeout)
            if element:
                logger.debug(f"Element found: {action.selector}")
                return True
            else:
                logger.warning(f"Element not found within timeout: {action.selector}")
                return False
                
        except Exception as e:
            logger.error(f"Wait for element failed: {e}")
            return False
    
    def _execute_wait_for_url_change(self, action: ActionStep) -> bool:
        """Execute wait for URL change action"""
        try:
            current_url = self.driver.current_url
            expected_pattern = action.value
            
            # Wait for URL to contain expected pattern
            def url_contains_pattern(driver):
                return expected_pattern.lower() in driver.current_url.lower()
            
            WebDriverWait(self.driver, action.timeout).until(url_contains_pattern)
            
            new_url = self.driver.current_url
            logger.debug(f"URL changed from {current_url} to {new_url}")
            return True
            
        except TimeoutException:
            logger.warning(f"URL did not change to contain '{action.value}' within {action.timeout} seconds")
            return False
        except Exception as e:
            logger.error(f"Wait for URL change failed: {e}")
            return False
    
    def _execute_wait_for_alert(self, action: ActionStep) -> bool:
        """Execute wait for alert action"""
        try:
            # Wait for alert to be present
            WebDriverWait(self.driver, action.timeout).until(EC.alert_is_present())
            alert = self.driver.switch_to.alert
            
            alert_text = alert.text
            logger.debug(f"Alert detected: {alert_text}")
            
            # Accept or dismiss based on action value
            if action.value and action.value.lower() == "dismiss":
                alert.dismiss()
                logger.debug("Alert dismissed")
            else:
                alert.accept()
                logger.debug("Alert accepted")
            
            return True
            
        except TimeoutException:
            logger.debug(f"No alert appeared within {action.timeout} seconds")
            return action.optional  # Return success if optional
        except Exception as e:
            logger.error(f"Alert handling failed: {e}")
            return False
    
    def _execute_input_text(self, action: ActionStep) -> bool:
        """Execute input text action"""
        try:
            element = self._find_element_safe(action.selector, action.timeout)
            if not element:
                return False
            
            # Clear existing text and input new text
            element.clear()
            element.send_keys(action.value)
            
            logger.debug(f"Input text '{action.value}' to element: {action.selector}")
            return True
            
        except Exception as e:
            logger.error(f"Input text action failed: {e}")
            return False
    
    def _execute_screenshot(self, action: ActionStep) -> bool:
        """Execute screenshot action"""
        try:
            filename = action.value or f"action_screenshot_{int(time.time())}.png"
            screenshot_path = self.driver_manager.screenshot(filename)
            
            if screenshot_path:
                logger.debug(f"Screenshot saved: {screenshot_path}")
                return True
            else:
                logger.warning("Screenshot failed")
                return False
                
        except Exception as e:
            logger.error(f"Screenshot action failed: {e}")
            return False
    
    def _execute_sleep(self, action: ActionStep) -> bool:
        """Execute sleep action"""
        try:
            duration = float(action.value) if action.value else 1.0
            logger.debug(f"Sleeping for {duration} seconds")
            time.sleep(duration)
            return True
            
        except Exception as e:
            logger.error(f"Sleep action failed: {e}")
            return False
    
    def _execute_confirm_checkbox(self, action: ActionStep) -> bool:
        """Execute confirm checkbox action"""
        try:
            element = self._find_element_safe(action.selector, action.timeout)
            if not element:
                return False
            
            # Check if already selected
            if not element.is_selected():
                element.click()
                logger.debug(f"Checked checkbox: {action.selector}")
            else:
                logger.debug(f"Checkbox already checked: {action.selector}")
            
            return True
            
        except Exception as e:
            logger.error(f"Confirm checkbox action failed: {e}")
            return False
    
    def _execute_submit_form(self, action: ActionStep) -> bool:
        """Execute submit form action"""
        try:
            # Try to find and click submit button first
            element = self._find_element_safe(action.selector, action.timeout)
            if element:
                if element.tag_name.lower() == 'form':
                    # Submit form directly
                    element.submit()
                    logger.debug(f"Submitted form: {action.selector}")
                else:
                    # Click submit button
                    element.click()
                    logger.debug(f"Clicked submit button: {action.selector}")
                
                return True
            
            return False
            
        except Exception as e:
            logger.error(f"Submit form action failed: {e}")
            return False
    
    def _find_element_safe(self, selector: str, timeout: float = 10) -> Optional[Any]:
        """
        Safely find element with multiple selector strategies
        
        Args:
            selector: CSS selector
            timeout: Maximum wait time
            
        Returns:
            WebElement if found, None otherwise
        """
        try:
            # Try CSS selector first
            element = WebDriverWait(self.driver, timeout).until(
                EC.presence_of_element_located((By.CSS_SELECTOR, selector))
            )
            return element
            
        except TimeoutException:
            # Try as XPath if CSS fails
            if not selector.startswith("//"):
                xpath_selector = f"//*[@id='{selector}'] | //*[@class='{selector}'] | //*[@name='{selector}']"
                try:
                    element = WebDriverWait(self.driver, 2).until(
                        EC.presence_of_element_located((By.XPATH, xpath_selector))
                    )
                    return element
                except TimeoutException:
                    pass
            
            logger.warning(f"Element not found: {selector}")
            return None
            
        except Exception as e:
            logger.error(f"Error finding element {selector}: {e}")
            return None
    
    def get_execution_stats(self) -> Dict[str, Any]:
        """Get execution statistics"""
        return self.execution_stats.copy()
    
    def reset_stats(self):
        """Reset execution statistics"""
        self.execution_stats = {
            "total_actions": 0,
            "successful_actions": 0,
            "failed_actions": 0,
            "skipped_actions": 0,
            "execution_time": 0.0
        }
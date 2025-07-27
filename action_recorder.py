"""
Action Recorder for capturing user interactions with web forms
"""

import logging
import time
from typing import List, Optional, Dict, Any
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException, NoSuchElementException

from action_manager import ActionStep, ActionSequence, ActionType, ActionFileManager
from web_driver_manager import WebDriverManager

logger = logging.getLogger(__name__)

class ActionRecorder:
    """Records user interactions for later playback"""
    
    def __init__(self, webdriver_manager: WebDriverManager):
        self.driver_manager = webdriver_manager
        self.driver = webdriver_manager.driver
        self.wait = webdriver_manager.wait
        
        self.recorded_actions: List[ActionStep] = []
        self.current_url = ""
        self.recording_session = {
            "start_time": time.time(),
            "site_url": "",
            "form_structure": {}
        }
        
    def start_recording_session(self, site_url: str = None) -> bool:
        """
        Start a new recording session
        
        Args:
            site_url: Target website URL to navigate to
            
        Returns:
            bool: True if successful, False otherwise
        """
        try:
            logger.info("Starting action recording session")
            
            if site_url:
                logger.info(f"Navigating to: {site_url}")
                if not self.driver_manager.navigate_to_url(site_url):
                    logger.error("Failed to navigate to target URL")
                    return False
            
            self.current_url = self.driver.current_url
            self.recording_session["site_url"] = self.current_url
            self.recorded_actions.clear()
            
            logger.info("Recording session started successfully")
            logger.info("Manual operations will be detected and recorded")
            
            return True
            
        except Exception as e:
            logger.error(f"Failed to start recording session: {e}")
            return False
    
    def record_interactive_session(self) -> ActionSequence:
        """
        Record actions through interactive user guidance
        
        Returns:
            ActionSequence: Recorded action sequence
        """
        logger.info("Starting interactive recording session")
        logger.info("You will be guided through the recording process")
        
        # Analyze current page structure
        self._analyze_form_structure()
        
        # Interactive recording loop
        step_count = 1
        while True:
            print(f"\n--- Recording Step {step_count} ---")
            print("Current URL:", self.driver.current_url)
            print("Available actions:")
            print("1. Record Click Action")
            print("2. Record Wait for Element")
            print("3. Record Wait for URL Change") 
            print("4. Record Alert Handling")
            print("5. Record Form Submission")
            print("6. Record Screenshot")
            print("7. Add Wait/Sleep")
            print("8. Finish Recording")
            
            choice = input("Select action to record (1-8): ").strip()
            
            if choice == "1":
                self._record_click_action()
            elif choice == "2":
                self._record_wait_for_element()
            elif choice == "3":
                self._record_wait_for_url_change()
            elif choice == "4":
                self._record_alert_handling()
            elif choice == "5":
                self._record_form_submission()
            elif choice == "6":
                self._record_screenshot()
            elif choice == "7":
                self._record_sleep()
            elif choice == "8":
                break
            else:
                print("Invalid choice. Please try again.")
                continue
            
            step_count += 1
        
        # Create action sequence
        metadata = {
            "name": f"Recorded Actions - {time.strftime('%Y%m%d_%H%M%S')}",
            "description": "Interactive recorded action sequence",
            "site_url": self.recording_session["site_url"],
            "recorded_at": time.strftime('%Y-%m-%d %H:%M:%S'),
            "form_structure": self.recording_session["form_structure"]
        }
        
        return ActionSequence(metadata=metadata, batch_actions=self.recorded_actions)
    
    def _analyze_form_structure(self):
        """Analyze current page form structure"""
        try:
            # Find forms
            forms = self.driver.find_elements(By.TAG_NAME, "form")
            
            # Find common button elements
            buttons = self.driver.find_elements(By.CSS_SELECTOR, "button, input[type='submit'], input[type='button']")
            
            # Find checkbox groups (assuming our voting form structure)
            checkboxes = self.driver.find_elements(By.CSS_SELECTOR, "input[type='checkbox']")
            
            structure = {
                "forms_count": len(forms),
                "buttons_count": len(buttons),
                "checkboxes_count": len(checkboxes),
                "common_selectors": []
            }
            
            # Identify common button selectors
            for button in buttons[:5]:  # Limit to first 5 buttons
                try:
                    if button.get_attribute("class"):
                        structure["common_selectors"].append(f".{button.get_attribute('class').replace(' ', '.')}")
                    if button.get_attribute("id"):
                        structure["common_selectors"].append(f"#{button.get_attribute('id')}")
                except:
                    pass
            
            self.recording_session["form_structure"] = structure
            logger.info(f"Analyzed form structure: {structure}")
            
        except Exception as e:
            logger.error(f"Failed to analyze form structure: {e}")
    
    def _record_click_action(self):
        """Record a click action with user guidance"""
        print("\n=== Recording Click Action ===")
        print("1. Manually click the element you want to record")
        print("2. Press Enter when done")
        
        # Get current state
        initial_url = self.driver.current_url
        
        input("Press Enter after clicking the element...")
        
        # Check for URL change
        new_url = self.driver.current_url
        url_changed = initial_url != new_url
        
        # Get element selector from user
        print("\nNow we need to identify the element you clicked.")
        print("Common element identification methods:")
        
        # Try to suggest selectors
        suggested_selectors = self._suggest_selectors()
        
        if suggested_selectors:
            print("Suggested selectors:")
            for i, selector in enumerate(suggested_selectors, 1):
                print(f"{i}. {selector}")
            print(f"{len(suggested_selectors) + 1}. Enter custom selector")
            
            choice = input("Select selector or enter custom (number): ").strip()
            
            try:
                choice_num = int(choice)
                if 1 <= choice_num <= len(suggested_selectors):
                    selector = suggested_selectors[choice_num - 1]
                else:
                    selector = input("Enter custom CSS selector: ").strip()
            except ValueError:
                selector = input("Enter CSS selector: ").strip()
        else:
            selector = input("Enter CSS selector for the clicked element: ").strip()
        
        description = input("Enter description for this action (optional): ").strip()
        
        # Create action step
        action = ActionStep(
            action=ActionType.CLICK.value,
            selector=selector,
            description=description or f"Click element: {selector}",
            wait_after=2.0 if url_changed else 1.0
        )
        
        self.recorded_actions.append(action)
        logger.info(f"Recorded click action: {selector}")
        
        # If URL changed, suggest recording URL change wait
        if url_changed:
            print(f"\nURL changed from {initial_url} to {new_url}")
            record_url_wait = input("Record URL change wait? (y/n): ").lower().startswith('y')
            if record_url_wait:
                self._add_url_change_wait(initial_url, new_url)
    
    def _record_wait_for_element(self):
        """Record wait for element action"""
        print("\n=== Recording Wait for Element ===")
        selector = input("Enter CSS selector for element to wait for: ").strip()
        timeout = input("Enter timeout in seconds (default 10): ").strip()
        description = input("Enter description (optional): ").strip()
        
        try:
            timeout = float(timeout) if timeout else 10.0
        except ValueError:
            timeout = 10.0
        
        action = ActionStep(
            action=ActionType.WAIT_FOR_ELEMENT.value,
            selector=selector,
            description=description or f"Wait for element: {selector}",
            timeout=timeout
        )
        
        self.recorded_actions.append(action)
        logger.info(f"Recorded wait for element: {selector}")
    
    def _record_wait_for_url_change(self):
        """Record wait for URL change action"""
        print("\n=== Recording Wait for URL Change ===")
        current_url = self.driver.current_url
        print(f"Current URL: {current_url}")
        
        expected_pattern = input("Enter expected URL pattern/substring: ").strip()
        timeout = input("Enter timeout in seconds (default 15): ").strip()
        description = input("Enter description (optional): ").strip()
        
        try:
            timeout = float(timeout) if timeout else 15.0
        except ValueError:
            timeout = 15.0
        
        action = ActionStep(
            action=ActionType.WAIT_FOR_URL_CHANGE.value,
            value=expected_pattern,
            description=description or f"Wait for URL containing: {expected_pattern}",
            timeout=timeout
        )
        
        self.recorded_actions.append(action)
        logger.info(f"Recorded wait for URL change: {expected_pattern}")
    
    def _record_alert_handling(self):
        """Record alert handling action"""
        print("\n=== Recording Alert Handling ===")
        print("1. Accept alert")
        print("2. Dismiss alert")
        
        choice = input("Select option (1-2): ").strip()
        accept = choice == "1"
        
        description = input("Enter description (optional): ").strip()
        
        action = ActionStep(
            action=ActionType.WAIT_FOR_ALERT.value,
            value="accept" if accept else "dismiss",
            description=description or f"{'Accept' if accept else 'Dismiss'} alert dialog",
            timeout=5.0
        )
        
        self.recorded_actions.append(action)
        logger.info(f"Recorded alert handling: {'accept' if accept else 'dismiss'}")
    
    def _record_form_submission(self):
        """Record form submission action"""
        print("\n=== Recording Form Submission ===")
        selector = input("Enter form selector or submit button selector: ").strip()
        description = input("Enter description (optional): ").strip()
        
        action = ActionStep(
            action=ActionType.SUBMIT_FORM.value,
            selector=selector,
            description=description or f"Submit form: {selector}",
            wait_after=3.0
        )
        
        self.recorded_actions.append(action)
        logger.info(f"Recorded form submission: {selector}")
    
    def _record_screenshot(self):
        """Record screenshot action"""
        print("\n=== Recording Screenshot ===")
        filename = input("Enter filename (optional, auto-generated if empty): ").strip()
        description = input("Enter description (optional): ").strip()
        
        action = ActionStep(
            action=ActionType.SCREENSHOT.value,
            value=filename or None,
            description=description or "Take screenshot",
            wait_after=0.5
        )
        
        self.recorded_actions.append(action)
        logger.info("Recorded screenshot action")
    
    def _record_sleep(self):
        """Record sleep/wait action"""
        print("\n=== Recording Sleep/Wait ===")
        duration = input("Enter wait duration in seconds: ").strip()
        description = input("Enter description (optional): ").strip()
        
        try:
            duration = float(duration)
        except ValueError:
            print("Invalid duration, using 1.0 seconds")
            duration = 1.0
        
        action = ActionStep(
            action=ActionType.SLEEP.value,
            value=str(duration),
            description=description or f"Wait {duration} seconds"
        )
        
        self.recorded_actions.append(action)
        logger.info(f"Recorded sleep action: {duration} seconds")
    
    def _suggest_selectors(self) -> List[str]:
        """Suggest common selectors based on page analysis"""
        selectors = []
        
        try:
            # Common button selectors
            common_patterns = [
                "button[type='submit']",
                "input[type='submit']",
                ".btn-submit",
                ".submit-btn", 
                ".button",
                "#submit",
                "button.primary",
                "a.btn"
            ]
            
            for pattern in common_patterns:
                try:
                    elements = self.driver.find_elements(By.CSS_SELECTOR, pattern)
                    if elements:
                        selectors.append(pattern)
                except:
                    pass
                    
        except Exception as e:
            logger.debug(f"Error suggesting selectors: {e}")
        
        return selectors[:5]  # Return top 5 suggestions
    
    def _add_url_change_wait(self, old_url: str, new_url: str):
        """Add URL change wait action"""
        # Extract meaningful part of new URL
        if "confirmation" in new_url.lower():
            pattern = "confirmation"
        elif "success" in new_url.lower():
            pattern = "success"
        elif "next" in new_url.lower():
            pattern = "next"
        else:
            # Use last part of URL path
            try:
                pattern = new_url.split('/')[-1].split('?')[0]
            except:
                pattern = "changed"
        
        action = ActionStep(
            action=ActionType.WAIT_FOR_URL_CHANGE.value,
            value=pattern,
            description=f"Wait for URL change to contain: {pattern}",
            timeout=15.0
        )
        
        self.recorded_actions.append(action)
        logger.info(f"Added URL change wait for pattern: {pattern}")
    
    def save_recorded_actions(self, filename: str) -> bool:
        """
        Save recorded actions to file
        
        Args:
            filename: Output filename
            
        Returns:
            bool: True if successful, False otherwise
        """
        if not self.recorded_actions:
            logger.warning("No actions recorded to save")
            return False
        
        # Create action sequence
        metadata = {
            "name": f"Recorded Actions - {time.strftime('%Y%m%d_%H%M%S')}",
            "description": "User recorded action sequence",
            "site_url": self.recording_session["site_url"],
            "recorded_at": time.strftime('%Y-%m-%d %H:%M:%S'),
            "total_actions": len(self.recorded_actions),
            "form_structure": self.recording_session.get("form_structure", {})
        }
        
        sequence = ActionSequence(metadata=metadata, batch_actions=self.recorded_actions)
        
        # Save to file
        file_manager = ActionFileManager()
        return file_manager.save_actions(sequence, filename)
    
    def get_recorded_actions(self) -> List[ActionStep]:
        """Get currently recorded actions"""
        return self.recorded_actions.copy()
    
    def clear_recorded_actions(self):
        """Clear all recorded actions"""
        self.recorded_actions.clear()
        logger.info("Recorded actions cleared")
    
    def preview_recorded_actions(self):
        """Display preview of recorded actions"""
        if not self.recorded_actions:
            print("No actions recorded yet")
            return
        
        print(f"\n=== Recorded Actions Preview ({len(self.recorded_actions)} actions) ===")
        for i, action in enumerate(self.recorded_actions, 1):
            print(f"{i:2d}. {action.action.upper()}")
            if action.selector:
                print(f"     Selector: {action.selector}")
            if action.value:
                print(f"     Value: {action.value}")
            if action.description:
                print(f"     Description: {action.description}")
            print(f"     Wait: before={action.wait_before}s, after={action.wait_after}s")
            print()
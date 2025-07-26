"""
WebDriver Manager for Web Form Automation System
"""

import logging
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import (
    TimeoutException, 
    NoSuchElementException, 
    WebDriverException,
    ElementNotInteractableException
)
from webdriver_manager.chrome import ChromeDriverManager
from webdriver_manager.firefox import GeckoDriverManager
from webdriver_manager.microsoft import EdgeChromiumDriverManager
from config import Config
import time
from typing import Optional, List, Union

logger = logging.getLogger(__name__)

class WebDriverManager:
    """Manages WebDriver lifecycle and common operations"""
    
    def __init__(self, browser: str = None, headless: bool = None, timeout: int = None):
        self.browser = browser or Config.BROWSER
        self.headless = headless if headless is not None else Config.HEADLESS_MODE
        self.timeout = timeout or Config.WEBDRIVER_TIMEOUT
        
        self.driver: Optional[webdriver.Chrome] = None
        self.wait: Optional[WebDriverWait] = None
        
    def setup_driver(self) -> bool:
        """
        Initialize and configure WebDriver
        
        Returns:
            bool: True if successful, False otherwise
        """
        try:
            logger.info(f"Setting up {self.browser} WebDriver (headless: {self.headless})")
            
            if self.browser.lower() == "chrome":
                self._setup_chrome_driver()
            elif self.browser.lower() == "firefox":
                self._setup_firefox_driver()
            elif self.browser.lower() == "edge":
                self._setup_edge_driver()
            else:
                logger.error(f"Unsupported browser: {self.browser}")
                return False
            
            # Configure timeouts
            self.driver.implicitly_wait(Config.IMPLICIT_WAIT)
            self.driver.set_page_load_timeout(Config.PAGE_LOAD_TIMEOUT)
            
            # Initialize WebDriverWait
            self.wait = WebDriverWait(self.driver, self.timeout)
            
            logger.info("WebDriver setup completed successfully")
            return True
            
        except WebDriverException as e:
            logger.error(f"WebDriver setup failed: {e}")
            return False
        except Exception as e:
            logger.error(f"Unexpected error during WebDriver setup: {e}")
            return False
    
    def _setup_chrome_driver(self):
        """Setup Chrome WebDriver"""
        options = Config.get_chrome_options()
        if self.headless:
            options.add_argument("--headless")
        
        service = webdriver.chrome.service.Service(ChromeDriverManager().install())
        self.driver = webdriver.Chrome(service=service, options=options)
    
    def _setup_firefox_driver(self):
        """Setup Firefox WebDriver"""
        options = Config.get_firefox_options()
        if self.headless:
            options.add_argument("--headless")
        
        service = webdriver.firefox.service.Service(GeckoDriverManager().install())
        self.driver = webdriver.Firefox(service=service, options=options)
    
    def _setup_edge_driver(self):
        """Setup Edge WebDriver"""
        options = webdriver.edge.options.Options()
        if self.headless:
            options.add_argument("--headless")
        
        service = webdriver.edge.service.Service(EdgeChromiumDriverManager().install())
        self.driver = webdriver.Edge(service=service, options=options)
    
    def navigate_to_url(self, url: str) -> bool:
        """
        Navigate to a specific URL
        
        Args:
            url: Target URL
            
        Returns:
            bool: True if successful, False otherwise
        """
        try:
            logger.info(f"Navigating to: {url}")
            self.driver.get(url)
            
            # Wait for page to load
            self.wait.until(
                lambda driver: driver.execute_script("return document.readyState") == "complete"
            )
            
            logger.info("Page loaded successfully")
            return True
            
        except TimeoutException:
            logger.error("Page load timeout")
            return False
        except WebDriverException as e:
            logger.error(f"Navigation failed: {e}")
            return False
    
    def find_element_safe(self, selectors: List[str], element_name: str = "element") -> Optional[object]:
        """
        Find element using multiple selector strategies
        
        Args:
            selectors: List of CSS selectors to try
            element_name: Name for logging purposes
            
        Returns:
            WebElement if found, None otherwise
        """
        for selector in selectors:
            try:
                # Handle different selector types
                if selector.startswith("//"):
                    # XPath selector
                    element = self.wait.until(
                        EC.presence_of_element_located((By.XPATH, selector))
                    )
                elif ":contains(" in selector:
                    # Convert CSS :contains to XPath
                    text = selector.split(":contains('")[1].split("')")[0]
                    tag = selector.split(":contains(")[0] or "*"
                    xpath = f"//{tag}[contains(text(), '{text}')]"
                    element = self.wait.until(
                        EC.presence_of_element_located((By.XPATH, xpath))
                    )
                else:
                    # CSS selector
                    element = self.wait.until(
                        EC.presence_of_element_located((By.CSS_SELECTOR, selector))
                    )
                
                logger.debug(f"Found {element_name} using selector: {selector}")
                return element
                
            except TimeoutException:
                logger.debug(f"Selector failed: {selector}")
                continue
            except Exception as e:
                logger.debug(f"Error with selector '{selector}': {e}")
                continue
        
        logger.warning(f"Could not find {element_name} with any provided selectors")
        return None
    
    def click_element_safe(self, selectors: List[str], element_name: str = "element") -> bool:
        """
        Click element using multiple selector strategies
        
        Args:
            selectors: List of selectors to try
            element_name: Name for logging purposes
            
        Returns:
            bool: True if successful, False otherwise
        """
        element = self.find_element_safe(selectors, element_name)
        if not element:
            return False
        
        try:
            # Wait for element to be clickable
            clickable_element = self.wait.until(EC.element_to_be_clickable(element))
            clickable_element.click()
            logger.info(f"Successfully clicked {element_name}")
            return True
            
        except ElementNotInteractableException:
            logger.warning(f"{element_name} not interactable, trying JavaScript click")
            try:
                self.driver.execute_script("arguments[0].click();", element)
                logger.info(f"Successfully clicked {element_name} using JavaScript")
                return True
            except Exception as e:
                logger.error(f"JavaScript click failed for {element_name}: {e}")
                return False
                
        except Exception as e:
            logger.error(f"Failed to click {element_name}: {e}")
            return False
    
    def handle_alert(self, accept: bool = True) -> bool:
        """
        Handle browser alert dialog
        
        Args:
            accept: True to accept alert, False to dismiss
            
        Returns:
            bool: True if alert was handled, False if no alert
        """
        try:
            WebDriverWait(self.driver, 5).until(EC.alert_is_present())
            alert = self.driver.switch_to.alert
            
            alert_text = alert.text
            logger.info(f"Alert detected: {alert_text}")
            
            if accept:
                alert.accept()
                logger.info("Alert accepted")
            else:
                alert.dismiss()
                logger.info("Alert dismissed")
            
            return True
            
        except TimeoutException:
            logger.debug("No alert present")
            return False
        except Exception as e:
            logger.error(f"Error handling alert: {e}")
            return False
    
    def wait_for_page_load(self, timeout: Optional[int] = None) -> bool:
        """
        Wait for page to fully load
        
        Args:
            timeout: Custom timeout (uses default if None)
            
        Returns:
            bool: True if page loaded, False if timeout
        """
        try:
            wait_time = timeout or self.timeout
            WebDriverWait(self.driver, wait_time).until(
                lambda driver: driver.execute_script("return document.readyState") == "complete"
            )
            logger.debug("Page load completed")
            return True
            
        except TimeoutException:
            logger.warning("Page load timeout")
            return False
    
    def screenshot(self, filename: str = None) -> str:
        """
        Take a screenshot
        
        Args:
            filename: Custom filename (auto-generated if None)
            
        Returns:
            str: Screenshot filename
        """
        if not filename:
            timestamp = time.strftime("%Y%m%d_%H%M%S")
            filename = f"screenshot_{timestamp}.png"
        
        try:
            self.driver.save_screenshot(filename)
            logger.info(f"Screenshot saved: {filename}")
            return filename
        except Exception as e:
            logger.error(f"Failed to take screenshot: {e}")
            return ""
    
    def quit_driver(self):
        """Safely quit the WebDriver"""
        if self.driver:
            try:
                self.driver.quit()
                logger.info("WebDriver quit successfully")
            except Exception as e:
                logger.error(f"Error quitting WebDriver: {e}")
            finally:
                self.driver = None
                self.wait = None
    
    def __enter__(self):
        """Context manager entry"""
        self.setup_driver()
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        """Context manager exit"""
        self.quit_driver()
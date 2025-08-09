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
    ElementNotInteractableException,
    InvalidSessionIdException,
)
from selenium.webdriver.chrome.options import Options as ChromeOptions
from selenium.webdriver.chrome.service import Service as ChromeService
from selenium.webdriver.firefox.options import Options as FirefoxOptions
from selenium.webdriver.firefox.service import Service as FirefoxService
from selenium.webdriver.edge.options import Options as EdgeOptions
from selenium.webdriver.edge.service import Service as EdgeService
from selenium.webdriver.remote.webdriver import WebDriver as RemoteWebDriver
from webdriver_manager.chrome import ChromeDriverManager
from webdriver_manager.firefox import GeckoDriverManager
from webdriver_manager.microsoft import EdgeChromiumDriverManager
from config import Config
import time
from typing import Optional, List, Union
from selenium.webdriver.remote.webelement import WebElement
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.common.action_chains import ActionChains

logger = logging.getLogger(__name__)

class WebDriverManager:
    """Manages WebDriver lifecycle and common operations"""
    
    def __init__(self, browser: Optional[str] = None, headless: Optional[bool] = None, timeout: Optional[int] = None):
        self.browser = browser or Config.BROWSER
        self.headless = headless if headless is not None else Config.HEADLESS_MODE
        self.timeout = timeout or Config.WEBDRIVER_TIMEOUT
        
        # Use generic RemoteWebDriver for cross-browser typing
        self.driver: Optional[RemoteWebDriver] = None
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
            assert self.driver is not None
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
        try:
            # Speed up by not waiting for all subresources
            options.page_load_strategy = "eager"  # type: ignore[attr-defined]
        except Exception:
            pass
        if self.headless:
            options.add_argument("--headless")
        service = ChromeService(ChromeDriverManager().install())
        self.driver = webdriver.Chrome(service=service, options=options)
    
    def _setup_firefox_driver(self):
        """Setup Firefox WebDriver"""
        options = Config.get_firefox_options()
        try:
            options.page_load_strategy = "eager"  # type: ignore[attr-defined]
        except Exception:
            pass
        if self.headless:
            options.add_argument("--headless")
        service = FirefoxService(GeckoDriverManager().install())
        self.driver = webdriver.Firefox(service=service, options=options)
    
    def _setup_edge_driver(self):
        """Setup Edge WebDriver"""
        options = EdgeOptions()
        try:
            options.page_load_strategy = "eager"  # type: ignore[attr-defined]
        except Exception:
            pass
        if self.headless:
            options.add_argument("--headless")
        # Stability flags (safe to apply even non-headless)
        options.add_argument("--disable-gpu")
        options.add_argument("--no-sandbox")
        options.add_argument("--disable-dev-shm-usage")
        options.add_argument("--window-size=1920,1080")
        # Prefer system EdgeDriver first (fast), avoid network in offline environments
        try:
            service = EdgeService()
            self.driver = webdriver.Edge(service=service, options=options)
            return
        except Exception as system_err:
            logger.warning(f"System EdgeDriver not available: {system_err}")
            # Try auto-download only if network allows; otherwise, fall back quickly to Chrome
            try:
                service = EdgeService(EdgeChromiumDriverManager().install())
                self.driver = webdriver.Edge(service=service, options=options)
                return
            except Exception as e:
                logger.warning(f"Failed to auto-download EdgeDriver: {e}")
                logger.info("Edge WebDriver unavailable, falling back to Chrome...")
                try:
                    self._setup_chrome_driver()
                    return
                except Exception as chrome_err:
                    raise Exception(
                        f"All WebDriver options failed. Edge system: {system_err}, Edge auto-download: {e}, Chrome fallback: {chrome_err}"
                    )
    
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
            assert self.driver is not None and self.wait is not None

            attempts = 0
            max_attempts = 3
            last_err: Optional[Exception] = None
            while attempts < max_attempts:
                attempts += 1
                try:
                    self.driver.get(url)
                    # Wait for page to load sufficiently
                    self.wait.until(
                        lambda driver: driver.execute_script("return document.readyState") in ("interactive", "complete")
                    )

                    current = self.driver.current_url or ""
                    if current.startswith("data:"):
                        logger.warning(f"Still at blank page (data:). Attempt {attempts}/{max_attempts} will retry...")
                        time.sleep(1)
                        continue

                    logger.info("Page loaded successfully")
                    return True
                except TimeoutException as e:
                    last_err = e
                    logger.warning(f"Page load timeout (attempt {attempts}/{max_attempts}). Retrying...")
                    continue
                except WebDriverException as e:
                    last_err = e
                    logger.warning(f"Navigation error (attempt {attempts}/{max_attempts}): {e}")
                    time.sleep(1)
                    continue

            if last_err:
                logger.error(f"Navigation failed after {max_attempts} attempts: {last_err}")
            else:
                logger.error(f"Navigation failed after {max_attempts} attempts for unknown reasons")
            return False
        except Exception as e:
            logger.error(f"Unexpected error during navigation: {e}")
            return False
    
    def find_element_safe(self, selectors: List[str], element_name: str = "element") -> Optional[WebElement]:
        """
        Find element using multiple selector strategies
        
        Args:
            selectors: List of CSS selectors to try
            element_name: Name for logging purposes
            
        Returns:
            WebElement if found, None otherwise
        """
        assert self.wait is not None and self.driver is not None
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
            assert self.wait is not None and self.driver is not None
            clickable_element = self.wait.until(EC.element_to_be_clickable(element))
            clickable_element.click()
            logger.info(f"Successfully clicked {element_name}")
            return True
            
        except ElementNotInteractableException:
            logger.warning(f"{element_name} not interactable, trying JavaScript click")
            try:
                assert self.driver is not None
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
            assert self.driver is not None
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
            assert self.driver is not None
            wait_time = timeout or self.timeout
            WebDriverWait(self.driver, wait_time).until(
                lambda driver: driver.execute_script("return document.readyState") == "complete"
            )
            logger.debug("Page load completed")
            return True
            
        except TimeoutException:
            logger.warning("Page load timeout")
            return False
    
    def screenshot(self, filename: Optional[str] = None) -> str:
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
            assert self.driver is not None
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

    # --- Session health helpers ---
    def is_session_valid(self) -> bool:
        """Check if current WebDriver session is alive."""
        try:
            if not self.driver:
                return False
            # A lightweight command to test session
            _ = self.driver.current_url  # type: ignore[unused-ignore]
            return True
        except InvalidSessionIdException:
            return False
        except WebDriverException:
            return False
        except Exception:
            return False

    def restart_driver(self) -> bool:
        """Restart WebDriver session (quit then setup)."""
        try:
            logger.warning("Restarting WebDriver due to invalid session or error...")
            self.quit_driver()
            ok = self.setup_driver()
            if ok:
                logger.info("WebDriver restarted successfully")
            return ok
        except Exception as e:
            logger.error(f"Failed to restart WebDriver: {e}")
            return False

    # --- Unexpected popup helpers ---
    def close_unexpected_popups(self, max_iframes: int = 5) -> int:
        """
        Try to close common unexpected modals/popups/overlays including alerts.

        Returns: number of popups likely handled
        """
        handled = 0
        start = time.time()
        budget_sec = 2.5  # keep this quick to avoid blocking main flow
        driver = self.driver
        assert driver is not None

        # 1) Alerts: quick check
        try:
            if self.handle_alert(accept=True):
                handled += 1
        except Exception:
            pass

        selectors: List[str] = [
            "[aria-label='close']",
            "[aria-label='Close']",
            "[data-testid*='close']",
            "button.close",
            "button[title*='閉じ']",
            "button[aria-label*='閉じ']",
            "[class*='close']",
            ".modal .close",
            ".popup .close",
            ".overlay .close",
            ".dialog .close",
            "//button[contains(normalize-space(),'閉じる')]",
            "//a[contains(normalize-space(),'閉じる')]",
            "//*[text()='×' or text()='✕']",
        ]

        def try_close_in_context_quick() -> int:
            c = 0
            for sel in selectors:
                if time.time() - start > budget_sec:
                    break
                try:
                    if sel.startswith("//"):
                        elems = driver.find_elements(By.XPATH, sel)
                    else:
                        elems = driver.find_elements(By.CSS_SELECTOR, sel)
                    for e in elems:
                        if time.time() - start > budget_sec:
                            break
                        try:
                            if e.is_displayed() and e.is_enabled():
                                e.click()
                                c += 1
                        except Exception:
                            continue
                except Exception:
                    continue
            # ESC as a generic dismiss (non-blocking)
            try:
                ActionChains(driver).send_keys(Keys.ESCAPE).perform()
            except Exception:
                pass
            return c

        # Default content quick scan
        try:
            handled += try_close_in_context_quick()
        except Exception:
            pass

        # Limited iframe scan (quick)
        try:
            if time.time() - start < budget_sec:
                frames = driver.find_elements(By.CSS_SELECTOR, "iframe")[:max_iframes]
                for frame in frames:
                    if time.time() - start > budget_sec:
                        break
                    try:
                        driver.switch_to.frame(frame)
                        handled += try_close_in_context_quick()
                    except Exception:
                        continue
                    finally:
                        try:
                            driver.switch_to.default_content()
                        except Exception:
                            pass
        except Exception:
            pass

        if handled:
            logger.info(f"Unexpected popups handled quickly: {handled}")
        else:
            logger.debug("No unexpected popups found (quick scan)")
        return handled
    
    def __enter__(self):
        """Context manager entry"""
        self.setup_driver()
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        """Context manager exit"""
        self.quit_driver()
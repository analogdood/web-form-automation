"""
Form Filler for Web Form Automation System
"""

import logging
from selenium.webdriver.common.by import By
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import (
    TimeoutException, 
    NoSuchElementException,
    ElementNotInteractableException,
    ElementClickInterceptedException,
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
        Submit the voting form (add to cart)
        
        Returns:
            bool: True if successful, False otherwise
        """
        try:
            logger.info("Attempting to submit form (add to cart)")
            
            # Pre-clean: quickly dismiss popups/overlays that may block the cart button
            try:
                handled = self._dismiss_popups_and_overlays_quick()
                if handled:
                    logger.info(f"Pre-clean dismissed {handled} popup/overlay elements")
            except Exception as e:
                logger.debug(f"Pre-clean failed: {e}")

            # Enhanced scrolling to ensure cart button is visible
            try:
                logger.info("🔄 Enhanced scrolling to find cart button...")
                
                # Get initial page height
                initial_height = self.driver.execute_script("return document.body.scrollHeight")
                logger.info(f"Initial page height: {initial_height}px")
                
                # Scroll to very bottom
                self.driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
                time.sleep(2)
                
                # Scroll down in multiple steps to load dynamic content
                for step in range(5):
                    current_height = self.driver.execute_script("return document.body.scrollHeight")
                    scroll_position = self.driver.execute_script("return window.pageYOffset")
                    logger.info(f"Step {step+1}: Page height={current_height}px, Scroll position={scroll_position}px")
                    
                    # Scroll down a bit more
                    self.driver.execute_script(f"window.scrollTo(0, {current_height + 100});")
                    time.sleep(0.5)
                    
                    # Check if new content loaded
                    new_height = self.driver.execute_script("return document.body.scrollHeight")
                    if new_height > current_height:
                        logger.info(f"New content loaded, height increased to {new_height}px")
                
                # Final scroll to absolute bottom
                final_height = self.driver.execute_script("return document.body.scrollHeight")
                self.driver.execute_script(f"window.scrollTo(0, {final_height});")
                time.sleep(2)
                
                # Also try scrolling the document element (sometimes needed)
                self.driver.execute_script("document.documentElement.scrollTop = document.documentElement.scrollHeight;")
                time.sleep(1)
                
                final_scroll_position = self.driver.execute_script("return window.pageYOffset")
                logger.info(f"✅ Final scroll position: {final_scroll_position}px of {final_height}px")
                
            except Exception as e:
                logger.warning(f"Enhanced scrolling failed: {e}")
                # Fallback to simple scroll
                try:
                    self.driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
                    time.sleep(1)
                    logger.info("Fallback scroll completed")
                except:
                    pass
            
            # Debug: Find all potential clickable elements including links and divs
            all_clickables = []
            
            # Try different selectors to find all clickable elements
            selectors_to_try = [
                "button, input[type='submit'], input[type='button']",
                "a[href], div[onclick], span[onclick]",
                "span, div, a",  # Include all spans and divs
                "*[onclick]",
                "input[type='image']",
                ".btn, .button, .cart, .add",
                ".kounyu_cart_multiline_base",  # Specific cart button class
                "*[class*='kounyu']",
                "*[class*='cart']"
            ]
            
            for selector in selectors_to_try:
                try:
                    elements = self.driver.find_elements(By.CSS_SELECTOR, selector)
                    all_clickables.extend(elements)
                    # Only log if we found significant elements to reduce spam
                    if len(elements) > 10:
                        logger.debug(f"Found {len(elements)} elements with selector: {selector}")
                except Exception as e:
                    logger.debug(f"Selector {selector} failed: {e}")
            
            # Remove duplicates
            unique_clickables = []
            seen_elements = set()
            for element in all_clickables:
                try:
                    element_id = id(element)
                    if element_id not in seen_elements:
                        unique_clickables.append(element)
                        seen_elements.add(element_id)
                except:
                    pass
            
            logger.info(f"🔍 Found {len(unique_clickables)} clickable elements, filtering for cart buttons...")

            # Extra pre-check: run one more quick popup/overlay dismissal before analyzing buttons
            try:
                handled2 = self._dismiss_popups_and_overlays_quick()
                if handled2:
                    logger.info(f"Pre-click cleanup dismissed {handled2} popup/overlay elements")
            except Exception as e:
                logger.debug(f"Pre-click cleanup failed: {e}")
            
            cart_button_candidates = []
            # Only analyze a reasonable number of elements to reduce log spam
            elements_to_analyze = min(len(unique_clickables), 100)  # Limit to 100 elements max
            
            # Negative texts we must avoid (view/confirm cart)
            negative_cart_texts = [
                '購入カートを確認', 'カートを確認', 'カート確認', '確認', '確認する', 'view', 'チェック', '確認へ'
            ]

            for i, btn in enumerate(unique_clickables[:elements_to_analyze]):
                try:
                    btn_text = btn.get_attribute('value') or btn.text or 'no-text'
                    btn_onclick = btn.get_attribute('onclick') or 'no-onclick'
                    btn_class = btn.get_attribute('class') or 'no-class'
                    btn_id = btn.get_attribute('id') or 'no-id'
                    btn_name = btn.get_attribute('name') or 'no-name'
                    
                    # Check if this looks like a cart button (avoid header cart links)
                    is_cart_button = (
                        ('追加' in btn_text or 'カート' in btn_text or 
                         '購入' in btn_text or '申込' in btn_text or
                         '購入カートに追加' in btn_text or
                         'kounyu_cart' in btn_class.lower() or
                         'cart' in btn_onclick.lower() or 'add' in btn_onclick.lower() or
                         'buy' in btn_onclick.lower() or 'purchase' in btn_onclick.lower() or
                         'cart' in btn_class.lower() or 'add' in btn_class.lower() or
                         'buy' in btn_class.lower() or 'purchase' in btn_class.lower() or
                         'cart' in btn_id.lower() or 'add' in btn_id.lower() or
                         'buy' in btn_id.lower() or 'purchase' in btn_id.lower() or
                         'cart' in btn_name.lower() or 'add' in btn_name.lower() or
                         'kounyu' in btn_class.lower()) and
                        # Exclude header navigation cart buttons
                        not ('header' in btn_class.lower() or 'nav' in btn_class.lower() or
                             'l-header' in btn_class.lower() or 'main-nav' in btn_class.lower())
                    )
                    # Exclude confirm/view-cart variants by text
                    if is_cart_button and any(neg in btn_text for neg in negative_cart_texts):
                        is_cart_button = False
                    
                    # Only log cart button candidates to reduce log spam
                    if is_cart_button:
                        btn_visible = btn.is_displayed()
                        btn_enabled = btn.is_enabled()
                        cart_button_candidates.append((i, btn, btn_text))
                        logger.info(f"  🎯 CART BUTTON {len(cart_button_candidates)}: '{btn_text}' (class: {btn_class}, visible: {btn_visible}, enabled: {btn_enabled})")
                        
                except Exception as e:
                    logger.debug(f"Error analyzing button {i}: {e}")
            
            logger.info(f"🎯 Found {len(cart_button_candidates)} cart button candidates")
            
            # Try to find cart button first using improved method
            cart_success = self._try_click_cart_button(cart_button_candidates)
            
            if cart_success:
                logger.info("Cart button clicked successfully")
                
                # Immediately check for alert before any other checks
                logger.info("Checking for immediate alert after cart button click...")
                try:
                    alert = self.driver.switch_to.alert
                    alert_text = alert.text
                    logger.info(f"✅ Found immediate alert: '{alert_text}'")
                    alert.accept()
                    logger.info("✅ Immediate alert accepted successfully")
                    time.sleep(2)
                    
                    # Check if new window opened
                    self._handle_new_window_after_cart_addition()
                    
                    # Check if we're redirected to confirmation page
                    current_url = self.driver.current_url
                    if "vote/confirm" in current_url or "index.html" in current_url:
                        logger.info("✅ Redirected to confirmation/result page after alert - cart addition successful")
                        return True
                    
                    logger.info("✅ Alert handled, form submission successful")
                    return True
                    
                except Exception as e:
                    logger.debug(f"No immediate alert found: {e}")
                    
                # Wait a moment and check if anything happened
                time.sleep(2)
                
                # Check for form validation errors and detailed status (but handle alerts first)
                try:
                    if not self._check_form_status_after_click():
                        logger.warning("Form validation or other issues detected")
                        # Try to get more information about why the form submission failed
                        self._diagnose_form_submission_failure()
                        return False
                except Exception as status_error:
                    # If status check fails due to alert, try to handle alert
                    if "unexpected alert open" in str(status_error):
                        logger.info("Alert detected during status check - handling it now")
                        try:
                            alert = self.driver.switch_to.alert
                            alert_text = alert.text
                            logger.info(f"✅ Found alert during status check: '{alert_text}'")
                            alert.accept()
                            logger.info("✅ Alert accepted during status check")
                            return True
                        except:
                            pass
                    return False
                
                # Handle confirmation dialog
                if self._handle_confirmation_dialog():
                    logger.info("Form submitted successfully with cart button")
                    
                    # Check if we're redirected to confirmation page
                    current_url = self.driver.current_url
                    if "vote/confirm" in current_url or "index.html" in current_url:
                        logger.info("✅ Redirected to confirmation/result page - cart addition successful")
                        # Handle navigation from confirmation page
                        if self._handle_cart_page_navigation():
                            return True
                        else:
                            logger.warning("Failed to navigate back from confirmation page")
                            return False
                    
                    # Check if we're on cart page and need to go back
                    if self._handle_cart_page_navigation():
                        return True
                    else:
                        logger.warning("Failed to navigate back from cart page")
                        return False
                else:
                    logger.warning("Cart button clicked but confirmation dialog failed")
                    return False
            
            # Fallback to regular submit button
            logger.info("Cart button not found, trying regular submit button")
            # Clean one more time before trying submit
            try:
                self._dismiss_popups_and_overlays_quick()
            except Exception:
                pass
            success = self.driver_manager.click_element_safe(
                Config.SELECTORS['submit_button'], 
                "submit button"
            )
            
            if success:
                logger.info("Form submitted successfully with regular submit button")
                # Handle confirmation dialog
                self._handle_confirmation_dialog()
                time.sleep(2)
                return True
            else:
                logger.error("Failed to submit form")
                return False
                
        except Exception as e:
            logger.error(f"Error submitting form: {e}")
            return False

    def _dismiss_popups_and_overlays_quick(self) -> int:
        """Quickly dismiss common popups and hide overlays that may block clicks.

        Returns:
            int: Approximate number of elements handled/hidden.
        """
        handled = 0
        try:
            # Use driver manager quick popup closer (alerts, close buttons, limited iframes)
            handled += self.driver_manager.close_unexpected_popups(max_iframes=3)
        except Exception:
            pass

        # Hide overlay/modals with JS (non-destructive styling overrides)
        try:
            js = """
            (function(){
                var selectors = [
                    '.modal-backdrop', '.modal', '.popup', '.overlay',
                    '[aria-modal="true"]', '[role="dialog"]',
                    '[class*="modal"]', '[class*="popup"]', '[class*="overlay"]'
                ];
                var count = 0;
                var nodes = document.querySelectorAll(selectors.join(','));
                for (var i=0;i<nodes.length;i++){
                    var el = nodes[i];
                    try{
                        el.style.setProperty('display','none','important');
                        el.style.setProperty('visibility','hidden','important');
                        el.style.setProperty('pointer-events','none','important');
                        el.style.setProperty('opacity','0','important');
                        count++;
                    }catch(e){}
                }
                try{ document.body.style.setProperty('overflow','auto','important'); }catch(e){}
                return count;
            })();
            """
            hidden = self.driver.execute_script(js)
            if hidden:
                handled += int(hidden) if isinstance(hidden, (int, float)) else 0
        except Exception:
            pass

        return handled
    
    def _handle_confirmation_dialog(self) -> bool:
        """
        Handle confirmation dialog that appears after clicking cart button
        
        Returns:
            bool: True if dialog handled successfully, False otherwise
        """
        try:
            logger.info("🔍 Checking for confirmation dialog after cart button click...")
            
            # Wait longer for dialog to appear
            time.sleep(3)
            
            # Method 1: More aggressive JavaScript alert handling
            logger.info("Method 1: Aggressive JavaScript alert handling...")
            for attempt in range(10):  # Try 10 times over 5 seconds
                try:
                    alert = self.driver.switch_to.alert
                    alert_text = alert.text
                    logger.info(f"✅ Found JavaScript alert (attempt {attempt + 1}): '{alert_text}'")
                    alert.accept()  # Click OK
                    logger.info("✅ JavaScript alert accepted (OK clicked)")
                    time.sleep(2)
                    return True
                except Exception as e:
                    if attempt < 9:  # Don't log error on last attempt
                        logger.debug(f"Attempt {attempt + 1}: No alert yet: {e}")
                        time.sleep(0.5)
                    continue
            
            logger.info("No JavaScript alert found after 10 attempts")
            
            # Method 2: Immediate alert check (sometimes alerts appear instantly)
            logger.info("Method 2: Immediate alert check...")
            try:
                alert = self.driver.switch_to.alert
                alert_text = alert.text
                logger.info(f"✅ Found immediate alert: '{alert_text}'")
                alert.accept()
                logger.info("✅ Immediate alert accepted")
                time.sleep(2)
                return True
            except Exception as e:
                logger.debug(f"No immediate alert: {e}")
            
            # Method 3: Enhanced DOM dialog search with immediate action
            logger.info("Method 3: Enhanced DOM dialog search...")
            
            # Check current page state
            current_url = self.driver.current_url
            page_title = self.driver.title
            logger.info(f"Current URL: {current_url}")
            logger.info(f"Page title: {page_title}")
            
            # Check if we already redirected to result page
            if "vote/confirm" in current_url or "index.html" in current_url:
                logger.info("✅ Already redirected to confirmation/result page - dialog was likely auto-handled")
                return True
            
            # Try to find and click confirmation buttons aggressively
            confirmation_selectors = [
                "//button[contains(text(), 'OK')]",
                "//button[contains(text(), 'はい')]", 
                "//button[contains(text(), '確認')]",
                "//button[contains(text(), 'ok')]",
                "//input[@value='OK']",
                "//input[@value='はい']", 
                "//input[@value='確認']",
                "//button[@value='OK']",
                "//button[@value='はい']",
                "//button[@value='確認']",
                "button[onclick*='ok']",
                "button[onclick*='OK']",
                "button[onclick*='confirm']",
                ".modal button",
                ".dialog button", 
                ".popup button",
                "[role='dialog'] button",
                ".confirm-button",
                ".ok-button",
                "*[data-action='confirm']",
                "*[data-action='ok']"
            ]
            
            # Avoid delete/cancel buttons
            avoid_keywords = ['削除', 'delete', '取消', 'cancel', '×', 'close', '閉じる', 'キャンセル']
            
            # Try each selector with multiple attempts
            for selector in confirmation_selectors:
                for attempt in range(3):  # 3 attempts per selector
                    try:
                        if selector.startswith("//"):
                            elements = self.driver.find_elements(By.XPATH, selector)
                        else:
                            elements = self.driver.find_elements(By.CSS_SELECTOR, selector)
                        
                        for element in elements:
                            if element.is_displayed() and element.is_enabled():
                                element_text = element.text or element.get_attribute('value') or 'no-text'
                                
                                # Skip delete/cancel buttons
                                if any(keyword in element_text.lower() for keyword in avoid_keywords):
                                    logger.debug(f"Skipping avoid button: '{element_text}'")
                                    continue
                                
                                # Click any visible confirmation-like button
                                logger.info(f"Found potential OK button: '{element_text}' (selector: {selector})")
                                try:
                                    element.click()
                                    logger.info(f"✅ Clicked confirmation button: '{element_text}'")
                                    time.sleep(3)  # Wait longer after click
                                    
                                    # Check if URL changed (redirect to result page)
                                    new_url = self.driver.current_url
                                    if new_url != current_url:
                                        logger.info(f"✅ URL changed after button click: {new_url}")
                                        return True
                                    
                                    return True
                                except Exception as click_error:
                                    logger.debug(f"Failed to click button '{element_text}': {click_error}")
                                    continue
                                    
                    except Exception as e:
                        logger.debug(f"Selector {selector} attempt {attempt + 1} failed: {e}")
                        if attempt < 2:  # Wait before retry
                            time.sleep(0.5)
                        continue
            
            # Method 4: Try pressing Enter key (sometimes works for dialogs)
            logger.info("Method 4: Trying Enter key...")
            try:
                from selenium.webdriver.common.keys import Keys
                # Try Enter on body
                self.driver.find_element(By.TAG_NAME, 'body').send_keys(Keys.ENTER)
                logger.info("✅ Pressed Enter key on body")
                time.sleep(2)
                
                # Check if URL changed after Enter
                new_url = self.driver.current_url
                if new_url != current_url:
                    logger.info(f"✅ URL changed after Enter key: {new_url}")
                    return True
                
                # Try Space key as well (sometimes confirms dialogs)
                self.driver.find_element(By.TAG_NAME, 'body').send_keys(Keys.SPACE)
                logger.info("✅ Pressed Space key")
                time.sleep(2)
                
                return True
            except Exception as e:
                logger.info(f"Key press failed: {e}")
            
            # Final check - see if we're on a different page now
            final_url = self.driver.current_url
            if final_url != current_url:
                logger.info(f"✅ URL changed during dialog handling: {final_url}")
                return True
            
            logger.warning("⚠️ No confirmation dialog found or could not handle it")
            return True  # Continue anyway as dialog might have been auto-handled
            
        except Exception as e:
            logger.error(f"❌ Error handling confirmation dialog: {e}")
            return False
    
    def _handle_new_window_after_cart_addition(self):
        """
        Handle new window that might open after cart addition
        """
        try:
            logger.info("🔍 Checking for new windows after cart addition...")
            
            # Get all window handles
            all_windows = self.driver.window_handles
            logger.info(f"Found {len(all_windows)} window(s)")
            
            if len(all_windows) > 1:
                logger.info("✅ New window detected - handling new window")
                
                # Switch to the new window (usually the last one)
                new_window = all_windows[-1]
                original_window = all_windows[0]
                
                logger.info(f"Switching to new window: {new_window}")
                self.driver.switch_to.window(new_window)
                
                # Wait for new window to load
                time.sleep(3)
                
                # Get new window URL and title
                new_url = self.driver.current_url
                new_title = self.driver.title
                logger.info(f"New window URL: {new_url}")
                logger.info(f"New window title: {new_title}")
                
                # Check if it's a confirmation/result page
                if any(keyword in new_url.lower() for keyword in ['confirm', 'result', 'cart', 'complete', 'success']):
                    logger.info("✅ New window appears to be confirmation/result page")
                
                # Close the new window and return to original
                logger.info("Closing new window and returning to original voting page...")
                self.driver.close()
                self.driver.switch_to.window(original_window)
                
                # Wait a moment for focus to return
                time.sleep(2)
                
                logger.info("✅ Returned to original voting page window")
                
                # Check if we're still on voting page
                current_url = self.driver.current_url
                if "PGSPSL00001MoveSingleVoteSheet.form" in current_url:
                    logger.info("✅ Successfully back on voting page - ready for next batch")
                else:
                    logger.warning(f"Not on voting page: {current_url}")
                    
            else:
                logger.info("No new windows opened")
                
        except Exception as e:
            logger.error(f"Error handling new window: {e}")
            # Try to return to original window if something went wrong
            try:
                if len(self.driver.window_handles) > 0:
                    self.driver.switch_to.window(self.driver.window_handles[0])
            except:
                pass
    
    def _check_browser_alive(self) -> bool:
        """
        Check if browser is still alive and responsive
        
        Returns:
            bool: True if browser is responsive, False otherwise
        """
        try:
            # Try to get current URL - this will fail if browser crashed
            _ = self.driver.current_url
            # Try to execute a simple JavaScript command
            self.driver.execute_script("return document.readyState;")
            return True
        except Exception as e:
            logger.warning(f"Browser responsiveness check failed: {e}")
            return False
    
    def _handle_cart_page_navigation(self) -> bool:
        """
        Handle navigation after cart addition (return to voting page or stay for next batch)
        
        Returns:
            bool: True if navigation handled successfully, False otherwise
        """
        import time
        start_time = time.time()
        max_navigation_time = 30  # 30 seconds max for navigation
        
        try:
            # Add browser stability check
            if not self._check_browser_alive():
                logger.error("Browser is not responsive - cannot handle cart page navigation")
                return False
                
            current_url = self.driver.current_url
            logger.info(f"Current URL after cart addition: {current_url}")
            
            # Check if we're on cart page or confirmation page
            try:
                page_source = self.driver.page_source
            except Exception as e:
                logger.warning(f"Failed to get page source: {e}")
                page_source = ""
                
            if ("cart" in current_url.lower() or "カート" in page_source or "SPSL006" in page_source or 
                "confirm" in current_url.lower() or "index.html" in current_url):
                logger.info("✅ Detected cart page - product added successfully")
                
                # Try multiple methods to return to voting page with timeout
                logger.info("🔄 Attempting to return to voting page for next batch...")
                
                # Method 1: Look for specific links to voting page (including the new button)
                try:
                    # Set shorter timeout for link searches to avoid hanging
                    from selenium.webdriver.support.wait import WebDriverWait
                    from selenium.webdriver.support import expected_conditions as EC
                    
                    # Prioritize specific "totoの投票を追加する" buttons first to avoid wrong redirects
                    voting_page_links = [
                        "//*[contains(@class, 'c-clubtoto-btn-base__text') and contains(text(), 'totoの投票を追加する')]",
                        "//button[contains(text(), 'totoの投票を追加する')]",
                        "//a[contains(text(), 'totoの投票を追加する')]",
                        "//p[contains(text(), 'totoの投票を追加する')]",
                        "//img[@id='select_single' or @name='select_single']",  # Single button for next batch
                        "//a[contains(@href, 'PGSPSL00001MoveSingleVoteSheet')]",
                        "//a[contains(text(), '続けて購入')]",
                        "//a[contains(text(), '投票を追加')]",
                        "//a[contains(text(), '投票')]",
                        "//a[contains(text(), '予想')]",
                        # Removed generic "toto" and breadcrumb links to avoid wrong redirects
                    ]
                    
                    for link_xpath in voting_page_links:
                        try:
                            # Check timeout
                            if time.time() - start_time > max_navigation_time:
                                logger.warning(f"Navigation timeout exceeded ({max_navigation_time}s), aborting")
                                return False
                            
                            # Check browser health before each search
                            if not self._check_browser_alive():
                                logger.warning("Browser became unresponsive, skipping navigation")
                                return False
                            
                            # Use timeout for element search
                            wait = WebDriverWait(self.driver, 3)  # 3 second timeout per element
                            if link_xpath.startswith("//"):
                                elements = self.driver.find_elements(By.XPATH, link_xpath)
                            else:
                                elements = self.driver.find_elements(By.CSS_SELECTOR, link_xpath)
                                
                            for element in elements:
                                if element.is_displayed() and element.is_enabled():
                                    link_text = element.text or element.get_attribute('href') or 'no-text'
                                    link_href = element.get_attribute('href') or ''
                                    
                                    # Skip links that lead to confirmation/result pages
                                    if any(bad_url in link_href.lower() for bad_url in ['confirm', 'result', 'vote/confirm']):
                                        logger.debug(f"Skipping link that leads to confirmation page: {link_href}")
                                        continue
                                    
                                    logger.info(f"Found potential return link: '{link_text}' (href: {link_href}) with xpath: {link_xpath}")
                                    
                                    # Special handling for specific buttons
                                    if 'totoの投票を追加する' in link_text:
                                        logger.info("🎯 Found 'totoの投票を追加する' button - clicking to return to voting page")
                                    elif 'select_single' in str(element.get_attribute('id')) or 'select_single' in str(element.get_attribute('name')):
                                        logger.info("🎯 Found 'シングル' button - clicking to start next batch input loop")
                                    
                                    element.click()
                                    time.sleep(3)  # Wait longer for page transition
                                    
                                    # Check if we're back on voting page
                                    new_url = self.driver.current_url
                                    if "PGSPSL00001MoveSingleVoteSheet.form" in new_url:
                                        logger.info("✅ Successfully returned to voting page via link")
                                        return True
                                    elif "vote/confirm" in new_url:
                                        logger.warning(f"⚠️ Link led to confirmation page: {new_url} - this should be avoided")
                                        # Don't return True, continue to next link
                                        continue
                                    else:
                                        logger.info(f"Link led to: {new_url}, continuing search...")
                                        
                        except Exception as e:
                            logger.debug(f"Link search {link_xpath} failed: {e}")
                            continue
                            
                except Exception as e:
                    logger.warning(f"Link search failed: {e}")
                
                # Method 2: Navigate back using browser back button
                logger.info("🔄 Trying browser back navigation...")
                try:
                    self.driver.back()
                    time.sleep(3)
                    
                    # Verify we're back on voting page
                    new_url = self.driver.current_url
                    if "PGSPSL00001MoveSingleVoteSheet.form" in new_url:
                        logger.info("✅ Successfully returned to voting page via back button")
                        return True
                    else:
                        logger.warning(f"Back navigation led to unexpected page: {new_url}")
                        
                except Exception as e:
                    logger.warning(f"Back navigation failed: {e}")
                
                # Method 3: Direct URL navigation (if we know the URL pattern)
                logger.info("🔄 Trying direct URL navigation...")
                try:
                    # Try to construct the voting page URL based on current URL
                    if "store.toto-dream.com" in current_url:
                        voting_url = "https://store.toto-dream.com/dcs/subos/screen/ps01/spsl000/PGSPSL00001MoveSingleVoteSheet.form"
                        logger.info(f"Attempting direct navigation to: {voting_url}")
                        self.driver.get(voting_url)
                        time.sleep(3)
                        
                        new_url = self.driver.current_url
                        if "PGSPSL00001MoveSingleVoteSheet.form" in new_url:
                            logger.info("✅ Successfully returned to voting page via direct URL")
                            return True
                        else:
                            logger.warning(f"Direct navigation led to: {new_url}")
                            
                except Exception as e:
                    logger.warning(f"Direct navigation failed: {e}")
                
                # Method 4: Try fallback navigation method
                return self._navigate_to_voting_page()
            
            # If not on cart page, we might still be on voting page
            elif "PGSPSL00001MoveSingleVoteSheet.form" in current_url:
                logger.info("✅ Still on voting page - ready for next batch")
                return True
            
            else:
                logger.warning(f"Unexpected page after cart addition: {current_url}")
                return self._navigate_to_voting_page()
            
        except Exception as e:
            logger.error(f"❌ Error handling cart page navigation: {e}")
            
            # Check if browser crashed
            if not self._check_browser_alive():
                logger.error("Browser appears to have crashed during navigation")
                return False
            
            # Try one more time with direct navigation
            try:
                logger.info("Attempting emergency navigation to voting page...")
                voting_url = "https://www.toto-dream.com/toto/index.html"
                self.driver.get(voting_url)
                time.sleep(3)
                
                current_url = self.driver.current_url
                if "PGSPSL00001MoveSingleVoteSheet.form" in current_url or "toto" in current_url:
                    logger.info("✅ Emergency navigation successful")
                    return True
                else:
                    logger.warning(f"Emergency navigation led to: {current_url}")
                    return False
            except Exception as emergency_error:
                logger.error(f"Emergency navigation also failed: {emergency_error}")
                return False
    
    def _navigate_to_voting_page(self) -> bool:
        """
        Navigate to voting page (fallback method)
        
        Returns:
            bool: True if successful, False otherwise
        """
        try:
            logger.info("🔄 Attempting to navigate to voting page...")
            
            # Try to find link to voting page
            voting_links = [
                "//a[contains(@href, 'PGSPSL00001MoveSingleVoteSheet')]",
                "//a[contains(text(), '投票')]",
                "//a[contains(text(), '予想')]",
                "//button[contains(text(), '投票')]",
                "//button[contains(text(), '予想')]"
            ]
            
            for link_xpath in voting_links:
                try:
                    elements = self.driver.find_elements(By.XPATH, link_xpath)
                    if elements:
                        element = elements[0]
                        if element.is_displayed() and element.is_enabled():
                            element.click()
                            logger.info(f"✅ Clicked voting page link: {link_xpath}")
                            time.sleep(2)
                            return True
                except Exception as e:
                    logger.debug(f"Failed to click link {link_xpath}: {e}")
                    continue
            
            logger.warning("⚠️ Could not find voting page link - manual navigation may be required")
            return False
            
        except Exception as e:
            logger.error(f"❌ Error navigating to voting page: {e}")
            return False
    
    def _try_click_cart_button(self, cart_button_candidates) -> bool:
        """
        Try multiple methods to click cart button
        
        Args:
            cart_button_candidates: List of (index, element, text) tuples
            
        Returns:
            bool: True if cart button clicked successfully, False otherwise
        """
        try:
            # Quick cleanup before attempts
            try:
                self._dismiss_popups_and_overlays_quick()
            except Exception:
                pass

            # Sort candidates to prioritize true '追加' buttons and known classes, de-prioritize anything with '確認'
            def score_candidate(btn, text: str) -> int:
                t = text or ''
                cls = (btn.get_attribute('class') or '').lower()
                onclick = (btn.get_attribute('onclick') or '').lower()
                score = 0
                if '購入カートに追加' in t:
                    score += 100
                if 'カートに追加' in t:
                    score += 80
                if '追加' in t:
                    score += 60
                if 'kounyu_cart' in cls or 'kounyu_cart_multiline_base' in cls:
                    score += 50
                if 'cart' in onclick or 'add' in onclick:
                    score += 20
                # Strongly penalize confirm/view variants
                for neg in ['購入カートを確認','カートを確認','カート確認','確認','確認する','view','チェック','確認へ']:
                    if neg in t:
                        score -= 1000
                return score

            sorted_candidates = sorted(cart_button_candidates, key=lambda tup: score_candidate(tup[1], tup[2]), reverse=True)

            # Method 1: Try direct candidates from analysis (sorted by priority)
            logger.info("🎯 Method 1: Trying direct cart button candidates...")
            for i, (index, btn, text) in enumerate(sorted_candidates):
                try:
                    if btn.is_displayed() and btn.is_enabled():
                        logger.info(f"Attempting to click candidate {i}: '{text}'")
                        # Ensure in view and unobscured
                        try:
                            self.driver.execute_script("arguments[0].scrollIntoView({behavior:'instant',block:'center'});", btn)
                        except Exception:
                            pass
                        # One more cleanup right before click
                        try:
                            self._dismiss_popups_and_overlays_quick()
                        except Exception:
                            pass
                        try:
                            # Prefer waiting for clickable to avoid intercepted clicks
                            if self.wait:
                                self.wait.until(EC.element_to_be_clickable(btn))
                            btn.click()
                        except (ElementClickInterceptedException, ElementNotInteractableException) as ce:
                            logger.debug(f"Direct click intercepted for candidate {i}: {ce} — trying JS click")
                            self.driver.execute_script("arguments[0].click();", btn)
                        logger.info(f"✅ Successfully clicked cart button candidate {i}: '{text}'")
                        time.sleep(1)
                        return True
                except Exception as e:
                    logger.warning(f"Failed to click candidate {i}: {e}")
                    continue
            
            # Method 2: Try using WebDriverManager's click_element_safe
            logger.info("🎯 Method 2: Trying with WebDriverManager...")
            cart_success = self.driver_manager.click_element_safe(
                Config.SELECTORS['cart_button'], 
                "cart button"
            )
            if cart_success:
                logger.info("✅ Cart button clicked via WebDriverManager")
                return True
            
            # Method 3: Try XPath-based search for cart buttons
            logger.info("🎯 Method 3: Trying XPath-based search...")
            cart_xpaths = [
                "//span[contains(@class, 'kounyu_cart_multiline_base')]",
                "//span[contains(text(), '購入カートに追加')]",
                "//*[contains(@class, 'kounyu_cart')]",
                "//div[contains(text(), '購入カートに追加')]",
                "//a[contains(text(), '購入カートに追加')]",
                "//input[contains(@value, 'カートに追加')]",
                "//input[contains(@value, '購入カートに追加')]",
                "//input[contains(@value, '追加')]",
                "//button[contains(text(), 'カートに追加')]",
                "//button[contains(text(), '購入カートに追加')]",
                "//button[contains(text(), '追加')]",
                "//span[contains(text(), 'カート')]",
                "//span[contains(text(), '追加')]",
                "//input[@type='submit' and contains(@value, 'カート')]",
                "//input[@type='button' and contains(@value, 'カート')]",
                "//button[@type='submit' and contains(text(), 'カート')]",
                "//button[@type='button' and contains(text(), 'カート')]",
                "//*[contains(@onclick, 'cart') or contains(@onclick, 'Cart')]",
                "//*[contains(@onclick, 'add') or contains(@onclick, 'Add')]"
            ]
            
            for xpath in cart_xpaths:
                try:
                    try:
                        self._dismiss_popups_and_overlays_quick()
                    except Exception:
                        pass
                    elements = self.driver.find_elements(By.XPATH, xpath)
                    for element in elements:
                        if element.is_displayed() and element.is_enabled():
                            element_text = element.get_attribute('value') or element.text or 'no-text'
                            # Skip confirm/view-cart variants
                            if any(neg in element_text for neg in ['購入カートを確認','カートを確認','カート確認','確認','確認する','view','チェック','確認へ']):
                                logger.debug(f"Skipping non-add cart button: '{element_text}'")
                                continue
                            logger.info(f"Trying XPath cart button: '{element_text}'")
                            try:
                                self.driver.execute_script("arguments[0].scrollIntoView({behavior:'instant',block:'center'});", element)
                            except Exception:
                                pass
                            element.click()
                            logger.info(f"✅ Successfully clicked XPath cart button: '{element_text}'")
                            time.sleep(1)
                            return True
                except Exception as e:
                    logger.debug(f"XPath {xpath} failed: {e}")
                    continue
            
            # Method 4: JavaScript click for stubborn buttons
            logger.info("🎯 Method 4: Trying JavaScript click...")
            try:
                # Try to find any element with cart-related attributes via JavaScript
                js_script = """
                var elements = document.querySelectorAll('*');
                for (var i = 0; i < elements.length; i++) {
                    var elem = elements[i];
                    var text = elem.value || elem.textContent || elem.innerText || '';
                    var onclick = elem.getAttribute('onclick') || '';
                    var className = elem.className || '';
                    var id = elem.id || '';
                    
                    if (text.includes('購入カートに追加') || 
                        className.includes('kounyu_cart_multiline_base') ||
                        className.includes('kounyu_cart') ||
                        text.includes('追加') || text.includes('カート') || 
                        onclick.toLowerCase().includes('cart') || onclick.toLowerCase().includes('add') ||
                        className.toLowerCase().includes('cart') || className.toLowerCase().includes('add') ||
                        id.toLowerCase().includes('cart') || id.toLowerCase().includes('add')) {
                        
                        console.log('Found cart element via JS:', text, 'class:', className);
                        try {
                            // Try multiple click methods
                            console.log('Attempting to click element:', text);
                            
                            // Method 1: Direct click
                            elem.click();
                            
                            // Method 2: Dispatch click event
                            var clickEvent = new MouseEvent('click', {
                                view: window,
                                bubbles: true,
                                cancelable: true
                            });
                            elem.dispatchEvent(clickEvent);
                            
                            // Method 3: If it has onclick, execute it
                            if (onclick) {
                                try {
                                    eval(onclick);
                                } catch (e2) {
                                    console.log('onclick eval failed:', e2);
                                }
                            }
                            
                            return 'clicked: ' + text + ' (class: ' + className + ')';
                        } catch (e) {
                            console.log('Click failed for element:', e);
                        }
                    }
                }
                return 'not found';
                """
                
                result = self.driver.execute_script(js_script)
                if result and result != 'not found':
                    logger.info(f"✅ JavaScript click successful: {result}")
                    time.sleep(1)
                    return True
                else:
                    logger.info("JavaScript method found no clickable cart buttons")
                    
            except Exception as e:
                logger.warning(f"JavaScript click method failed: {e}")
            
            logger.error("❌ All cart button click methods failed")
            return False
            
        except Exception as e:
            logger.error(f"❌ Error in _try_click_cart_button: {e}")
            return False
    
    def _check_form_status_after_click(self) -> bool:
        """
        Check form status after cart button click to identify issues
        
        Returns:
            bool: True if form seems OK, False if issues detected
        """
        try:
            logger.info("🔍 Checking form status after cart button click...")
            
            # First check if there's an alert and handle it
            try:
                alert = self.driver.switch_to.alert
                alert_text = alert.text
                logger.info(f"✅ Found alert during status check: '{alert_text}'")
                alert.accept()
                logger.info("✅ Alert accepted during status check")
                
                # Check if new window opened after alert
                self._handle_new_window_after_cart_addition()
                
                return True
            except:
                # No alert, continue with normal checks
                pass
            
            # Get current URL
            current_url = self.driver.current_url
            logger.info(f"Current URL: {current_url}")
            
            # Check for JavaScript errors in console
            try:
                js_errors = self.driver.execute_script("""
                    var errors = [];
                    if (window.console && window.console.error) {
                        // This is a simplified check - in reality we'd need to capture console messages
                        return 'Console check completed';
                    }
                    return 'No console access';
                """)
                logger.info(f"JavaScript console check: {js_errors}")
            except Exception as e:
                logger.debug(f"Console check failed: {e}")
            
            # Check for form validation messages
            try:
                error_selectors = [
                    ".error, .error-message, .validation-error",
                    "[class*='error']",
                    "[id*='error']",
                    "span[style*='color: red'], div[style*='color: red']",
                    ".alert, .warning, .notice",
                    "*[class*='alert']"
                ]
                
                for selector in error_selectors:
                    try:
                        error_elements = self.driver.find_elements(By.CSS_SELECTOR, selector)
                        for element in error_elements:
                            if element.is_displayed():
                                error_text = element.text.strip()
                                if error_text:
                                    logger.warning(f"❌ Found error message: '{error_text}' (selector: {selector})")
                                    return False
                    except Exception as e:
                        logger.debug(f"Error selector {selector} failed: {e}")
                        
            except Exception as e:
                logger.debug(f"Error message check failed: {e}")
            
            # Check if any alerts are present
            try:
                alert = self.driver.switch_to.alert
                alert_text = alert.text
                logger.info(f"Found alert after click: '{alert_text}'")
                alert.accept()  # Accept it immediately
                logger.info("✅ Alert accepted in status check")
                return True  # Alert is expected for cart addition
            except:
                logger.debug("No alert found")
            
            # Check if URL changed (might indicate redirect or success)
            if current_url != self.driver.current_url:
                new_url = self.driver.current_url
                logger.info(f"URL changed to: {new_url}")
                return True
            
            # Check if page content changed
            try:
                page_title = self.driver.title
                logger.info(f"Page title: {page_title}")
                
                # Look for success indicators
                success_indicators = [
                    "カート", "cart", "追加", "success", "complete"
                ]
                
                page_source_lower = self.driver.page_source.lower()
                for indicator in success_indicators:
                    if indicator in page_source_lower:
                        logger.info(f"Found success indicator: '{indicator}' in page")
                        return True
                        
            except Exception as e:
                logger.debug(f"Page content check failed: {e}")
            
            # Check for required fields that might be missing
            try:
                required_fields = self.driver.find_elements(By.CSS_SELECTOR, "input[required], select[required]")
                empty_required = []
                
                for field in required_fields:
                    if field.is_displayed():
                        field_value = field.get_attribute('value') or ''
                        field_name = field.get_attribute('name') or field.get_attribute('id') or 'unknown'
                        
                        if not field_value.strip():
                            empty_required.append(field_name)
                
                if empty_required:
                    logger.warning(f"❌ Found empty required fields: {empty_required}")
                    return False
                else:
                    logger.info("✅ All required fields appear to be filled")
                    
            except Exception as e:
                logger.debug(f"Required fields check failed: {e}")
            
            logger.info("✅ Form status check completed - no obvious issues detected")
            return True
            
        except Exception as e:
            logger.error(f"❌ Error checking form status: {e}")
            return True  # Don't fail the whole process for this check
    
    def _diagnose_form_submission_failure(self):
        """
        Diagnose why form submission might have failed
        """
        try:
            logger.info("🔍 Diagnosing form submission failure...")
            
            # Check if we're still on the same page
            current_url = self.driver.current_url
            logger.info(f"Still on URL: {current_url}")
            
            # Look for specific validation issues in toto forms
            try:
                # Check if all games have selections
                logger.info("Checking if all games have selections...")
                
                games_without_selection = []
                # Quick check for games without selections (only first 5 games to reduce log spam)
                for game_index in range(min(13, 5)):  # Check only first 5 games to reduce processing
                    game_has_selection = False
                    
                    # Check if any checkbox is selected for this game
                    for set_index in range(min(10, 3)):  # Check only first 3 sets to reduce processing
                        for value in [0, 1, 2]:
                            try:
                                checkbox_name = f"chkbox_{game_index}_{set_index}_{value}"
                                checkbox = self.driver.find_element(By.NAME, checkbox_name)
                                if checkbox.is_selected():
                                    game_has_selection = True
                                    break
                            except:
                                continue
                            
                            if game_has_selection:
                                break
                        
                        if game_has_selection:
                            break
                    
                    if not game_has_selection:
                        games_without_selection.append(game_index + 1)
                
                if games_without_selection:
                    logger.warning(f"❌ Some games may lack selections (sampled first 5 games): {games_without_selection}")
                else:
                    logger.info("✅ Sampled games appear to have selections")
                    
            except Exception as e:
                logger.debug(f"Game selection check failed: {e}")
            
            # Check for JavaScript errors or console messages
            try:
                js_result = self.driver.execute_script("""
                    // Check if checkBeforeSubmit function exists
                    if (typeof checkBeforeSubmit === 'function') {
                        console.log('checkBeforeSubmit function exists');
                        return 'checkBeforeSubmit exists';
                    } else {
                        console.log('checkBeforeSubmit function not found');
                        return 'checkBeforeSubmit not found';
                    }
                """)
                logger.info(f"JavaScript function check: {js_result}")
                
                # Try to manually call the validation function
                validation_result = self.driver.execute_script("""
                    try {
                        if (typeof checkBeforeSubmit === 'function') {
                            var result = checkBeforeSubmit('PGSPSL00001Form','addShoppingCartTotoSingle','ON','Add');
                            console.log('checkBeforeSubmit result:', result);
                            return 'validation result: ' + result;
                        }
                        return 'function not available';
                    } catch (e) {
                        console.log('Validation function error:', e);
                        return 'validation error: ' + e.message;
                    }
                """)
                logger.info(f"Manual validation result: {validation_result}")
                
            except Exception as e:
                logger.debug(f"JavaScript validation check failed: {e}")
            
            # Check form state
            try:
                form_info = self.driver.execute_script("""
                    var form = document.forms['PGSPSL00001Form'];
                    if (form) {
                        var inputs = form.querySelectorAll('input[type="checkbox"]:checked');
                        return 'Form found with ' + inputs.length + ' checked checkboxes';
                    } else {
                        return 'Form PGSPSL00001Form not found';
                    }
                """)
                logger.info(f"Form state: {form_info}")
                
            except Exception as e:
                logger.debug(f"Form state check failed: {e}")
                
        except Exception as e:
            logger.error(f"❌ Error in form submission diagnosis: {e}")
    
    def navigate_to_next_form(self) -> bool:
        """
        Navigate to the next form page or back to voting page for next batch
        
        Returns:
            bool: True if successful, False otherwise
        """
        try:
            logger.info("Navigating to next form or voting page for next batch")
            
            # First try the cart page navigation (for post-cart scenarios)
            if self._handle_cart_page_navigation():
                logger.info("Successfully navigated back to voting page via cart navigation")
                return True
            
            # If that fails, try the traditional next button approach
            success = self.driver_manager.click_element_safe(
                Config.SELECTORS['next_button'], 
                "next button"
            )
            
            if success:
                logger.info("Successfully navigated to next form via next button")
                # Wait for new page to load
                self.driver_manager.wait_for_page_load()
                return True
            else:
                logger.warning("Failed to find next button, trying emergency navigation...")
                # Try emergency navigation to voting page
                try:
                    voting_url = "https://www.toto-dream.com/toto/index.html"
                    self.driver.get(voting_url)
                    time.sleep(3)
                    
                    current_url = self.driver.current_url
                    if "PGSPSL00001MoveSingleVoteSheet.form" in current_url or "toto" in current_url:
                        logger.info("✅ Emergency navigation to voting page successful")
                        return True
                    else:
                        logger.warning(f"Emergency navigation led to: {current_url}")
                        return False
                except Exception as emergency_error:
                    logger.error(f"Emergency navigation failed: {emergency_error}")
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
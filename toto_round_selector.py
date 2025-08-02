"""
Toto Round Selection Module

This module handles the detection and selection of toto rounds (第xxxx回)
from the main toto page.
"""

import logging
import re
import time
from typing import List, Dict, Optional, Tuple
from selenium.webdriver.common.by import By
from selenium.webdriver.support.wait import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC

logger = logging.getLogger(__name__)

class TotoRoundSelector:
    """Class for detecting and selecting toto rounds"""
    
    def __init__(self, driver):
        self.driver = driver
        self.selected_round = None
        self.selected_round_id = None
        self.selected_round_url = None
    
    def navigate_to_start_page(self, start_url: str) -> bool:
        """
        Navigate to the initial toto page
        
        Args:
            start_url: The starting URL
            
        Returns:
            bool: True if navigation successful, False otherwise
        """
        try:
            logger.info(f"Navigating to start page: {start_url}")
            self.driver.get(start_url)
            time.sleep(3)  # Wait for page to load
            
            current_url = self.driver.current_url
            logger.info(f"Current URL after navigation: {current_url}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to navigate to start page: {e}")
            return False
    
    def detect_toto_rounds(self) -> List[Dict[str, str]]:
        """
        Detect all available toto rounds (第xxxx回) on the page
        
        Returns:
            List[Dict]: List of rounds with their info
                       [{'round_number': '1558', 'text': '第1558回', 'url': '...', 'element': element}]
        """
        try:
            logger.info("🔍 Detecting available toto rounds...")
            
            # Enhanced patterns to detect round links more accurately
            round_patterns = [
                # PC-specific patterns (pcOnlyInline class)
                "//a[contains(@class, 'pcOnlyInline') and contains(text(), '第') and contains(text(), '回')]",
                "//a[contains(@href, 'PGSPIN00001DisptotoLotInfo') and contains(text(), '第')]",
                "//a[contains(@href, '/redirect?url=') and contains(text(), '第') and contains(text(), '回')]",
                
                # Mobile-specific patterns (spOnlyInline class) - keep for compatibility
                "//a[contains(@class, 'spOnlyInline') and contains(text(), '第') and contains(text(), '回')]",
                
                # General patterns
                "//a[contains(text(), '第') and contains(text(), '回')]",
                "//a[contains(@href, 'holdCntId=') and contains(text(), '第')]"
            ]
            
            rounds = []
            
            for pattern in round_patterns:
                try:
                    logger.debug(f"Trying pattern: {pattern}")
                    elements = self.driver.find_elements(By.XPATH, pattern)
                    
                    for element in elements:
                        if element.is_displayed() and element.is_enabled():
                            link_text = element.text.strip()
                            href = element.get_attribute('href') or ''
                            class_name = element.get_attribute('class') or ''
                            
                            # Extract round number using regex
                            match = re.search(r'第(\d+)回', link_text)
                            if match:
                                round_number = match.group(1)
                                
                                # Additional validation for round links
                                is_valid_round_link = (
                                    'PGSPIN00001DisptotoLotInfo' in href or  # PC version
                                    'PGSSIN02601InittotoSP' in href or      # Mobile version
                                    'holdCntId=' in href or                 # Has round ID
                                    'pcOnlyInline' in class_name or         # PC-specific class
                                    'spOnlyInline' in class_name            # Mobile-specific class
                                )
                                
                                if is_valid_round_link:
                                    round_info = {
                                        'round_number': round_number,
                                        'text': link_text,
                                        'url': href,
                                        'element': element,
                                        'class': class_name,
                                        'link_type': 'pc' if 'pcOnlyInline' in class_name else 'mobile' if 'spOnlyInline' in class_name else 'general'
                                    }
                                    
                                    # Avoid duplicates based on round number
                                    if not any(r['round_number'] == round_number for r in rounds):
                                        rounds.append(round_info)
                                        logger.info(f"Found round: {link_text} (Type: {round_info['link_type']}, URL: {href})")
                                else:
                                    logger.debug(f"Skipped invalid round link: {link_text} (URL: {href})")
                
                except Exception as e:
                    logger.debug(f"Pattern {pattern} failed: {e}")
                    continue
            
            # Sort by round number (descending, latest first)
            rounds.sort(key=lambda x: int(x['round_number']), reverse=True)
            
            logger.info(f"✅ Detected {len(rounds)} valid toto rounds")
            return rounds
            
        except Exception as e:
            logger.error(f"❌ Error detecting toto rounds: {e}")
            return []
    
    def select_round_automatically(self, rounds: List[Dict[str, str]]) -> bool:
        """
        Automatically select a round (latest/first available)
        
        Args:
            rounds: List of available rounds
            
        Returns:
            bool: True if selection successful, False otherwise
        """
        if not rounds:
            logger.warning("No rounds available for automatic selection")
            return False
        
        try:
            # Select the first round (or implement logic for latest)
            selected = rounds[0]
            logger.info(f"🎯 Auto-selecting round: {selected['text']}")
            
            return self._click_round(selected)
            
        except Exception as e:
            logger.error(f"❌ Error in automatic round selection: {e}")
            return False
    
    def select_round_by_number(self, rounds: List[Dict[str, str]], round_number: str) -> bool:
        """
        Select a specific round by number
        
        Args:
            rounds: List of available rounds
            round_number: The round number to select (e.g., "1558")
            
        Returns:
            bool: True if selection successful, False otherwise
        """
        try:
            # Find the specific round
            selected_round = None
            for round_info in rounds:
                if round_info['round_number'] == round_number:
                    selected_round = round_info
                    break
            
            if not selected_round:
                logger.error(f"Round {round_number} not found in available rounds")
                return False
            
            logger.info(f"🎯 Selecting round: {selected_round['text']}")
            return self._click_round(selected_round)
            
        except Exception as e:
            logger.error(f"❌ Error selecting round {round_number}: {e}")
            return False
    
    def _click_round(self, round_info: Dict[str, str]) -> bool:
        """
        Click on a round link
        
        Args:
            round_info: Round information dictionary
            
        Returns:
            bool: True if click successful, False otherwise
        """
        try:
            element = round_info['element']
            
            # Log detailed information about the link we're clicking
            logger.info(f"🎯 Clicking on round: {round_info['text']}")
            logger.info(f"   Link type: {round_info.get('link_type', 'unknown')}")
            logger.info(f"   Class: {round_info.get('class', 'none')}")
            logger.info(f"   URL: {round_info['url']}")
            
            # Store current URL for comparison
            current_url = self.driver.current_url
            
            # Handle any modal dialogs that might be blocking the click
            self._handle_modal_dialogs()
            
            # Try to click the element with different strategies
            success = self._safe_click_element(element)
            if not success:
                logger.error("❌ Failed to click round element after trying multiple strategies")
                return False
                
            logger.info("✅ Round link clicked, waiting for navigation...")
            time.sleep(4)  # Wait longer for navigation
            
            # Store selection for session memory
            self.selected_round = round_info['text']
            self.selected_round_id = round_info['round_number']
            self.selected_round_url = round_info['url']
            
            # Verify navigation
            new_url = self.driver.current_url
            logger.info(f"Navigated from: {current_url}")
            logger.info(f"Navigated to: {new_url}")
            
            # Check if we navigated to the expected round information page
            success_indicators = [
                'PGSPIN00001DisptotoLotInfo' in new_url,  # PC version round info page
                'PGSSIN02601InittotoSP' in new_url,       # Mobile version
                f'holdCntId={round_info["round_number"]}' in new_url,  # Correct round ID
                'toto' in new_url.lower(),
                'spin000' in new_url.lower(),
                'ssin026' in new_url.lower()
            ]
            
            if any(success_indicators):
                logger.info("✅ Successfully navigated to toto round information page")
                
                # Additional check for specific round ID
                if f'holdCntId={round_info["round_number"]}' in new_url:
                    logger.info(f"✅ Confirmed navigation to round {round_info['round_number']}")
                
                return True
            else:
                logger.warning(f"⚠️ Navigation may not be correct. Expected round info page, got: {new_url}")
                
                # Still consider it success if URL changed (might be different but valid)
                if new_url != current_url:
                    logger.info("URL changed, considering it a successful navigation")
                    return True
                else:
                    logger.error("❌ URL did not change, click may have failed")
                    return False
                
        except Exception as e:
            logger.error(f"❌ Error clicking round: {e}")
            return False
    
    def get_selected_round_info(self) -> Optional[Dict[str, str]]:
        """
        Get information about the currently selected round
        
        Returns:
            Dict or None: Selected round information
        """
        if self.selected_round:
            return {
                'round_text': self.selected_round,
                'round_number': self.selected_round_id,
                'round_url': self.selected_round_url
            }
        return None
    
    def is_round_selected(self) -> bool:
        """
        Check if a round has been selected in this session
        
        Returns:
            bool: True if round is selected, False otherwise
        """
        return self.selected_round is not None
    
    def click_voting_prediction_button(self) -> bool:
        """
        Click the '今すぐ投票予想する' (Start Voting Prediction) button
        Then automatically click the 'シングル' button since we always buy single
        
        Returns:
            bool: True if both buttons clicked successfully, False otherwise
        """
        try:
            logger.info("🎯 Looking for '今すぐ投票予想する' button...")
            
            # Multiple selectors to find the voting prediction button
            button_selectors = [
                "//img[@id='bt_yosou2']",
                "//img[@name='bt_yosou2']",
                "//img[@alt='今すぐ投票予想する']",
                "//img[contains(@src, 'bt_yosou.gif')]",
                "//input[@id='bt_yosou2']",
                "//button[@id='bt_yosou2']",
                "//*[@id='bt_yosou2']",
                "//*[@name='bt_yosou2']"
            ]
            
            for selector in button_selectors:
                try:
                    logger.debug(f"Trying selector: {selector}")
                    elements = self.driver.find_elements(By.XPATH, selector)
                    
                    for element in elements:
                        if element.is_displayed() and element.is_enabled():
                            logger.info(f"✅ Found voting prediction button with selector: {selector}")
                            
                            # Get button information for logging
                            button_info = {
                                'tag': element.tag_name,
                                'id': element.get_attribute('id'),
                                'name': element.get_attribute('name'),
                                'alt': element.get_attribute('alt'),
                                'src': element.get_attribute('src')
                            }
                            logger.info(f"Button info: {button_info}")
                            
                            # Click the button
                            element.click()
                            logger.info("🚀 Clicked '今すぐ投票予想する' button successfully!")
                            time.sleep(3)  # Wait for page transition
                            
                            # Verify navigation
                            new_url = self.driver.current_url
                            logger.info(f"Navigated to: {new_url}")
                            
                            # Now automatically click the シングル button since we always buy single
                            logger.info("🎯 Automatically clicking 'シングル' button (we always buy single)...")
                            if self.click_single_button():
                                logger.info("✅ Successfully clicked both '今すぐ投票予想する' and 'シングル' buttons!")
                                return True
                            else:
                                logger.warning("⚠️ '今すぐ投票予想する' succeeded but 'シングル' button failed")
                                return False
                                
                except Exception as e:
                    logger.debug(f"Selector {selector} failed: {e}")
                    continue
            
            logger.warning("⚠️ Could not find '今すぐ投票予想する' button with any selector")
            return False
            
        except Exception as e:
            logger.error(f"❌ Error clicking voting prediction button: {e}")
            return False
    
    def click_round_link_on_addition_page(self) -> bool:
        """
        Click the round link on the voting addition page (after cart addition)
        For example: <a href="#" onclick="ChengeCommodityId('06');AlertNoVote('PGSPSL00001Form','moveTotoMultiHoldCnt','1558'); return false;">第1558回</a>
        
        Returns:
            bool: True if round link clicked successfully, False otherwise
        """
        try:
            if not self.selected_round:
                logger.error("❌ No round selected - cannot click round link")
                return False
            
            # Use stored round ID instead of parsing from selected_round text
            round_number = self.selected_round_id
            logger.info(f"🎯 Looking for round link '第{round_number}回' on voting addition page...")
            
            # Wait longer for voting addition page to fully load
            time.sleep(5)
            logger.info("⏳ Waiting for voting addition page to load completely...")
            
            # Get current page info for debugging
            current_url = self.driver.current_url
            page_title = self.driver.title
            logger.info(f"Current page: {current_url}")
            logger.info(f"Page title: {page_title}")
            
            # First, click "totoの投票を追加する" button if present
            logger.info("🎯 Looking for 'totoの投票を追加する' button first...")
            toto_add_selectors = [
                "//p[contains(@class, 'c-clubtoto-btn-base__text') and contains(text(), 'totoの投票を追加する')]/parent::*",
                "//*[contains(text(), 'totoの投票を追加する')]",
                "//button[contains(text(), 'totoの投票を追加する')]",
                "//a[contains(text(), 'totoの投票を追加する')]",
                "//*[contains(@class, 'toto') and contains(text(), '投票を追加')]"
            ]
            
            toto_add_clicked = False
            for selector in toto_add_selectors:
                try:
                    logger.debug(f"Trying toto add selector: {selector}")
                    elements = self.driver.find_elements(By.XPATH, selector)
                    for element in elements:
                        if element.is_displayed() and element.is_enabled():
                            logger.info(f"✅ Found 'totoの投票を追加する' button with selector: {selector}")
                            element.click()
                            logger.info("🚀 Clicked 'totoの投票を追加する' button successfully!")
                            time.sleep(3)  # Wait for page transition
                            toto_add_clicked = True
                            break
                    if toto_add_clicked:
                        break
                except Exception as e:
                    logger.debug(f"Toto add selector {selector} failed: {e}")
                    continue
            
            if not toto_add_clicked:
                logger.info("ℹ️ 'totoの投票を追加する' button not found or not needed")
            
            # Wait a bit more after clicking toto add button
            time.sleep(2)
            
            # First, let's find ALL links with round numbers to debug
            logger.info("🔍 Debug: Finding all round-related links on page...")
            debug_selectors = [
                "//a[contains(text(), '第') and contains(text(), '回')]",
                "//a[contains(@onclick, 'ChengeCommodityId')]",
                "//a[contains(@onclick, 'moveTotoMultiHoldCnt')]",
                "//*[contains(text(), '第') and contains(text(), '回')]"
            ]
            
            all_round_links = []
            for debug_selector in debug_selectors:
                try:
                    elements = self.driver.find_elements(By.XPATH, debug_selector)
                    for element in elements:
                        if element.is_displayed():
                            link_text = element.text.strip()
                            onclick = element.get_attribute('onclick') or ''
                            href = element.get_attribute('href') or ''
                            if link_text and ('第' in link_text and '回' in link_text):
                                all_round_links.append({
                                    'text': link_text,
                                    'onclick': onclick,
                                    'href': href,
                                    'element': element
                                })
                except Exception as e:
                    logger.debug(f"Debug selector {debug_selector} failed: {e}")
            
            logger.info(f"Found {len(all_round_links)} round-related links:")
            for i, link in enumerate(all_round_links):
                logger.info(f"  {i+1}. Text: '{link['text']}', onclick: '{link['onclick'][:50]}...'")
            
            # Multiple selectors to find the specific round link (more comprehensive)
            round_link_selectors = [
                f"//a[contains(text(), '第{round_number}回')]",
                f"//a[contains(@onclick, '{round_number}') and contains(text(), '第')]",
                f"//a[contains(@onclick, 'moveTotoMultiHoldCnt') and contains(@onclick, '{round_number}')]",
                f"//a[contains(@onclick, 'ChengeCommodityId') and contains(text(), '第{round_number}回')]",
                f"//*[contains(text(), '第{round_number}回') and @onclick]",
                f"//a[@href='#' and contains(@onclick, '{round_number}')]",
                f"//a[text()='第{round_number}回']",
                f"//*[@onclick and contains(text(), '第{round_number}回')]",
                # Additional selectors for different page structures
                f"//button[contains(text(), '第{round_number}回')]",
                f"//span[contains(text(), '第{round_number}回')]/parent::a",
                f"//td[contains(text(), '第{round_number}回')]//a",
                f"//*[contains(@class, 'round') and contains(text(), '第{round_number}回')]",
                f"//a[contains(@href, '{round_number}')]",
                f"//*[contains(@id, '{round_number}') and contains(text(), '第')]"
            ]
            
            # Try exact match first
            for link in all_round_links:
                if f'第{round_number}回' in link['text'] and round_number in link['onclick']:
                    logger.info(f"✅ Found exact match round link: '{link['text']}'")
                    try:
                        link['element'].click()
                        logger.info(f"🚀 Clicked round link '第{round_number}回' successfully!")
                        time.sleep(3)  # Wait for page transition
                        
                        # Verify navigation
                        new_url = self.driver.current_url
                        logger.info(f"Navigated to: {new_url}")
                        return True
                    except Exception as click_error:
                        logger.warning(f"Failed to click exact match: {click_error}")
            
            # Try selectors if exact match failed
            for selector in round_link_selectors:
                try:
                    logger.debug(f"Trying selector: {selector}")
                    elements = self.driver.find_elements(By.XPATH, selector)
                    
                    for element in elements:
                        if element.is_displayed() and element.is_enabled():
                            logger.info(f"✅ Found round link with selector: {selector}")
                            
                            # Get link information for logging
                            link_info = {
                                'tag': element.tag_name,
                                'text': element.text,
                                'href': element.get_attribute('href'),
                                'onclick': element.get_attribute('onclick')
                            }
                            logger.info(f"Link info: {link_info}")
                            
                            # Click the link
                            element.click()
                            logger.info(f"🚀 Clicked round link '第{round_number}回' successfully!")
                            time.sleep(3)  # Wait for page transition
                            
                            # Verify navigation
                            new_url = self.driver.current_url
                            logger.info(f"Navigated to: {new_url}")
                            
                            return True
                                
                except Exception as e:
                    logger.debug(f"Selector {selector} failed: {e}")
                    continue
            
            logger.warning(f"⚠️ Could not find round link '第{round_number}回' with any method")
            logger.warning("💡 This might indicate we're not on the correct page or the page structure has changed")
            
            # Take a screenshot for debugging
            try:
                import time as time_module
                screenshot_name = f"debug_round_link_{int(time_module.time())}.png"
                self.driver.save_screenshot(screenshot_name)
                logger.info(f"📸 Screenshot saved: {screenshot_name}")
            except:
                pass
            
            return False
            
        except Exception as e:
            logger.error(f"❌ Error clicking round link: {e}")
            return False
    
    def click_single_button(self) -> bool:
        """
        Click the 'シングル' (Single) button to go to single voting page
        
        Returns:
            bool: True if button clicked successfully, False otherwise
        """
        try:
            logger.info("🎯 Looking for 'シングル' button...")
            
            # Multiple selectors to find the single button
            single_button_selectors = [
                "//img[@id='select_single']",
                "//img[@name='select_single']",
                "//img[@alt='シングル']",
                "//img[contains(@src, 'bt_toto_single.gif')]",
                "//*[@id='select_single']",
                "//*[@name='select_single']",
                "//input[@id='select_single']",
                "//button[@id='select_single']",
                "//a[@id='select_single']",
                "//img[contains(@src, 'single')]",
                "//img[contains(@alt, 'シングル')]"
            ]
            
            for selector in single_button_selectors:
                try:
                    logger.debug(f"Trying selector: {selector}")
                    elements = self.driver.find_elements(By.XPATH, selector)
                    
                    for element in elements:
                        if element.is_displayed() and element.is_enabled():
                            logger.info(f"✅ Found 'シングル' button with selector: {selector}")
                            
                            # Get button information for logging
                            button_info = {
                                'tag': element.tag_name,
                                'id': element.get_attribute('id'),
                                'name': element.get_attribute('name'),
                                'alt': element.get_attribute('alt'),
                                'src': element.get_attribute('src')
                            }
                            logger.info(f"Button info: {button_info}")
                            
                            # Click the button
                            element.click()
                            logger.info("🚀 Clicked 'シングル' button successfully!")
                            time.sleep(4)  # Wait longer for page transition to single voting page
                            
                            # Verify navigation to single voting page
                            new_url = self.driver.current_url
                            logger.info(f"Navigated to: {new_url}")
                            
                            # Check if we're on the single voting page
                            if 'PGSPSL00001MoveSingleVoteSheet' in new_url or 'single' in new_url.lower():
                                logger.info("✅ Successfully navigated to single voting page")
                                return True
                            else:
                                logger.info(f"URL changed after clicking シングル button: {new_url}")
                                # Still consider success if URL changed
                                return True
                                
                except Exception as e:
                    logger.debug(f"Selector {selector} failed: {e}")
                    continue
            
            logger.warning("⚠️ Could not find 'シングル' button with any selector")
            return False
            
        except Exception as e:
            logger.error(f"❌ Error clicking シングル button: {e}")
            return False
    
    def navigate_to_voting_prediction(self) -> bool:
        """
        Complete navigation flow: detect rounds, select round info page, click voting prediction (auto-clicks single)
        
        Returns:
            bool: True if complete flow successful, False otherwise
        """
        try:
            logger.info("🔄 Starting complete navigation to single voting page...")
            logger.info("Flow: Start Page → Detect Rounds → Select Round Info → Click Voting Prediction (auto-clicks Single)")
            
            # Step 1: Navigate to start page
            logger.info("📍 Step 1: Navigate to start page")
            if not self.navigate_to_start_page("https://www.toto-dream.com/toto/index.html"):
                logger.error("❌ Step 1 failed: Could not navigate to start page")
                return False
            logger.info("✅ Step 1 completed: On start page")
            
            # Step 2: Detect rounds
            logger.info("📍 Step 2: Detect available rounds")
            rounds = self.detect_toto_rounds()
            if not rounds:
                logger.error("❌ Step 2 failed: No rounds detected")
                return False
            logger.info(f"✅ Step 2 completed: Found {len(rounds)} rounds")
            
            # Step 3: Select round (this navigates to round info page)
            logger.info("📍 Step 3: Select round and navigate to round info page")
            if not self.select_round_automatically(rounds):
                logger.error("❌ Step 3 failed: Could not select round")
                return False
            logger.info("✅ Step 3 completed: On round info page")
            
            # Step 4: Wait and verify we're on the correct page
            logger.info("📍 Step 4: Verify round info page and look for voting prediction button")
            time.sleep(2)  # Additional wait for page to fully load
            
            # Step 5: Click voting prediction button (this now automatically clicks single too)
            logger.info("📍 Step 5: Click '今すぐ投票予想する' button (will auto-click 'シングル' too)")
            if not self.click_voting_prediction_button():
                logger.error("❌ Step 5 failed: Could not complete voting prediction and single button sequence")
                return False
            logger.info("✅ Step 5 completed: Successfully reached single voting page")
            
            # Final verification
            final_url = self.driver.current_url
            logger.info(f"🎯 Final URL: {final_url}")
            
            if 'PGSPSL00001MoveSingleVoteSheet' in final_url or 'single' in final_url.lower():
                logger.info("✅ Complete navigation to single voting page successful!")
                return True
            elif 'vote' in final_url.lower() or 'yosou' in final_url.lower():
                logger.info("✅ Complete navigation to voting page successful!")
                return True
            else:
                logger.warning(f"⚠️ Navigation completed but final URL unexpected: {final_url}")
                return True  # Still consider success if we got this far
            
        except Exception as e:
            logger.error(f"❌ Error in complete navigation flow: {e}")
            return False
    
    def _handle_modal_dialogs(self) -> None:
        """
        Handle any modal dialogs that might be blocking element clicks
        """
        try:
            logger.debug("🔍 Checking for modal dialogs...")
            
            # Common modal dialog selectors
            modal_selectors = [
                ".modal-cont-wrap",
                ".modal-dialog",
                ".modal-backdrop",
                "[role='dialog']",
                ".overlay",
                ".popup",
                "#modal",
                ".modal"
            ]
            
            # Try to close modal by clicking close buttons
            close_button_selectors = [
                ".modal-close",
                ".close",
                "button[aria-label='Close']",
                "button[data-dismiss='modal']",
                ".modal-header .close",
                "//button[contains(text(), '閉じる')]",
                "//button[contains(text(), 'Close')]",
                "//button[contains(text(), 'OK')]",
                "//span[contains(@class, 'close')]"
            ]
            
            modal_found = False
            
            # Check for modal elements
            for selector in modal_selectors:
                try:
                    if selector.startswith("//"):
                        elements = self.driver.find_elements(By.XPATH, selector)
                    else:
                        elements = self.driver.find_elements(By.CSS_SELECTOR, selector)
                    
                    for element in elements:
                        if element.is_displayed():
                            logger.info(f"🚨 Found modal dialog with selector: {selector}")
                            modal_found = True
                            break
                    
                    if modal_found:
                        break
                        
                except Exception:
                    continue
            
            if modal_found:
                logger.info("🔧 Attempting to close modal dialog...")
                
                # Try to click close buttons
                for close_selector in close_button_selectors:
                    try:
                        if close_selector.startswith("//"):
                            close_elements = self.driver.find_elements(By.XPATH, close_selector)
                        else:
                            close_elements = self.driver.find_elements(By.CSS_SELECTOR, close_selector)
                        
                        for close_element in close_elements:
                            if close_element.is_displayed() and close_element.is_enabled():
                                logger.info(f"🔧 Clicking close button: {close_selector}")
                                close_element.click()
                                time.sleep(1)
                                logger.info("✅ Modal dialog closed")
                                return
                                
                    except Exception as e:
                        logger.debug(f"Close button selector failed: {close_selector}, {e}")
                        continue
                
                # Try pressing Escape key
                try:
                    from selenium.webdriver.common.keys import Keys
                    logger.info("🔧 Trying to close modal with Escape key...")
                    self.driver.find_element(By.TAG_NAME, "body").send_keys(Keys.ESCAPE)
                    time.sleep(1)
                    logger.info("✅ Sent Escape key to close modal")
                except Exception as e:
                    logger.debug(f"Escape key failed: {e}")
                
                # Try clicking backdrop to close modal
                try:
                    logger.info("🔧 Trying to click modal backdrop...")
                    backdrop_elements = self.driver.find_elements(By.CSS_SELECTOR, ".modal-backdrop, .overlay")
                    for backdrop in backdrop_elements:
                        if backdrop.is_displayed():
                            backdrop.click()
                            time.sleep(1)
                            logger.info("✅ Clicked modal backdrop")
                            return
                except Exception as e:
                    logger.debug(f"Backdrop click failed: {e}")
            else:
                logger.debug("✅ No modal dialogs found")
                
        except Exception as e:
            logger.debug(f"Error handling modal dialogs: {e}")
    
    def _safe_click_element(self, element) -> bool:
        """
        Safely click an element using multiple strategies
        
        Args:
            element: WebElement to click
            
        Returns:
            bool: True if click successful, False otherwise
        """
        try:
            # Strategy 1: Direct click
            try:
                logger.debug("🔧 Trying direct click...")
                element.click()
                logger.info("✅ Direct click successful")
                return True
            except Exception as e:
                logger.debug(f"Direct click failed: {e}")
            
            # Strategy 2: Scroll into view and click
            try:
                logger.debug("🔧 Trying scroll into view and click...")
                self.driver.execute_script("arguments[0].scrollIntoView(true);", element)
                time.sleep(1)
                element.click()
                logger.info("✅ Scroll and click successful")
                return True
            except Exception as e:
                logger.debug(f"Scroll and click failed: {e}")
            
            # Strategy 3: JavaScript click
            try:
                logger.debug("🔧 Trying JavaScript click...")
                self.driver.execute_script("arguments[0].click();", element)
                logger.info("✅ JavaScript click successful")
                return True
            except Exception as e:
                logger.debug(f"JavaScript click failed: {e}")
            
            # Strategy 4: ActionChains click
            try:
                from selenium.webdriver.common.action_chains import ActionChains
                logger.debug("🔧 Trying ActionChains click...")
                ActionChains(self.driver).move_to_element(element).click().perform()
                logger.info("✅ ActionChains click successful")
                return True
            except Exception as e:
                logger.debug(f"ActionChains click failed: {e}")
            
            # Strategy 5: Click at coordinates
            try:
                logger.debug("🔧 Trying coordinate click...")
                self.driver.execute_script("""
                    var element = arguments[0];
                    var rect = element.getBoundingClientRect();
                    var x = rect.left + rect.width / 2;
                    var y = rect.top + rect.height / 2;
                    var clickEvent = new MouseEvent('click', {
                        'view': window,
                        'bubbles': true,
                        'cancelable': true,
                        'clientX': x,
                        'clientY': y
                    });
                    element.dispatchEvent(clickEvent);
                """, element)
                logger.info("✅ Coordinate click successful")
                return True
            except Exception as e:
                logger.debug(f"Coordinate click failed: {e}")
            
            logger.error("❌ All click strategies failed")
            return False
            
        except Exception as e:
            logger.error(f"❌ Error in safe click element: {e}")
            return False
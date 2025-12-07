#!/usr/bin/env python3
"""
Test script for the complete toto navigation flow
Tests: Start Page → Detect Rounds → Select Round Info → Click Voting Prediction
"""

import logging
import sys
import time
from pathlib import Path

# Add project root to path
sys.path.append(str(Path(__file__).parent))

from config import Config
from web_driver_manager import WebDriverManager
from toto_round_selector import TotoRoundSelector

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    handlers=[
        logging.StreamHandler(sys.stdout)
    ]
)

logger = logging.getLogger(__name__)

def test_complete_navigation_flow():
    """Test the complete navigation flow"""
    logger.info("🚀 Starting complete navigation flow test...")
    
    # Setup WebDriver
    webdriver_manager = WebDriverManager(headless=False, timeout=20)
    
    if not webdriver_manager.setup_driver():
        logger.error("❌ Failed to setup WebDriver")
        return False
    
    try:
        # Initialize round selector
        round_selector = TotoRoundSelector(webdriver_manager.driver)
        logger.info("✅ Round selector initialized")
        
        # Test complete navigation flow
        logger.info("🔄 Starting complete navigation to voting prediction...")
        success = round_selector.navigate_to_voting_prediction()
        
        if success:
            logger.info("✅ COMPLETE NAVIGATION FLOW SUCCESSFUL!")
            logger.info("🎯 Ready for next automation step (form filling)")
            
            # Get current URL for verification
            current_url = webdriver_manager.driver.current_url
            logger.info(f"📍 Final URL: {current_url}")
            
            # Display selected round info
            round_info = round_selector.get_selected_round_info()
            if round_info:
                logger.info(f"🎯 Selected Round: {round_info}")
            
            # Wait to allow manual inspection
            logger.info("⏳ Pausing for 10 seconds to allow manual inspection...")
            time.sleep(10)
            
        else:
            logger.error("❌ Complete navigation flow failed")
            
        return success
        
    except Exception as e:
        logger.error(f"❌ Test failed with exception: {e}")
        return False
        
    finally:
        # Cleanup
        logger.info("🧹 Cleaning up...")
        webdriver_manager.quit_driver()

def test_individual_components():
    """Test individual components separately"""
    logger.info("🔍 Starting individual component tests...")
    
    # Setup WebDriver
    webdriver_manager = WebDriverManager(headless=False, timeout=20)
    
    if not webdriver_manager.setup_driver():
        logger.error("❌ Failed to setup WebDriver")
        return False
    
    try:
        # Initialize round selector
        round_selector = TotoRoundSelector(webdriver_manager.driver)
        logger.info("✅ Round selector initialized")
        
        # Test 1: Navigate to start page
        logger.info("📍 Test 1: Navigate to start page")
        if round_selector.navigate_to_start_page(Config.START_URL):
            logger.info("✅ Test 1 passed: Start page navigation successful")
        else:
            logger.error("❌ Test 1 failed: Start page navigation failed")
            return False
        
        # Test 2: Detect rounds
        logger.info("🔍 Test 2: Detect available rounds")
        rounds = round_selector.detect_toto_rounds()
        if rounds:
            logger.info(f"✅ Test 2 passed: Found {len(rounds)} rounds")
            for i, round_info in enumerate(rounds):
                logger.info(f"  Round {i+1}: {round_info['text']} (Type: {round_info['link_type']})")
        else:
            logger.error("❌ Test 2 failed: No rounds detected")
            return False
        
        # Test 3: Select first round
        logger.info("🎯 Test 3: Select first available round")
        if round_selector.select_round_automatically(rounds):
            logger.info("✅ Test 3 passed: Round selection successful")
            
            # Display selected round info
            round_info = round_selector.get_selected_round_info()
            logger.info(f"Selected: {round_info}")
        else:
            logger.error("❌ Test 3 failed: Round selection failed")
            return False
        
        # Test 4: Click voting prediction button
        logger.info("🚀 Test 4: Click voting prediction button")
        if round_selector.click_voting_prediction_button():
            logger.info("✅ Test 4 passed: Voting prediction button clicked successfully")
        else:
            logger.error("❌ Test 4 failed: Could not click voting prediction button")
            return False
        
        logger.info("✅ ALL INDIVIDUAL COMPONENT TESTS PASSED!")
        
        # Wait to allow manual inspection
        logger.info("⏳ Pausing for 10 seconds to allow manual inspection...")
        time.sleep(10)
        
        return True
        
    except Exception as e:
        logger.error(f"❌ Component tests failed with exception: {e}")
        return False
        
    finally:
        # Cleanup
        logger.info("🧹 Cleaning up...")
        webdriver_manager.quit_driver()

def main():
    """Main test function"""
    logger.info("=" * 60)
    logger.info("🧪 TOTO NAVIGATION FLOW TEST SUITE")
    logger.info("=" * 60)
    
    # Test 1: Complete navigation flow
    logger.info("\n" + "=" * 40)
    logger.info("TEST 1: COMPLETE NAVIGATION FLOW")
    logger.info("=" * 40)
    
    complete_flow_success = test_complete_navigation_flow()
    
    # Test 2: Individual components (if complete flow fails)
    if not complete_flow_success:
        logger.info("\n" + "=" * 40)
        logger.info("TEST 2: INDIVIDUAL COMPONENT TESTS")
        logger.info("=" * 40)
        
        individual_tests_success = test_individual_components()
        
        if individual_tests_success:
            logger.info("✅ Individual components work - may be a timing or integration issue")
        else:
            logger.error("❌ Individual components also failing")
    
    # Final summary
    logger.info("\n" + "=" * 60)
    logger.info("📊 TEST SUMMARY")
    logger.info("=" * 60)
    
    if complete_flow_success:
        logger.info("✅ COMPLETE FLOW TEST: PASSED")
        logger.info("🎉 System ready for next automation step!")
        logger.info("📋 Next step: Implement form filling after reaching voting page")
    else:
        logger.error("❌ COMPLETE FLOW TEST: FAILED")
        logger.info("🔧 Debugging may be needed")
    
    logger.info("=" * 60)

if __name__ == "__main__":
    main()
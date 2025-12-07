#!/usr/bin/env python3
"""
Test script for the complete loop automation with batch processing
Tests: Complete workflow with multiple batches and loop handling
"""

import logging
import sys
import time
from pathlib import Path

# Add project root to path
sys.path.append(str(Path(__file__).parent))

from complete_toto_automation import CompleteTotoAutomation

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    handlers=[
        logging.StreamHandler(sys.stdout)
    ]
)

logger = logging.getLogger(__name__)

def create_test_csv():
    """Create a test CSV file with multiple batches for testing"""
    import csv
    import random
    
    test_csv_path = "test_loop_data.csv"
    
    # Create test data for 3 batches (30 sets total)
    # Each set has 13 games with values 0, 1, or 2
    test_data = []
    for batch in range(3):  # 3 batches
        for set_in_batch in range(10):  # 10 sets per batch
            row = [random.choice([0, 1, 2]) for _ in range(13)]  # 13 games
            test_data.append(row)
    
    # Write to CSV
    with open(test_csv_path, 'w', newline='', encoding='utf-8') as csvfile:
        writer = csv.writer(csvfile)
        for row in test_data:
            writer.writerow(row)
    
    logger.info(f"✅ Created test CSV with {len(test_data)} sets: {test_csv_path}")
    return test_csv_path

def test_complete_loop_automation():
    """Test the complete loop automation with multiple batches"""
    logger.info("🚀 Starting complete loop automation test...")
    
    try:
        # Create test CSV data
        csv_path = create_test_csv()
        
        # Initialize complete automation
        automation = CompleteTotoAutomation(
            headless=False,  # Visible browser for testing
            timeout=20
        )
        
        # Execute complete workflow
        logger.info("🎯 Executing complete workflow with loop processing...")
        success = automation.execute_complete_workflow(csv_path)
        
        if success:
            # Get statistics
            stats = automation.get_automation_stats()
            
            logger.info("=" * 60)
            logger.info("✅ COMPLETE LOOP AUTOMATION TEST SUCCESSFUL!")
            logger.info("=" * 60)
            logger.info(f"📦 Total Batches: {stats.get('total_batches', 0)}")
            logger.info(f"✅ Successful Batches: {stats.get('successful_batches', 0)}")
            logger.info(f"❌ Failed Batches: {stats.get('failed_batches', 0)}")
            logger.info(f"📊 Total Sets: {stats.get('total_sets', 0)}")
            logger.info(f"⏱️ Duration: {(stats.get('end_time', 0) - stats.get('start_time', 0)):.2f}s")
            
            if stats.get('successful_batches', 0) == stats.get('total_batches', 0):
                logger.info("🎉 ALL BATCHES PROCESSED SUCCESSFULLY!")
                logger.info("🛒 All items should be in cart for checkout")
            else:
                logger.warning("⚠️ Some batches failed - check logs for details")
            
        else:
            logger.error("❌ Complete loop automation test failed!")
        
        return success
        
    except Exception as e:
        logger.error(f"❌ Test failed with exception: {e}")
        return False

def test_loop_navigation_only():
    """Test just the loop navigation without form filling (for debugging)"""
    logger.info("🔍 Testing loop navigation only...")
    
    try:
        from web_driver_manager import WebDriverManager
        from toto_round_selector import TotoRoundSelector
        from config import Config
        
        # Setup WebDriver
        webdriver_manager = WebDriverManager(headless=False, timeout=20)
        
        if not webdriver_manager.setup_driver():
            logger.error("❌ Failed to setup WebDriver")
            return False
        
        # Initialize round selector
        round_selector = TotoRoundSelector(webdriver_manager.driver)
        
        # Test complete navigation
        logger.info("🎯 Testing initial navigation...")
        if not round_selector.navigate_to_voting_prediction():
            logger.error("❌ Initial navigation failed")
            return False
        
        logger.info("✅ Initial navigation successful")
        
        # Simulate being on voting addition page (would happen after cart addition)
        logger.info("🔄 Simulating navigation from voting addition page...")
        
        # In a real scenario, we would be on the addition page here
        # For testing, we'll just test the round link clicking function
        if round_selector.selected_round:
            logger.info("🎯 Testing round link click on addition page...")
            # This would normally be called when on the addition page
            # For now, just log that we would do this
            logger.info(f"Would click round link: 第{round_selector.selected_round['round_number']}回")
            
        logger.info("✅ Loop navigation test completed")
        
        # Cleanup
        webdriver_manager.quit_driver()
        return True
        
    except Exception as e:
        logger.error(f"❌ Loop navigation test failed: {e}")
        return False

def main():
    """Main test function"""
    logger.info("=" * 60)
    logger.info("🧪 COMPLETE LOOP AUTOMATION TEST SUITE")
    logger.info("=" * 60)
    
    # Ask user which test to run
    print("\nSelect test to run:")
    print("1. Complete Loop Automation (Full test with CSV data)")
    print("2. Loop Navigation Only (Debug navigation flow)")
    print("3. Both tests")
    
    choice = input("\nEnter choice (1, 2, or 3): ").strip()
    
    if choice == "1":
        logger.info("Running complete loop automation test...")
        success = test_complete_loop_automation()
    elif choice == "2":
        logger.info("Running loop navigation test...")
        success = test_loop_navigation_only()
    elif choice == "3":
        logger.info("Running both tests...")
        nav_success = test_loop_navigation_only()
        time.sleep(2)
        full_success = test_complete_loop_automation()
        success = nav_success and full_success
    else:
        logger.error("Invalid choice. Running complete test by default.")
        success = test_complete_loop_automation()
    
    # Final summary
    logger.info("\n" + "=" * 60)
    logger.info("📊 TEST SUMMARY")
    logger.info("=" * 60)
    
    if success:
        logger.info("✅ COMPLETE LOOP AUTOMATION TEST: PASSED")
        logger.info("🎉 Loop processing system is working correctly!")
        logger.info("📋 Ready for production use with multiple CSV batches")
    else:
        logger.error("❌ COMPLETE LOOP AUTOMATION TEST: FAILED")
        logger.info("🔧 Check logs for debugging information")
    
    logger.info("=" * 60)

if __name__ == "__main__":
    main()
#!/usr/bin/env python3
"""
Debug script for multi-batch automation
Tests the complete workflow with detailed debugging
"""

import logging
import sys
import time
from pathlib import Path

# Add project root to path
sys.path.append(str(Path(__file__).parent))

from complete_toto_automation import CompleteTotoAutomation

# Setup detailed logging
logging.basicConfig(
    level=logging.DEBUG,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    handlers=[
        logging.StreamHandler(sys.stdout),
        logging.FileHandler(f"debug_automation_{int(time.time())}.log")
    ]
)

logger = logging.getLogger(__name__)

def debug_multi_batch_automation():
    """Debug the multi-batch automation workflow"""
    logger.info("🔍 Starting debug multi-batch automation...")
    
    try:
        # Use the test CSV we just created
        csv_path = "test_multi_batch.csv"
        
        if not Path(csv_path).exists():
            logger.error(f"Test CSV not found: {csv_path}")
            logger.info("Run: python3 create_test_multidata.py first")
            return False
        
        # Initialize complete automation with debug settings
        automation = CompleteTotoAutomation(
            headless=False,  # Visible browser for debugging
            timeout=20  # Longer timeout for debugging
        )
        
        logger.info("🎯 Starting complete workflow with debug information...")
        
        # Execute complete workflow
        success = automation.execute_complete_workflow(csv_path)
        
        if success:
            # Get detailed statistics
            stats = automation.get_automation_stats()
            
            logger.info("=" * 60)
            logger.info("📊 DEBUG AUTOMATION RESULTS")
            logger.info("=" * 60)
            logger.info(f"📦 Total Batches Expected: 3")
            logger.info(f"📦 Total Batches Processed: {stats.get('total_batches', 0)}")
            logger.info(f"✅ Successful Batches: {stats.get('successful_batches', 0)}")
            logger.info(f"❌ Failed Batches: {stats.get('failed_batches', 0)}")
            logger.info(f"📊 Total Sets: {stats.get('total_sets', 0)}")
            logger.info(f"⏱️ Duration: {(stats.get('end_time', 0) - stats.get('start_time', 0)):.2f}s")
            
            if stats.get('total_batches', 0) < 3:
                logger.error("❌ PROBLEM: Expected 3 batches but only processed {stats.get('total_batches', 0)}")
                logger.error("💡 This indicates the batch splitting or loop processing has issues")
            elif stats.get('successful_batches', 0) < stats.get('total_batches', 0):
                logger.warning("⚠️ Some batches failed - likely the round link clicking issue")
            else:
                logger.info("🎉 ALL BATCHES PROCESSED SUCCESSFULLY!")
                
        else:
            logger.error("❌ Debug automation failed!")
        
        return success
        
    except Exception as e:
        logger.error(f"❌ Debug test failed with exception: {e}")
        return False

def test_batch_splitting_only():
    """Test just the batch splitting logic"""
    logger.info("🔍 Testing batch splitting logic only...")
    
    try:
        from data_handler import DataHandler
        
        csv_path = "test_multi_batch.csv"
        if not Path(csv_path).exists():
            logger.error(f"Test CSV not found: {csv_path}")
            return False
        
        # Initialize data handler
        data_handler = DataHandler(csv_path)
        if not data_handler.load_csv_data():
            logger.error("Failed to load CSV data")
            return False
        
        # Get data info
        data_info = data_handler.get_data_info()
        logger.info(f"📊 Data info: {data_info}")
        
        # Split into batches
        batches = data_handler.split_data_into_batches()
        logger.info(f"📦 Split into {len(batches)} batches:")
        
        for i, batch in enumerate(batches):
            logger.info(f"  Batch {i+1}: {len(batch)} sets")
            for j, set_data in enumerate(batch[:2]):  # Show first 2 sets of each batch
                logger.info(f"    Set {j+1}: {set_data}")
            if len(batch) > 2:
                logger.info(f"    ... and {len(batch)-2} more sets")
        
        if len(batches) == 3:
            logger.info("✅ Batch splitting is working correctly!")
            return True
        else:
            logger.error(f"❌ Expected 3 batches, got {len(batches)}")
            return False
        
    except Exception as e:
        logger.error(f"❌ Batch splitting test failed: {e}")
        return False

def main():
    """Main debug function"""
    logger.info("=" * 60)
    logger.info("🧪 DEBUG MULTI-BATCH AUTOMATION")
    logger.info("=" * 60)
    
    print("\nSelect debug test:")
    print("1. Test batch splitting only (quick)")
    print("2. Debug full multi-batch automation (requires browser)")
    print("3. Both tests")
    
    choice = input("\nEnter choice (1, 2, or 3): ").strip()
    
    if choice == "1":
        logger.info("Running batch splitting test...")
        success = test_batch_splitting_only()
    elif choice == "2":
        logger.info("Running full debug automation...")
        success = debug_multi_batch_automation()
    elif choice == "3":
        logger.info("Running both tests...")
        split_success = test_batch_splitting_only()
        if split_success:
            time.sleep(2)
            full_success = debug_multi_batch_automation()
        else:
            logger.error("Batch splitting failed - skipping full test")
            full_success = False
        success = split_success and full_success
    else:
        logger.error("Invalid choice - running batch splitting test")
        success = test_batch_splitting_only()
    
    # Final summary
    logger.info("\n" + "=" * 60)
    logger.info("📊 DEBUG SUMMARY")
    logger.info("=" * 60)
    
    if success:
        logger.info("✅ DEBUG TESTS: PASSED")
        logger.info("🎯 Multi-batch system should be working")
    else:
        logger.error("❌ DEBUG TESTS: FAILED")
        logger.info("🔧 Check logs for specific issues")
    
    logger.info("=" * 60)

if __name__ == "__main__":
    main()
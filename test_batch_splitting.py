#!/usr/bin/env python3
"""
Test batch splitting logic without selenium dependencies
"""

import sys
from pathlib import Path

# Add project root to path
sys.path.append(str(Path(__file__).parent))

from data_handler import DataHandler
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def test_batch_splitting():
    """Test the batch splitting logic"""
    logger.info("🔍 Testing batch splitting logic...")
    
    try:
        csv_path = "test_multi_batch.csv"
        if not Path(csv_path).exists():
            logger.error(f"Test CSV not found: {csv_path}")
            logger.info("Run: python3 create_test_multidata.py first")
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
        
        total_sets_in_batches = 0
        for i, batch in enumerate(batches):
            total_sets_in_batches += len(batch)
            logger.info(f"  Batch {i+1}: {len(batch)} sets")
            # Show first set of each batch as example
            if batch:
                logger.info(f"    Example set 1: {batch[0]}")
        
        logger.info(f"📊 Total sets in original data: {data_info['total_sets']}")
        logger.info(f"📊 Total sets in all batches: {total_sets_in_batches}")
        
        if len(batches) == 3 and total_sets_in_batches == 25:
            logger.info("✅ Batch splitting is working correctly!")
            logger.info("Expected: 3 batches with 10, 10, 5 sets")
            logger.info(f"Actual: {len(batches)} batches with {[len(b) for b in batches]} sets")
            return True
        else:
            logger.error(f"❌ Expected 3 batches with 25 total sets")
            logger.error(f"Got {len(batches)} batches with {total_sets_in_batches} total sets")
            return False
        
    except Exception as e:
        logger.error(f"❌ Batch splitting test failed: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    success = test_batch_splitting()
    if success:
        print("\n✅ Batch splitting works correctly!")
        print("🎯 The issue is likely in the cart navigation loop, not batch splitting")
        print("💡 The system may not be properly detecting the voting addition page")
        print("   or the round link clicking is failing")
    else:
        print("\n❌ Batch splitting has issues!")
        print("🔧 Fix the data handling first")
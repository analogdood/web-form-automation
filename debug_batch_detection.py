#!/usr/bin/env python3
"""
Debug batch detection issue - why only 1 batch detected when there should be 2+
"""

import sys
from pathlib import Path
sys.path.append(str(Path(__file__).parent))

import logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def debug_batch_detection():
    """Debug why only 1 batch is detected"""
    try:
        from data_handler import DataHandler
        
        # Check all CSV files
        csv_files = list(Path('.').glob('*.csv'))
        
        for csv_file in csv_files:
            logger.info(f"\n=== Testing {csv_file.name} ===")
            try:
                handler = DataHandler(str(csv_file))
                if handler.load_csv_data():
                    info = handler.get_data_info()
                    total_sets = info['total_sets']
                    estimated_batches = info['estimated_batches']
                    
                    logger.info(f"📊 Total sets: {total_sets}")
                    logger.info(f"📊 Estimated batches: {estimated_batches}")
                    
                    # Split into batches
                    batches = handler.split_data_into_batches()
                    actual_batches = len(batches)
                    batch_sizes = [len(b) for b in batches]
                    
                    logger.info(f"📦 Actual batches: {actual_batches}")
                    logger.info(f"📦 Batch sizes: {batch_sizes}")
                    
                    # Check batch size calculation
                    max_batch_size = handler.max_batch_size
                    logger.info(f"🔢 Max batch size: {max_batch_size}")
                    
                    if actual_batches == 1 and total_sets > max_batch_size:
                        logger.error(f"❌ BUG: {total_sets} sets should create multiple batches (max size: {max_batch_size})")
                    elif actual_batches > 1:
                        logger.info(f"✅ Correctly split {total_sets} sets into {actual_batches} batches")
                    else:
                        logger.info(f"✅ Single batch is correct for {total_sets} sets (≤ {max_batch_size})")
                        
                else:
                    logger.error(f"❌ Failed to load {csv_file.name}")
                    
            except Exception as e:
                logger.error(f"❌ Error with {csv_file.name}: {e}")
                
        # The user mentioned they had 2 batches, so let's check what might be the issue
        logger.info(f"\n=== Diagnosis ===")
        logger.info("🔍 If you're seeing 'batch processing completed: 1/1 successful'")
        logger.info("   but expecting 2+ batches, possible causes:")
        logger.info("   1. Wrong CSV file being used (check GUI CSV path)")
        logger.info("   2. CSV file has ≤10 sets (creates only 1 batch)")
        logger.info("   3. EnhancedAutomationSystem.batch_data is set (forces single batch)")
        logger.info("   4. Data handler not being used (fallback to batch_data)")
                
    except Exception as e:
        logger.error(f"❌ Debug failed: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    debug_batch_detection()
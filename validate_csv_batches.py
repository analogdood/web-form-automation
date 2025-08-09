#!/usr/bin/env python3
"""
Validate CSV files for multi-batch processing
"""

import sys
from pathlib import Path
sys.path.append(str(Path(__file__).parent))

import logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def validate_csv_batches():
    """Check which CSV files create multiple batches"""
    try:
        from data_handler import DataHandler
        
        logger.info("🔍 CHECKING CSV FILES FOR MULTI-BATCH POTENTIAL")
        logger.info("=" * 60)
        
        csv_files = list(Path('.').glob('*.csv'))
        multi_batch_files = []
        
        for csv_file in csv_files:
            try:
                handler = DataHandler(str(csv_file))
                if handler.load_csv_data():
                    info = handler.get_data_info()
                    total_sets = info['total_sets']
                    
                    batches = handler.split_data_into_batches()
                    actual_batches = len(batches)
                    batch_sizes = [len(b) for b in batches]
                    
                    logger.info(f"\n📄 {csv_file.name}:")
                    logger.info(f"   📊 Total sets: {total_sets}")
                    logger.info(f"   📦 Batches: {actual_batches}")
                    logger.info(f"   📏 Batch sizes: {batch_sizes}")
                    
                    if actual_batches > 1:
                        multi_batch_files.append({
                            'name': csv_file.name,
                            'sets': total_sets,
                            'batches': actual_batches,
                            'sizes': batch_sizes
                        })
                        logger.info(f"   ✅ MULTI-BATCH FILE")
                    else:
                        logger.info(f"   ⚠️ Single batch only")
                        
            except Exception as e:
                logger.error(f"❌ Error with {csv_file.name}: {e}")
        
        logger.info(f"\n" + "=" * 60)
        if multi_batch_files:
            logger.info("✅ MULTI-BATCH FILES FOUND:")
            for file_info in multi_batch_files:
                logger.info(f"   🎯 {file_info['name']}: {file_info['sets']} sets → {file_info['batches']} batches {file_info['sizes']}")
            
            best_file = max(multi_batch_files, key=lambda x: x['batches'])
            logger.info(f"\n💡 RECOMMENDED FOR TESTING:")
            logger.info(f"   Use '{best_file['name']}' in the GUI")
            logger.info(f"   Expected result: 'batch processing completed: {best_file['batches']}/{best_file['batches']} successful'")
        else:
            logger.warning("⚠️ NO MULTI-BATCH FILES FOUND")
            logger.info("   All CSV files have ≤10 sets (create only 1 batch)")
            logger.info("   This explains why you see 'batch processing completed: 1/1 successful'")
            
        logger.info(f"\n🔍 DIAGNOSIS:")
        logger.info("   If user sees '1/1 successful' but expects 2+ batches:")
        logger.info("   → User is using a CSV file with ≤10 sets")
        logger.info("   → Solution: Use a CSV file with >10 sets")
            
    except Exception as e:
        logger.error(f"❌ Validation failed: {e}")

if __name__ == "__main__":
    validate_csv_batches()
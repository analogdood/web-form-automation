#!/usr/bin/env python3
"""
Create test CSV file with multiple batches for testing the loop automation
"""

import csv
import random
import logging

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def create_multi_batch_test_csv():
    """Create a test CSV with multiple batches (25 sets = 3 batches)"""
    
    # Create 25 sets (will be split into 3 batches: 10, 10, 5)
    test_data = []
    
    for set_num in range(25):  # 25 sets total
        # Generate random betting data for 13 games
        row = []
        for game in range(13):
            # Random choice: 0=引き分け, 1=ホーム勝ち, 2=アウェイ勝ち
            row.append(random.choice([0, 1, 2]))
        
        test_data.append(row)
        logger.info(f"Created set {set_num + 1}: {row}")
    
    # Write to CSV
    csv_filename = "test_multi_batch.csv"
    with open(csv_filename, 'w', newline='', encoding='utf-8') as csvfile:
        writer = csv.writer(csvfile)
        for row in test_data:
            writer.writerow(row)
    
    logger.info("=" * 60)
    logger.info(f"✅ Created test CSV: {csv_filename}")
    logger.info(f"📊 Total sets: {len(test_data)}")
    logger.info(f"📦 Expected batches: {(len(test_data) + 9) // 10}")  # 10 sets per batch
    logger.info("Batch breakdown:")
    
    # Show how batches will be split
    batch_size = 10
    for i in range(0, len(test_data), batch_size):
        batch_num = (i // batch_size) + 1
        batch_sets = min(batch_size, len(test_data) - i)
        logger.info(f"  Batch {batch_num}: Sets {i+1}-{i+batch_sets} ({batch_sets} sets)")
    
    logger.info("=" * 60)
    
    return csv_filename

if __name__ == "__main__":
    csv_file = create_multi_batch_test_csv()
    print(f"\n✅ Test CSV created: {csv_file}")
    print("🎯 Use this file to test the multi-batch loop automation!")
    print("\nTo test:")
    print("1. Run: python3 enhanced_gui_automation.py")
    print("2. Load this CSV file")
    print("3. Click 'Complete Workflow'")
    print("4. Watch the multi-batch processing!")
"""
Test script for Web Form Automation System
"""

import sys
import logging
from pathlib import Path
from data_handler import DataHandler
from config import Config

def test_csv_loading():
    """Test CSV data loading functionality"""
    print("Testing CSV data loading...")
    
    # Test with sample data
    data_handler = DataHandler("sample_data.csv")
    
    if not data_handler.load_csv_data():
        print("❌ Failed to load CSV data")
        return False
    
    # Check data info
    info = data_handler.get_data_info()
    print(f"✅ CSV loaded: {info['total_sets']} sets")
    
    # Test batch splitting
    batches = data_handler.split_data_into_batches()
    print(f"✅ Data split into {len(batches)} batches")
    
    # Test data preview
    preview = data_handler.preview_data(2)
    print(f"✅ Data preview: {len(preview)} rows")
    
    return True

def test_configuration():
    """Test configuration settings"""
    print("Testing configuration...")
    
    # Test basic config values
    assert Config.MAX_SETS_PER_BATCH == 10
    assert Config.MAX_GAMES_PER_SET == 13
    assert Config.VALID_VALUES == [0, 1, 2]
    
    print("✅ Configuration validated")
    return True

def test_data_validation():
    """Test data validation"""
    print("Testing data validation...")
    
    data_handler = DataHandler("sample_data.csv")
    
    # Test valid set
    valid_set = [1, 2, 0, 1, 2, 0, 1, 2, 0, 1, 2, 0, 1]
    assert data_handler.validate_single_set(valid_set) == True
    
    # Test invalid set (wrong length)
    invalid_set_length = [1, 2, 0, 1, 2]
    assert data_handler.validate_single_set(invalid_set_length) == False
    
    # Test invalid set (wrong values)
    invalid_set_values = [1, 2, 0, 1, 2, 0, 1, 2, 0, 1, 2, 0, 3]  # 3 is invalid
    assert data_handler.validate_single_set(invalid_set_values) == False
    
    print("✅ Data validation tests passed")
    return True

def main():
    """Run all tests"""
    print("Web Form Automation System - Test Suite")
    print("=" * 50)
    
    # Setup basic logging
    logging.basicConfig(level=logging.ERROR)
    
    tests = [
        test_configuration,
        test_csv_loading,
        test_data_validation
    ]
    
    passed = 0
    failed = 0
    
    for test in tests:
        try:
            if test():
                passed += 1
            else:
                failed += 1
        except Exception as e:
            print(f"❌ Test failed with exception: {e}")
            failed += 1
        print()
    
    print("=" * 50)
    print(f"Test Results: {passed} passed, {failed} failed")
    
    if failed == 0:
        print("🎉 All tests passed!")
        return True
    else:
        print("⚠️ Some tests failed!")
        return False

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
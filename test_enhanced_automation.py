"""
Test suite for Enhanced Web Form Automation System
"""

import sys
import logging
import json
from pathlib import Path
from action_manager import (
    ActionStep, ActionSequence, ActionFileManager, ActionValidator,
    ActionType, create_action_step
)
from data_handler import DataHandler
from config import Config

def test_action_management():
    """Test action management functionality"""
    print("Testing action management...")
    
    # Test action step creation
    step = create_action_step(
        ActionType.CLICK,
        selector="button.submit",
        description="Submit button"
    )
    assert step.action == "click"
    assert step.selector == "button.submit"
    print("✅ Action step creation")
    
    # Test action validation
    errors = ActionValidator.validate_action_step(step)
    assert len(errors) == 0
    print("✅ Action validation")
    
    # Test invalid action
    invalid_step = ActionStep(action="", selector="")
    errors = ActionValidator.validate_action_step(invalid_step)
    assert len(errors) > 0
    print("✅ Invalid action detection")
    
    return True

def test_action_file_management():
    """Test action file operations"""
    print("Testing action file management...")
    
    file_manager = ActionFileManager()
    
    # Test sample action creation
    sample_actions = file_manager.create_sample_actions()
    assert len(sample_actions.batch_actions) > 0
    print("✅ Sample action creation")
    
    # Test action sequence validation
    is_valid = ActionValidator.is_valid_sequence(sample_actions)
    assert is_valid == True
    print("✅ Action sequence validation")
    
    # Test save and load
    test_filename = "test_actions.json"
    success = file_manager.save_actions(sample_actions, test_filename)
    assert success == True
    print("✅ Action file saving")
    
    loaded_actions = file_manager.load_actions(test_filename)
    assert loaded_actions is not None
    assert len(loaded_actions.batch_actions) == len(sample_actions.batch_actions)
    print("✅ Action file loading")
    
    # Cleanup test file
    try:
        (file_manager.actions_dir / test_filename).unlink()
    except:
        pass
    
    return True

def test_enhanced_csv_handling():
    """Test CSV handling with large datasets"""
    print("Testing enhanced CSV handling...")
    
    # Create test CSV with more data
    test_csv_path = "test_large_data.csv"
    
    # Generate 25 rows of test data (will create 3 batches)
    test_data = []
    for i in range(25):
        row = [i % 3 for _ in range(13)]  # Create pattern with 0,1,2
        test_data.append(",".join(map(str, row)))
    
    with open(test_csv_path, 'w') as f:
        f.write("\n".join(test_data))
    
    # Test data handling
    data_handler = DataHandler(test_csv_path)
    success = data_handler.load_csv_data()
    assert success == True
    print("✅ Large CSV loading")
    
    # Test batch splitting
    batches = data_handler.split_data_into_batches(batch_size=10)
    expected_batches = 3  # 25 rows -> 3 batches (10+10+5)
    assert len(batches) == expected_batches
    print(f"✅ Batch splitting: {len(batches)} batches created")
    
    # Test batch sizes
    assert len(batches[0]) == 10
    assert len(batches[1]) == 10
    assert len(batches[2]) == 5
    print("✅ Batch size validation")
    
    # Cleanup test file
    try:
        Path(test_csv_path).unlink()
    except:
        pass
    
    return True

def test_configuration():
    """Test enhanced configuration"""
    print("Testing enhanced configuration...")
    
    # Test action types
    assert ActionType.CLICK.value == "click"
    assert ActionType.WAIT_FOR_ELEMENT.value == "wait_for_element"
    print("✅ Action types")
    
    # Test config values
    assert Config.MAX_SETS_PER_BATCH >= 1
    assert Config.MAX_GAMES_PER_SET == 13
    assert Config.VALID_VALUES == [0, 1, 2]
    print("✅ Configuration values")
    
    return True

def test_action_types_coverage():
    """Test all supported action types"""
    print("Testing action type coverage...")
    
    supported_actions = [
        ActionType.CLICK,
        ActionType.WAIT_FOR_ELEMENT,
        ActionType.WAIT_FOR_URL_CHANGE,
        ActionType.WAIT_FOR_ALERT,
        ActionType.INPUT_TEXT,
        ActionType.SCREENSHOT,
        ActionType.SLEEP,
        ActionType.CONFIRM_CHECKBOX,
        ActionType.SUBMIT_FORM
    ]
    
    for action_type in supported_actions:
        step = create_action_step(action_type, selector="test")
        assert step.action == action_type.value
    
    print(f"✅ All {len(supported_actions)} action types supported")
    return True

def test_json_serialization():
    """Test JSON serialization of action sequences"""
    print("Testing JSON serialization...")
    
    # Create action sequence
    metadata = {"name": "Test Sequence", "version": "1.0"}
    actions = [
        create_action_step(ActionType.CLICK, "button.test", description="Test button"),
        create_action_step(ActionType.SLEEP, value="2.0", description="Wait 2 seconds")
    ]
    
    sequence = ActionSequence(metadata=metadata, batch_actions=actions)
    
    # Test serialization
    sequence_dict = sequence.to_dict()
    assert "metadata" in sequence_dict
    assert "batch_actions" in sequence_dict
    assert len(sequence_dict["batch_actions"]) == 2
    print("✅ Action sequence serialization")
    
    # Test deserialization
    restored_sequence = ActionSequence.from_dict(sequence_dict)
    assert len(restored_sequence.batch_actions) == len(actions)
    assert restored_sequence.metadata["name"] == "Test Sequence"
    print("✅ Action sequence deserialization")
    
    return True

def test_error_handling():
    """Test error handling scenarios"""
    print("Testing error handling...")
    
    # Test invalid CSV
    data_handler = DataHandler("nonexistent.csv")
    success = data_handler.load_csv_data()
    assert success == False
    print("✅ Invalid CSV handling")
    
    # Test invalid action file
    file_manager = ActionFileManager()
    actions = file_manager.load_actions("nonexistent.json")
    assert actions is None
    print("✅ Invalid action file handling")
    
    # Test validation errors
    invalid_sequence = ActionSequence(
        metadata={},
        batch_actions=[]
    )
    errors = ActionValidator.validate_action_sequence(invalid_sequence)
    assert len(errors) > 0
    print("✅ Validation error detection")
    
    return True

def main():
    """Run all enhanced tests"""
    print("Enhanced Web Form Automation System - Test Suite")
    print("=" * 60)
    
    # Setup basic logging
    logging.basicConfig(level=logging.ERROR)
    
    tests = [
        test_configuration,
        test_action_management,
        test_action_file_management,
        test_enhanced_csv_handling,
        test_action_types_coverage,
        test_json_serialization,
        test_error_handling
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
    
    print("=" * 60)
    print(f"Enhanced Test Results: {passed} passed, {failed} failed")
    
    if failed == 0:
        print("🎉 All enhanced tests passed!")
        print("\n🚀 Enhanced system ready for use:")
        print("   • GUI: python enhanced_gui_launcher.py")
        print("   • CLI: python enhanced_automation.py --help")
        return True
    else:
        print("⚠️ Some enhanced tests failed!")
        return False

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
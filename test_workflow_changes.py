#!/usr/bin/env python3
"""
Test workflow changes without selenium dependencies
"""

import sys
from pathlib import Path

# Add project root to path
sys.path.append(str(Path(__file__).parent))

import logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def test_workflow_changes():
    """Test that the workflow changes are correct"""
    logger.info("🔍 Testing workflow changes...")
    
    try:
        # Test 1: Verify batch splitting works
        from data_handler import DataHandler
        
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
        logger.info(f"📦 Split into {len(batches)} batches: {[len(b) for b in batches]}")
        
        if len(batches) != 3:
            logger.error(f"❌ Expected 3 batches, got {len(batches)}")
            return False
        
        if [len(b) for b in batches] != [10, 10, 5]:
            logger.error(f"❌ Expected [10, 10, 5] batch sizes, got {[len(b) for b in batches]}")
            return False
        
        logger.info("✅ Batch splitting test PASSED")
        
        # Test 2: Check if the GUI changes are syntactically correct
        try:
            logger.info("🔍 Testing GUI automation changes...")
            
            # Read the modified file to check syntax
            gui_file = Path("enhanced_gui_automation.py")
            if not gui_file.exists():
                logger.error("GUI file not found")
                return False
            
            # Try to compile the Python syntax (without importing due to dependencies)
            with open(gui_file, 'r', encoding='utf-8') as f:
                content = f.read()
            
            compile(content, str(gui_file), 'exec')
            logger.info("✅ GUI automation syntax test PASSED")
            
            # Check if the problematic methods were replaced
            if "self.automation_system.execute()" in content:
                logger.error("❌ Still contains old execute() method call")
                return False
            
            if "self.automation_system._process_data_batches()" in content:
                logger.info("✅ Uses correct _process_data_batches() method")
            else:
                logger.error("❌ Missing _process_data_batches() method call")
                return False
            
            if "self.automation_system._load_data()" in content:
                logger.info("✅ Calls _load_data() to load CSV")
            else:
                logger.error("❌ Missing _load_data() method call")
                return False
            
            logger.info("✅ GUI workflow changes test PASSED")
            
        except SyntaxError as e:
            logger.error(f"❌ GUI syntax error: {e}")
            return False
        
        # Test 3: Verify EnhancedAutomationSystem has required methods
        logger.info("🔍 Testing EnhancedAutomationSystem structure...")
        
        enhanced_file = Path("enhanced_automation.py")
        if not enhanced_file.exists():
            logger.error("Enhanced automation file not found")
            return False
        
        with open(enhanced_file, 'r', encoding='utf-8') as f:
            enhanced_content = f.read()
        
        required_methods = [
            "def _setup_webdriver(self)",
            "def _load_data(self)",
            "def _process_data_batches(self)",
            "def _process_single_batch_basic(self, batch_data: List[List[int]])"
        ]
        
        for method in required_methods:
            if method in enhanced_content:
                logger.info(f"✅ Found method: {method.split('(')[0].replace('def ', '')}")
            else:
                logger.error(f"❌ Missing method: {method}")
                return False
        
        # Check for proper loop handling in _process_single_batch_basic
        if "if self.current_batch > 1:" in enhanced_content:
            logger.info("✅ Contains multi-batch loop handling")
        else:
            logger.error("❌ Missing multi-batch loop handling")
            return False
        
        if "click_round_link_on_addition_page()" in enhanced_content:
            logger.info("✅ Contains round link clicking for loop processing")
        else:
            logger.error("❌ Missing round link clicking for loop processing")
            return False
        
        logger.info("✅ EnhancedAutomationSystem structure test PASSED")
        
        logger.info("🎉 ALL WORKFLOW TESTS PASSED!")
        logger.info("🎯 The multi-batch processing should now work correctly:")
        logger.info("   - Browser will not close prematurely")
        logger.info("   - All 3 batches should be processed")
        logger.info("   - Loop navigation between batches should work")
        logger.info("   - Using existing EnhancedAutomationSystem instead of CompleteTotoAutomation")
        
        return True
        
    except Exception as e:
        logger.error(f"❌ Workflow test failed: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    success = test_workflow_changes()
    if success:
        print("\n✅ WORKFLOW CHANGES VALIDATED!")
        print("🚀 Ready to test with actual browser automation")
        print("💡 The browser closure and single-batch issues should be fixed")
    else:
        print("\n❌ WORKFLOW CHANGES HAVE ISSUES!")
        print("🔧 Please check the test output for specific problems")
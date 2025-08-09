#!/usr/bin/env python3
"""
Test GUI launch
"""

import sys
from pathlib import Path

# Add project root to path
sys.path.append(str(Path(__file__).parent))

def test_gui():
    """Test GUI launch"""
    try:
        print("🚀 Launching GUI...")
        from enhanced_gui_automation import EnhancedAutomationGUI
        
        app = EnhancedAutomationGUI()
        print("✅ GUI created successfully")
        print("📱 GUI should now be visible")
        print("💡 Close the window to exit")
        
        # Start the GUI event loop
        app.root.mainloop()
        print("👋 GUI closed")
        
    except Exception as e:
        print(f"❌ GUI launch failed: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    test_gui()
#!/usr/bin/env python3
"""
Enhanced GUI Launcher with Action Recording and Playback
"""

import sys
import tkinter as tk
from tkinter import messagebox
import subprocess
import pkg_resources
import importlib.util

def check_dependencies():
    """Check if all required dependencies are installed"""
    required_packages = [
        'selenium',
        'pandas', 
        'webdriver-manager',
        'click'
    ]
    
    missing_packages = []
    
    for package in required_packages:
        try:
            pkg_resources.get_distribution(package)
        except pkg_resources.DistributionNotFound:
            missing_packages.append(package)
    
    return missing_packages

def install_dependencies(packages):
    """Install missing dependencies"""
    try:
        for package in packages:
            print(f"Installing {package}...")
            subprocess.check_call([sys.executable, "-m", "pip", "install", package])
        return True
    except subprocess.CalledProcessError:
        return False

def show_welcome_info():
    """Show welcome information about enhanced features"""
    root = tk.Tk()
    root.withdraw()  # Hide main window
    
    info_text = """
🚀 Enhanced Web Form Automation System

新機能:
✅ 操作記録・再生機能
✅ 3つの動作モード (Basic/Record/Execute)  
✅ アクションファイル管理
✅ 大量データ対応 (100+セット)
✅ GUI・CLI両対応

主な改善点:
• サイト変更に強い柔軟性
• 複雑な操作シーケンスの簡単管理
• 他サイトでの再利用可能性
• 保守性・スケーラビリティの向上

使用方法:
1. Record Mode: 操作を記録してアクションファイル作成
2. Execute Mode: CSVデータ + アクションで大量処理
3. Basic Mode: 従来機能（フォーム入力のみ）

詳細は README_ENHANCED.md をご覧ください
"""
    
    messagebox.showinfo("Enhanced Web Form Automation", info_text)
    root.destroy()

def main():
    """Main launcher function"""
    print("Enhanced Web Form Automation System - GUI Launcher")
    print("=" * 60)
    
    # Show welcome info
    show_welcome_info()
    
    # Check dependencies
    missing = check_dependencies()
    
    if missing:
        print(f"Missing dependencies: {', '.join(missing)}")
        
        # Create simple tkinter window for user choice
        root = tk.Tk()
        root.withdraw()  # Hide main window
        
        install = messagebox.askyesno(
            "Missing Dependencies",
            f"The following packages are missing:\n{', '.join(missing)}\n\n"
            f"Would you like to install them automatically?"
        )
        
        root.destroy()
        
        if install:
            print("Installing dependencies...")
            if install_dependencies(missing):
                print("Dependencies installed successfully!")
            else:
                print("Failed to install dependencies.")
                print("Please run: pip install -r requirements.txt")
                sys.exit(1)
        else:
            print("Please install dependencies manually:")
            print("pip install -r requirements.txt")
            sys.exit(1)
    
    # Import and run Enhanced GUI
    try:
        from enhanced_gui_automation import EnhancedAutomationGUI
        print("Starting Enhanced GUI application...")
        app = EnhancedAutomationGUI()
        app.run()
    except ImportError as e:
        print(f"Failed to import Enhanced GUI module: {e}")
        
        # Fallback to basic GUI
        try:
            from gui_automation import AutomationGUI
            print("Falling back to basic GUI...")
            app = AutomationGUI()
            app.run()
        except ImportError:
            print("Failed to import any GUI module")
            sys.exit(1)
    except Exception as e:
        print(f"Error starting Enhanced GUI: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()
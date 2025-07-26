#!/usr/bin/env python3
"""
Simple launcher script for the GUI application
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

def main():
    """Main launcher function"""
    print("Web Form Automation System - GUI Launcher")
    print("=" * 50)
    
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
    
    # Import and run GUI
    try:
        from gui_automation import AutomationGUI
        print("Starting GUI application...")
        app = AutomationGUI()
        app.run()
    except ImportError as e:
        print(f"Failed to import GUI module: {e}")
        sys.exit(1)
    except Exception as e:
        print(f"Error starting GUI: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()
"""
GUI Application for Web Form Automation System
"""

import tkinter as tk
from tkinter import ttk, filedialog, messagebox, scrolledtext
import threading
import queue
import logging
from pathlib import Path
import sys
import os
from typing import Optional

# Import our automation components
from config import Config
from data_handler import DataHandler
from voting_automation import VotingAutomationSystem

class AutomationGUI:
    """Main GUI application for web form automation"""
    
    def __init__(self):
        self.root = tk.Tk()
        self.root.title("Web Form Automation System")
        self.root.geometry("800x600")
        self.root.resizable(True, True)
        
        # Application state
        self.csv_path = tk.StringVar()
        self.url = tk.StringVar(value="https://www.toto-dream.com/toto/index.html")
        self.headless = tk.BooleanVar(value=False)
        self.browser = tk.StringVar(value="chrome")
        self.timeout = tk.IntVar(value=10)
        self.log_level = tk.StringVar(value="INFO")
        
        # Automation system
        self.automation_system: Optional[VotingAutomationSystem] = None
        self.automation_thread: Optional[threading.Thread] = None
        self.is_running = False
        
        # Logging setup
        self.log_queue = queue.Queue()
        self.setup_logging()
        
        # Create GUI
        self.create_widgets()
        self.setup_logging_handler()
        
        # Start log processing
        self.process_log_queue()
    
    def setup_logging(self):
        """Setup logging for the GUI"""
        class QueueHandler(logging.Handler):
            def __init__(self, log_queue):
                super().__init__()
                self.log_queue = log_queue
            
            def emit(self, record):
                self.log_queue.put(self.format(record))
        
        # Create queue handler
        self.queue_handler = QueueHandler(self.log_queue)
        self.queue_handler.setFormatter(
            logging.Formatter('%(asctime)s - %(levelname)s - %(message)s')
        )
        
        # Configure root logger
        root_logger = logging.getLogger()
        root_logger.setLevel(logging.DEBUG)
        root_logger.addHandler(self.queue_handler)
    
    def create_widgets(self):
        """Create and layout GUI widgets"""
        # Create notebook for tabs
        self.notebook = ttk.Notebook(self.root)
        self.notebook.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
        
        # Create tabs
        self.create_main_tab()
        self.create_settings_tab()
        self.create_logs_tab()
        
        # Status bar
        self.create_status_bar()
    
    def create_main_tab(self):
        """Create main control tab"""
        main_frame = ttk.Frame(self.notebook)
        self.notebook.add(main_frame, text="Main")
        
        # File selection section
        file_frame = ttk.LabelFrame(main_frame, text="CSV File Selection", padding=10)
        file_frame.pack(fill=tk.X, padx=10, pady=5)
        
        ttk.Label(file_frame, text="CSV File:").grid(row=0, column=0, sticky=tk.W, pady=2)
        ttk.Entry(file_frame, textvariable=self.csv_path, width=60).grid(row=0, column=1, padx=5, pady=2)
        ttk.Button(file_frame, text="Browse", command=self.browse_csv_file).grid(row=0, column=2, padx=5, pady=2)
        
        # URL section
        url_frame = ttk.LabelFrame(main_frame, text="Target URL (Optional)", padding=10)
        url_frame.pack(fill=tk.X, padx=10, pady=5)
        
        ttk.Label(url_frame, text="URL:").grid(row=0, column=0, sticky=tk.W, pady=2)
        ttk.Entry(url_frame, textvariable=self.url, width=70).grid(row=0, column=1, padx=5, pady=2)
        
        # Data preview section
        preview_frame = ttk.LabelFrame(main_frame, text="Data Preview", padding=10)
        preview_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=5)
        
        self.data_preview = scrolledtext.ScrolledText(preview_frame, height=8, state=tk.DISABLED)
        self.data_preview.pack(fill=tk.BOTH, expand=True)
        
        ttk.Button(preview_frame, text="Load & Preview Data", command=self.preview_data).pack(pady=5)
        
        # Control buttons
        control_frame = ttk.Frame(main_frame)
        control_frame.pack(fill=tk.X, padx=10, pady=10)
        
        self.start_button = ttk.Button(control_frame, text="Start Automation", command=self.start_automation)
        self.start_button.pack(side=tk.LEFT, padx=5)
        
        self.stop_button = ttk.Button(control_frame, text="Stop", command=self.stop_automation, state=tk.DISABLED)
        self.stop_button.pack(side=tk.LEFT, padx=5)
        
        ttk.Button(control_frame, text="Take Screenshot", command=self.take_screenshot).pack(side=tk.RIGHT, padx=5)
    
    def create_settings_tab(self):
        """Create settings configuration tab"""
        settings_frame = ttk.Frame(self.notebook)
        self.notebook.add(settings_frame, text="Settings")
        
        # Browser settings
        browser_frame = ttk.LabelFrame(settings_frame, text="Browser Settings", padding=10)
        browser_frame.pack(fill=tk.X, padx=10, pady=5)
        
        ttk.Label(browser_frame, text="Browser:").grid(row=0, column=0, sticky=tk.W, pady=2)
        browser_combo = ttk.Combobox(browser_frame, textvariable=self.browser, values=["chrome", "firefox", "edge"])
        browser_combo.grid(row=0, column=1, sticky=tk.W, padx=5, pady=2)
        
        ttk.Checkbutton(browser_frame, text="Headless Mode", variable=self.headless).grid(row=1, column=0, columnspan=2, sticky=tk.W, pady=2)
        
        # Timeout settings
        timeout_frame = ttk.LabelFrame(settings_frame, text="Timeout Settings", padding=10)
        timeout_frame.pack(fill=tk.X, padx=10, pady=5)
        
        ttk.Label(timeout_frame, text="WebDriver Timeout (seconds):").grid(row=0, column=0, sticky=tk.W, pady=2)
        timeout_spin = ttk.Spinbox(timeout_frame, from_=5, to=60, textvariable=self.timeout, width=10)
        timeout_spin.grid(row=0, column=1, sticky=tk.W, padx=5, pady=2)
        
        # Logging settings
        log_frame = ttk.LabelFrame(settings_frame, text="Logging Settings", padding=10)
        log_frame.pack(fill=tk.X, padx=10, pady=5)
        
        ttk.Label(log_frame, text="Log Level:").grid(row=0, column=0, sticky=tk.W, pady=2)
        log_combo = ttk.Combobox(log_frame, textvariable=self.log_level, values=["DEBUG", "INFO", "WARNING", "ERROR"])
        log_combo.grid(row=0, column=1, sticky=tk.W, padx=5, pady=2)
        
        # Progress settings
        progress_frame = ttk.LabelFrame(settings_frame, text="Processing Settings", padding=10)
        progress_frame.pack(fill=tk.X, padx=10, pady=5)
        
        self.batch_size = tk.IntVar(value=Config.MAX_SETS_PER_BATCH)
        ttk.Label(progress_frame, text="Sets per Batch:").grid(row=0, column=0, sticky=tk.W, pady=2)
        batch_spin = ttk.Spinbox(progress_frame, from_=1, to=20, textvariable=self.batch_size, width=10)
        batch_spin.grid(row=0, column=1, sticky=tk.W, padx=5, pady=2)
        
        # Apply settings button
        ttk.Button(settings_frame, text="Apply Settings", command=self.apply_settings).pack(pady=10)
    
    def create_logs_tab(self):
        """Create logs viewing tab"""
        logs_frame = ttk.Frame(self.notebook)
        self.notebook.add(logs_frame, text="Logs")
        
        # Log display
        self.log_display = scrolledtext.ScrolledText(logs_frame, state=tk.DISABLED, font=("Courier", 9))
        self.log_display.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
        
        # Log control buttons
        log_control_frame = ttk.Frame(logs_frame)
        log_control_frame.pack(fill=tk.X, padx=10, pady=5)
        
        ttk.Button(log_control_frame, text="Clear Logs", command=self.clear_logs).pack(side=tk.LEFT, padx=5)
        ttk.Button(log_control_frame, text="Save Logs", command=self.save_logs).pack(side=tk.LEFT, padx=5)
        
        # Auto-scroll checkbox
        self.auto_scroll = tk.BooleanVar(value=True)
        ttk.Checkbutton(log_control_frame, text="Auto Scroll", variable=self.auto_scroll).pack(side=tk.RIGHT, padx=5)
    
    def create_status_bar(self):
        """Create status bar"""
        self.status_frame = ttk.Frame(self.root)
        self.status_frame.pack(fill=tk.X, side=tk.BOTTOM)
        
        self.status_label = ttk.Label(self.status_frame, text="Ready", relief=tk.SUNKEN, anchor=tk.W)
        self.status_label.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=5, pady=2)
        
        self.progress = ttk.Progressbar(self.status_frame, mode='indeterminate')
        self.progress.pack(side=tk.RIGHT, padx=5, pady=2, fill=tk.X, expand=False)
    
    def setup_logging_handler(self):
        """Setup logging to display in GUI"""
        pass
    
    def process_log_queue(self):
        """Process log messages from queue"""
        try:
            while True:
                message = self.log_queue.get_nowait()
                self.display_log_message(message)
        except queue.Empty:
            pass
        
        # Schedule next check
        self.root.after(100, self.process_log_queue)
    
    def display_log_message(self, message):
        """Display log message in the log viewer"""
        self.log_display.config(state=tk.NORMAL)
        self.log_display.insert(tk.END, message + "\n")
        
        # Auto-scroll if enabled
        if self.auto_scroll.get():
            self.log_display.see(tk.END)
        
        self.log_display.config(state=tk.DISABLED)
    
    def browse_csv_file(self):
        """Open file dialog to select CSV file"""
        filename = filedialog.askopenfilename(
            title="Select CSV File",
            filetypes=[("CSV files", "*.csv"), ("All files", "*.*")]
        )
        if filename:
            self.csv_path.set(filename)
            self.preview_data()
    
    def preview_data(self):
        """Preview CSV data"""
        if not self.csv_path.get():
            messagebox.showerror("Error", "Please select a CSV file first")
            return
        
        try:
            # Load data
            data_handler = DataHandler(self.csv_path.get())
            if not data_handler.load_csv_data():
                messagebox.showerror("Error", "Failed to load CSV data")
                return
            
            # Get data info and preview
            info = data_handler.get_data_info()
            preview = data_handler.preview_data(10)
            
            # Display in preview area
            self.data_preview.config(state=tk.NORMAL)
            self.data_preview.delete(1.0, tk.END)
            
            # Add info
            self.data_preview.insert(tk.END, f"Data Information:\n")
            self.data_preview.insert(tk.END, f"Total Sets: {info['total_sets']}\n")
            self.data_preview.insert(tk.END, f"Games per Set: {info['games_per_set']}\n")
            self.data_preview.insert(tk.END, f"Estimated Batches: {info['estimated_batches']}\n\n")
            
            # Add preview
            self.data_preview.insert(tk.END, "Data Preview (first 10 rows):\n")
            self.data_preview.insert(tk.END, "-" * 50 + "\n")
            
            for i, row in enumerate(preview):
                self.data_preview.insert(tk.END, f"Set {i+1:2d}: {', '.join(map(str, row))}\n")
            
            self.data_preview.config(state=tk.DISABLED)
            self.update_status(f"Loaded {info['total_sets']} sets from CSV")
            
        except Exception as e:
            messagebox.showerror("Error", f"Failed to preview data: {e}")
    
    def apply_settings(self):
        """Apply settings to configuration"""
        try:
            # Update Config class with GUI settings
            Config.HEADLESS_MODE = self.headless.get()
            Config.WEBDRIVER_TIMEOUT = self.timeout.get()
            Config.BROWSER = self.browser.get()
            Config.LOG_LEVEL = self.log_level.get()
            Config.MAX_SETS_PER_BATCH = self.batch_size.get()
            
            # Update logging level
            logging.getLogger().setLevel(getattr(logging, self.log_level.get()))
            
            self.update_status("Settings applied successfully")
            messagebox.showinfo("Settings", "Settings applied successfully!")
            
        except Exception as e:
            messagebox.showerror("Error", f"Failed to apply settings: {e}")
    
    def start_automation(self):
        """Start the automation process"""
        if not self.csv_path.get():
            messagebox.showerror("Error", "Please select a CSV file first")
            return
        
        if self.is_running:
            messagebox.showwarning("Warning", "Automation is already running")
            return
        
        try:
            # Apply current settings
            self.apply_settings()
            
            # Create automation system
            self.automation_system = VotingAutomationSystem(
                csv_path=self.csv_path.get(),
                url=self.url.get() if self.url.get() else None,
                headless=self.headless.get(),
                timeout=self.timeout.get()
            )
            
            # Start automation in separate thread
            self.automation_thread = threading.Thread(target=self.run_automation, daemon=True)
            self.automation_thread.start()
            
            # Update UI
            self.is_running = True
            self.start_button.config(state=tk.DISABLED)
            self.stop_button.config(state=tk.NORMAL)
            self.progress.start()
            self.update_status("Automation started")
            
        except Exception as e:
            messagebox.showerror("Error", f"Failed to start automation: {e}")
    
    def run_automation(self):
        """Run automation in separate thread"""
        try:
            success = self.automation_system.run_automation()
            
            # Update UI in main thread
            self.root.after(0, self.automation_finished, success)
            
        except Exception as e:
            self.root.after(0, self.automation_error, str(e))
    
    def automation_finished(self, success):
        """Handle automation completion"""
        self.is_running = False
        self.start_button.config(state=tk.NORMAL)
        self.stop_button.config(state=tk.DISABLED)
        self.progress.stop()
        
        if success:
            self.update_status("Automation completed successfully")
            messagebox.showinfo("Success", "Automation completed successfully!")
        else:
            self.update_status("Automation failed")
            messagebox.showerror("Error", "Automation failed. Check logs for details.")
    
    def automation_error(self, error_msg):
        """Handle automation error"""
        self.is_running = False
        self.start_button.config(state=tk.NORMAL)
        self.stop_button.config(state=tk.DISABLED)
        self.progress.stop()
        self.update_status(f"Automation error: {error_msg}")
        messagebox.showerror("Error", f"Automation error: {error_msg}")
    
    def stop_automation(self):
        """Stop the automation process"""
        if not self.is_running:
            return
        
        try:
            # This is a simple stop - in a real implementation, you'd want
            # more graceful shutdown handling
            self.is_running = False
            if self.automation_system:
                self.automation_system._cleanup()
            
            self.start_button.config(state=tk.NORMAL)
            self.stop_button.config(state=tk.DISABLED)
            self.progress.stop()
            self.update_status("Automation stopped")
            
        except Exception as e:
            messagebox.showerror("Error", f"Failed to stop automation: {e}")
    
    def take_screenshot(self):
        """Take a screenshot for debugging"""
        if not self.automation_system or not self.automation_system.webdriver_manager:
            messagebox.showwarning("Warning", "No active browser session")
            return
        
        try:
            filename = self.automation_system.take_screenshot()
            if filename:
                self.update_status(f"Screenshot saved: {filename}")
                messagebox.showinfo("Screenshot", f"Screenshot saved: {filename}")
            else:
                messagebox.showerror("Error", "Failed to take screenshot")
        except Exception as e:
            messagebox.showerror("Error", f"Screenshot error: {e}")
    
    def clear_logs(self):
        """Clear the log display"""
        self.log_display.config(state=tk.NORMAL)
        self.log_display.delete(1.0, tk.END)
        self.log_display.config(state=tk.DISABLED)
    
    def save_logs(self):
        """Save logs to file"""
        filename = filedialog.asksaveasfilename(
            title="Save Logs",
            defaultextension=".txt",
            filetypes=[("Text files", "*.txt"), ("All files", "*.*")]
        )
        if filename:
            try:
                with open(filename, 'w', encoding='utf-8') as f:
                    logs = self.log_display.get(1.0, tk.END)
                    f.write(logs)
                messagebox.showinfo("Success", f"Logs saved to {filename}")
            except Exception as e:
                messagebox.showerror("Error", f"Failed to save logs: {e}")
    
    def update_status(self, message):
        """Update status bar message"""
        self.status_label.config(text=message)
    
    def run(self):
        """Run the GUI application"""
        self.root.mainloop()

def main():
    """Main entry point for GUI application"""
    app = AutomationGUI()
    app.run()

if __name__ == "__main__":
    main()
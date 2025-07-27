"""
Enhanced GUI Application with Action Recording and Playback
"""

import tkinter as tk
from tkinter import ttk, filedialog, messagebox, scrolledtext
import threading
import queue
import logging
from pathlib import Path
import sys
import os
import json
from typing import Optional

# Import enhanced automation components
from config import Config
from data_handler import DataHandler
from enhanced_automation import EnhancedAutomationSystem, AutomationMode
from action_manager import ActionFileManager

class EnhancedAutomationGUI:
    """Enhanced GUI application with action recording and playback"""
    
    def __init__(self):
        self.root = tk.Tk()
        self.root.title("Enhanced Web Form Automation System")
        self.root.geometry("900x700")
        self.root.resizable(True, True)
        
        # Application state
        self.csv_path = tk.StringVar()
        self.action_file = tk.StringVar()
        self.url = tk.StringVar(value="https://www.toto-dream.com/toto/index.html")
        self.automation_mode = tk.StringVar(value="basic")
        self.headless = tk.BooleanVar(value=False)
        self.browser = tk.StringVar(value="chrome")
        self.timeout = tk.IntVar(value=10)
        self.log_level = tk.StringVar(value="INFO")
        self.selected_batch = tk.IntVar(value=0)
        
        # Data state
        self.data_handler = None
        self.available_batches = []
        self.batch_checkboxes = []  # For multi-batch selection
        self.current_batch_index = 0
        self.processing_all_batches = False
        
        # Enhanced automation system
        self.automation_system: Optional[EnhancedAutomationSystem] = None
        self.automation_thread: Optional[threading.Thread] = None
        self.is_running = False
        
        # Action file manager
        self.action_file_manager = ActionFileManager()
        
        # Logging setup
        self.log_queue = queue.Queue()
        self.setup_logging()
        
        # Create GUI
        self.create_widgets()
        self.setup_logging_handler()
        
        # Start log processing
        self.process_log_queue()
        
        # Load available action files
        self.refresh_action_files()
        
        # Initialize batch mode UI
        self.update_batch_mode()
    
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
        self.create_actions_tab()
        self.create_settings_tab()
        self.create_logs_tab()
        
        # Status bar
        self.create_status_bar()
    
    def create_main_tab(self):
        """Create main control tab"""
        main_frame = ttk.Frame(self.notebook)
        self.notebook.add(main_frame, text="Main")
        
        # Mode selection
        mode_frame = ttk.LabelFrame(main_frame, text="Automation Mode", padding=10)
        mode_frame.pack(fill=tk.X, padx=10, pady=5)
        
        ttk.Radiobutton(mode_frame, text="Basic Mode (Original)", 
                       variable=self.automation_mode, value="basic").pack(anchor=tk.W)
        ttk.Radiobutton(mode_frame, text="Record Mode (Record Actions)", 
                       variable=self.automation_mode, value="record").pack(anchor=tk.W)
        ttk.Radiobutton(mode_frame, text="Execute Mode (CSV + Actions)", 
                       variable=self.automation_mode, value="execute").pack(anchor=tk.W)
        
        # File selection section
        file_frame = ttk.LabelFrame(main_frame, text="File Selection", padding=10)
        file_frame.pack(fill=tk.X, padx=10, pady=5)
        
        # CSV file
        ttk.Label(file_frame, text="CSV File:").grid(row=0, column=0, sticky=tk.W, pady=2)
        ttk.Entry(file_frame, textvariable=self.csv_path, width=50).grid(row=0, column=1, padx=5, pady=2)
        ttk.Button(file_frame, text="Browse", command=self.browse_csv_file).grid(row=0, column=2, padx=5, pady=2)
        
        # Action file
        ttk.Label(file_frame, text="Action File:").grid(row=1, column=0, sticky=tk.W, pady=2)
        self.action_combo = ttk.Combobox(file_frame, textvariable=self.action_file, width=47)
        self.action_combo.grid(row=1, column=1, padx=5, pady=2)
        ttk.Button(file_frame, text="Refresh", command=self.refresh_action_files).grid(row=1, column=2, padx=5, pady=2)
        
        # Batch selection section
        batch_frame = ttk.LabelFrame(main_frame, text="Batch Selection", padding=10)
        batch_frame.pack(fill=tk.X, padx=10, pady=5)
        
        ttk.Label(batch_frame, text="Batch:").grid(row=0, column=0, sticky=tk.W, pady=2)
        self.batch_combo = ttk.Combobox(batch_frame, width=47, state="readonly")
        self.batch_combo.grid(row=0, column=1, padx=5, pady=2)
        self.batch_combo.bind('<<ComboboxSelected>>', self.on_batch_selected)
        ttk.Button(batch_frame, text="Update Batches", command=self.update_batches).grid(row=0, column=2, padx=5, pady=2)
        
        # URL section
        url_frame = ttk.LabelFrame(main_frame, text="Target URL (Optional)", padding=10)
        url_frame.pack(fill=tk.X, padx=10, pady=5)
        
        ttk.Label(url_frame, text="URL:").grid(row=0, column=0, sticky=tk.W, pady=2)
        ttk.Entry(url_frame, textvariable=self.url, width=70).grid(row=0, column=1, padx=5, pady=2)
        
        # Data preview section
        preview_frame = ttk.LabelFrame(main_frame, text="Data Preview", padding=10)
        preview_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=5)
        
        self.data_preview = scrolledtext.ScrolledText(preview_frame, height=6, state=tk.DISABLED)
        self.data_preview.pack(fill=tk.BOTH, expand=True)
        
        ttk.Button(preview_frame, text="Load & Preview Data", command=self.preview_data).pack(pady=5)
        
        # Control buttons
        control_frame = ttk.Frame(main_frame)
        control_frame.pack(fill=tk.X, padx=10, pady=10)
        
        self.start_button = ttk.Button(control_frame, text="Start Automation", command=self.start_automation)
        self.start_button.pack(side=tk.LEFT, padx=5)
        
        self.stop_button = ttk.Button(control_frame, text="Stop", command=self.stop_automation, state=tk.DISABLED)
        self.stop_button.pack(side=tk.LEFT, padx=5)
        
        # Form input control section (initially hidden)
        self.form_input_frame = ttk.LabelFrame(main_frame, text="Form Input Control", padding=10)
        
        # Voting page status
        self.voting_page_status = ttk.Label(self.form_input_frame, text="Voting page not reached", foreground="red")
        self.voting_page_status.pack(pady=5)
        
        # Batch selection mode
        batch_mode_frame = ttk.Frame(self.form_input_frame)
        batch_mode_frame.pack(fill=tk.X, pady=5)
        
        self.batch_mode = tk.StringVar(value="single")
        ttk.Radiobutton(batch_mode_frame, text="Single Batch", variable=self.batch_mode, 
                       value="single", command=self.update_batch_mode).pack(side=tk.LEFT, padx=5)
        ttk.Radiobutton(batch_mode_frame, text="All Batches", variable=self.batch_mode, 
                       value="all", command=self.update_batch_mode).pack(side=tk.LEFT, padx=5)
        
        # Single batch selection
        self.single_batch_frame = ttk.Frame(self.form_input_frame)
        self.single_batch_frame.pack(fill=tk.X, pady=5)
        
        ttk.Label(self.single_batch_frame, text="Batch to input:").pack(side=tk.LEFT, padx=5)
        self.form_input_batch_combo = ttk.Combobox(self.single_batch_frame, width=30, state="readonly")
        self.form_input_batch_combo.pack(side=tk.LEFT, padx=5)
        
        # Multiple batch selection
        self.multi_batch_frame = ttk.LabelFrame(self.form_input_frame, text="Batch Selection", padding=5)
        
        # Processing status
        self.processing_status_frame = ttk.Frame(self.form_input_frame)
        self.processing_status_frame.pack(fill=tk.X, pady=5)
        
        self.current_batch_label = ttk.Label(self.processing_status_frame, text="Ready")
        self.current_batch_label.pack(side=tk.LEFT, padx=5)
        
        self.batch_progress = ttk.Progressbar(self.processing_status_frame, mode='determinate')
        self.batch_progress.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=5)
        
        # Form input control buttons
        input_buttons_frame = ttk.Frame(self.form_input_frame)
        input_buttons_frame.pack(fill=tk.X, pady=5)
        
        self.start_form_input_button = ttk.Button(input_buttons_frame, text="Start Form Input", 
                                                 command=self.start_form_input, state=tk.DISABLED)
        self.start_form_input_button.pack(side=tk.LEFT, padx=5)
        
        self.start_all_batches_button = ttk.Button(input_buttons_frame, text="Process All Batches", 
                                                  command=self.start_all_batches, state=tk.DISABLED)
        self.start_all_batches_button.pack(side=tk.LEFT, padx=5)
        
        ttk.Button(control_frame, text="Take Screenshot", command=self.take_screenshot).pack(side=tk.RIGHT, padx=5)
    
    def create_actions_tab(self):
        """Create actions management tab"""
        actions_frame = ttk.Frame(self.notebook)
        self.notebook.add(actions_frame, text="Actions")
        
        # Action file management
        file_mgmt_frame = ttk.LabelFrame(actions_frame, text="Action File Management", padding=10)
        file_mgmt_frame.pack(fill=tk.X, padx=10, pady=5)
        
        ttk.Button(file_mgmt_frame, text="Create New Action File", 
                  command=self.create_new_action_file).pack(side=tk.LEFT, padx=5)
        ttk.Button(file_mgmt_frame, text="Load Action File", 
                  command=self.load_action_file).pack(side=tk.LEFT, padx=5)
        ttk.Button(file_mgmt_frame, text="Delete Action File", 
                  command=self.delete_action_file).pack(side=tk.LEFT, padx=5)
        
        # Action sequence viewer
        viewer_frame = ttk.LabelFrame(actions_frame, text="Action Sequence Viewer", padding=10)
        viewer_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=5)
        
        # Treeview for actions
        columns = ("Step", "Action", "Selector", "Description")
        self.actions_tree = ttk.Treeview(viewer_frame, columns=columns, show="headings", height=10)
        
        for col in columns:
            self.actions_tree.heading(col, text=col)
            self.actions_tree.column(col, width=100)
        
        scrollbar = ttk.Scrollbar(viewer_frame, orient=tk.VERTICAL, command=self.actions_tree.yview)
        self.actions_tree.configure(yscroll=scrollbar.set)
        
        self.actions_tree.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        
        # Action details
        details_frame = ttk.LabelFrame(actions_frame, text="Action Details", padding=10)
        details_frame.pack(fill=tk.X, padx=10, pady=5)
        
        self.action_details = scrolledtext.ScrolledText(details_frame, height=6, state=tk.DISABLED)
        self.action_details.pack(fill=tk.BOTH, expand=True)
    
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
        
        # Processing settings
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
    
    def refresh_action_files(self):
        """Refresh list of available action files"""
        action_files = self.action_file_manager.list_action_files()
        self.action_combo['values'] = action_files
        
        if action_files and not self.action_file.get():
            self.action_file.set(action_files[0])
    
    def create_new_action_file(self):
        """Create new action file through recording"""
        if self.is_running:
            messagebox.showwarning("Warning", "Please stop current automation first")
            return
        
        filename = filedialog.asksaveasfilename(
            title="Save Action File",
            defaultextension=".json",
            filetypes=[("JSON files", "*.json"), ("All files", "*.*")]
        )
        
        if filename:
            # Start recording mode
            self.action_file.set(Path(filename).name)
            self.automation_mode.set("record")
            messagebox.showinfo("Info", "Action file name set. Switch to Record mode and start automation to record actions.")
    
    def load_action_file(self):
        """Load and display action file contents"""
        action_file = self.action_file.get()
        if not action_file:
            messagebox.showwarning("Warning", "Please select an action file first")
            return
        
        # Load action sequence
        sequence = self.action_file_manager.load_actions(action_file)
        if not sequence:
            messagebox.showerror("Error", "Failed to load action file")
            return
        
        # Display in actions tree
        self.display_action_sequence(sequence)
    
    def delete_action_file(self):
        """Delete selected action file"""
        action_file = self.action_file.get()
        if not action_file:
            messagebox.showwarning("Warning", "Please select an action file first")
            return
        
        if messagebox.askyesno("Confirm", f"Delete action file '{action_file}'?"):
            try:
                action_path = self.action_file_manager.actions_dir / action_file
                action_path.unlink()
                self.refresh_action_files()
                messagebox.showinfo("Success", f"Action file '{action_file}' deleted")
            except Exception as e:
                messagebox.showerror("Error", f"Failed to delete action file: {e}")
    
    def display_action_sequence(self, sequence):
        """Display action sequence in the tree view"""
        # Clear existing items
        for item in self.actions_tree.get_children():
            self.actions_tree.delete(item)
        
        # Add actions to tree
        for i, action in enumerate(sequence.batch_actions, 1):
            self.actions_tree.insert("", "end", values=(
                i,
                action.action,
                action.selector or "",
                action.description or ""
            ))
        
        # Display metadata
        self.action_details.config(state=tk.NORMAL)
        self.action_details.delete(1.0, tk.END)
        
        metadata = sequence.metadata
        details = f"Action File Details:\n"
        details += f"Name: {metadata.get('name', 'Unknown')}\n"
        details += f"Description: {metadata.get('description', 'No description')}\n"
        details += f"Site URL: {metadata.get('site_url', 'Unknown')}\n"
        details += f"Total Actions: {len(sequence.batch_actions)}\n"
        details += f"Recorded At: {metadata.get('recorded_at', 'Unknown')}\n"
        
        self.action_details.insert(tk.END, details)
        self.action_details.config(state=tk.DISABLED)
    
    def preview_data(self):
        """Preview CSV data"""
        if not self.csv_path.get():
            messagebox.showerror("Error", "Please select a CSV file first")
            return
        
        try:
            # Load data
            self.data_handler = DataHandler(self.csv_path.get())
            if not self.data_handler.load_csv_data():
                messagebox.showerror("Error", "Failed to load CSV data")
                return
            
            # Split into batches and update UI
            self.available_batches = self.data_handler.split_data_into_batches()
            self.update_batch_selection()
            
            # Get data info and preview
            info = self.data_handler.get_data_info()
            preview = self.data_handler.preview_data(10)
            
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
        mode = self.automation_mode.get()
        
        # Validate requirements based on mode
        if mode in ["execute", "basic"] and not self.csv_path.get():
            messagebox.showerror("Error", "CSV file is required for execute and basic modes")
            return
        
        if mode in ["execute", "basic"] and not self.available_batches:
            messagebox.showerror("Error", "Please load CSV data and update batches first")
            return
        
        if mode == "execute" and not self.action_file.get():
            messagebox.showerror("Error", "Action file is required for execute mode")
            return
        
        if self.is_running:
            messagebox.showwarning("Warning", "Automation is already running")
            return
        
        try:
            # Apply current settings
            self.apply_settings()
            
            # Create enhanced automation system
            automation_mode = AutomationMode(mode)
            self.automation_system = EnhancedAutomationSystem(
                mode=automation_mode,
                csv_path=self.csv_path.get() if self.csv_path.get() else None,
                action_file=self.action_file.get() if self.action_file.get() else None,
                url=self.url.get() if self.url.get() else None,
                headless=self.headless.get(),
                timeout=self.timeout.get()
            )
            
            # Set batch data if available
            if mode in ["execute", "basic"] and self.available_batches:
                selected_batch_data = self.get_selected_batch_data()
                if selected_batch_data:
                    self.automation_system.set_batch_data(selected_batch_data)
            
            # Start automation in separate thread
            self.automation_thread = threading.Thread(target=self.run_automation, daemon=True)
            self.automation_thread.start()
            
            # Update UI
            self.is_running = True
            self.start_button.config(state=tk.DISABLED)
            self.stop_button.config(state=tk.NORMAL)
            self.progress.start()
            self.update_status(f"Automation started in {mode} mode")
            
            # Start checking voting page status
            if mode in ["execute", "basic"]:
                self.check_voting_page_status()
            
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
        
        # Hide form input frame and reset state
        self.form_input_frame.pack_forget()
        self.voting_page_status.config(text="Voting page not reached", foreground="red")
        self.start_form_input_button.config(state=tk.DISABLED)
        self.start_all_batches_button.config(state=tk.DISABLED)
        
        # Reset batch processing state
        self.processing_all_batches = False
        self.current_batch_index = 0
        self.current_batch_label.config(text="Ready")
        self.batch_progress['value'] = 0
        self.stop_button.config(state=tk.DISABLED)
        self.progress.stop()
        
        if success:
            self.update_status("Automation completed successfully")
            messagebox.showinfo("Success", "Automation completed successfully!")
            
            # Refresh action files in case new ones were created
            self.refresh_action_files()
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
    
    def update_batches(self):
        """Update available batches from current CSV"""
        if not self.csv_path.get():
            messagebox.showerror("Error", "Please select a CSV file first")
            return
        
        try:
            if not self.data_handler:
                self.data_handler = DataHandler(self.csv_path.get())
                if not self.data_handler.load_csv_data():
                    messagebox.showerror("Error", "Failed to load CSV data")
                    return
            
            self.available_batches = self.data_handler.split_data_into_batches()
            self.update_batch_selection()
            self.update_status(f"Updated batches: {len(self.available_batches)} available")
            
        except Exception as e:
            messagebox.showerror("Error", f"Failed to update batches: {e}")
    
    def update_batch_selection(self):
        """Update batch selection combobox"""
        if not self.available_batches:
            self.batch_combo['values'] = ["No batches available"]
            self.batch_combo.set("No batches available")
            return
        
        # Create batch options with details
        batch_options = []
        for i, batch in enumerate(self.available_batches):
            batch_info = f"Batch {i+1} ({len(batch)} sets)"
            batch_options.append(batch_info)
        
        self.batch_combo['values'] = batch_options
        self.batch_combo.set(batch_options[0])
        self.selected_batch.set(0)  # Reset to first batch
    
    def on_batch_selected(self, event):
        """Handle batch selection change"""
        selected_text = self.batch_combo.get()
        if selected_text and "Batch" in selected_text:
            # Extract batch number from text like "Batch 1 (10 sets)"
            try:
                batch_num = int(selected_text.split()[1]) - 1  # Convert to 0-based index
                self.selected_batch.set(batch_num)
                self.update_status(f"Selected {selected_text}")
            except (IndexError, ValueError):
                pass
    
    def get_selected_batch_data(self):
        """Get the currently selected batch data"""
        if not self.available_batches or self.selected_batch.get() >= len(self.available_batches):
            return None
        return self.available_batches[self.selected_batch.get()]
    
    def start_form_input(self):
        """Start form input with selected batch"""
        if not self.automation_system:
            messagebox.showerror("Error", "No automation system running")
            return
        
        if not self.automation_system.is_voting_page_ready():
            messagebox.showerror("Error", "Voting page not ready")
            return
        
        # Get selected batch for form input
        selected_batch_text = self.form_input_batch_combo.get()
        if not selected_batch_text or "Batch" not in selected_batch_text:
            messagebox.showerror("Error", "Please select a batch to input")
            return
        
        try:
            # Extract batch index
            batch_num = int(selected_batch_text.split()[1]) - 1
            if batch_num >= len(self.available_batches):
                messagebox.showerror("Error", "Invalid batch selection")
                return
            
            # Set the selected batch data
            selected_batch_data = self.available_batches[batch_num]
            self.automation_system.set_batch_data(selected_batch_data)
            
            # Authorize form input
            self.automation_system.start_form_input()
            
            # Update UI
            self.start_form_input_button.config(state=tk.DISABLED)
            self.update_status(f"Form input started with {selected_batch_text}")
            
        except (IndexError, ValueError) as e:
            messagebox.showerror("Error", f"Failed to start form input: {e}")
    
    def check_voting_page_status(self):
        """Check and update voting page status"""
        if self.automation_system and self.automation_system.is_voting_page_ready():
            self.voting_page_status.config(text="✅ Voting page ready", foreground="green")
            self.form_input_frame.pack(fill=tk.X, padx=10, pady=5)
            
            # Update batch mode UI
            self.update_batch_mode()
            
            # Update form input batch combo
            if self.available_batches:
                batch_options = []
                for i, batch in enumerate(self.available_batches):
                    batch_info = f"Batch {i+1} ({len(batch)} sets)"
                    batch_options.append(batch_info)
                self.form_input_batch_combo['values'] = batch_options
                if batch_options:
                    self.form_input_batch_combo.set(batch_options[0])
        
        # Schedule next check
        if self.is_running:
            self.root.after(1000, self.check_voting_page_status)
    
    def update_batch_mode(self):
        """Update UI based on selected batch mode"""
        # Check if UI elements exist
        if not hasattr(self, 'single_batch_frame') or not hasattr(self, 'multi_batch_frame'):
            return
        
        mode = self.batch_mode.get()
        
        if mode == "single":
            self.single_batch_frame.pack(fill=tk.X, pady=5)
            self.multi_batch_frame.pack_forget()
            if hasattr(self, 'start_form_input_button'):
                self.start_form_input_button.config(state=tk.NORMAL if self.automation_system and self.automation_system.is_voting_page_ready() else tk.DISABLED)
            if hasattr(self, 'start_all_batches_button'):
                self.start_all_batches_button.config(state=tk.DISABLED)
        elif mode == "all":
            self.single_batch_frame.pack_forget()
            self.setup_multi_batch_selection()
            self.multi_batch_frame.pack(fill=tk.X, pady=5)
            if hasattr(self, 'start_form_input_button'):
                self.start_form_input_button.config(state=tk.DISABLED)
            if hasattr(self, 'start_all_batches_button'):
                self.start_all_batches_button.config(state=tk.NORMAL if self.automation_system and self.automation_system.is_voting_page_ready() else tk.DISABLED)
    
    def setup_multi_batch_selection(self):
        """Setup multiple batch selection UI"""
        # Clear existing checkboxes
        for widget in self.multi_batch_frame.winfo_children():
            widget.destroy()
        self.batch_checkboxes.clear()
        
        if not self.available_batches:
            ttk.Label(self.multi_batch_frame, text="No batches available").pack()
            return
        
        ttk.Label(self.multi_batch_frame, text="Select batches to process:").pack(anchor=tk.W, pady=2)
        
        # Add "Select All" checkbox
        select_all_var = tk.BooleanVar()
        select_all_cb = ttk.Checkbutton(self.multi_batch_frame, text="Select All", 
                                       variable=select_all_var, command=lambda: self.toggle_all_batches(select_all_var.get()))
        select_all_cb.pack(anchor=tk.W, pady=2)
        
        # Add individual batch checkboxes
        for i, batch in enumerate(self.available_batches):
            var = tk.BooleanVar(value=True)  # Default to selected
            text = f"Batch {i+1} ({len(batch)} sets)"
            cb = ttk.Checkbutton(self.multi_batch_frame, text=text, variable=var)
            cb.pack(anchor=tk.W, padx=20, pady=1)
            self.batch_checkboxes.append(var)
    
    def toggle_all_batches(self, select_all: bool):
        """Toggle all batch checkboxes"""
        for var in self.batch_checkboxes:
            var.set(select_all)
    
    def start_all_batches(self):
        """Start processing all selected batches"""
        if not self.automation_system or not self.automation_system.is_voting_page_ready():
            messagebox.showerror("Error", "Voting page not ready")
            return
        
        # Get selected batches
        selected_batches = []
        for i, var in enumerate(self.batch_checkboxes):
            if var.get():
                selected_batches.append(i)
        
        if not selected_batches:
            messagebox.showerror("Error", "Please select at least one batch")
            return
        
        # Start processing
        self.processing_all_batches = True
        self.current_batch_index = 0
        self.selected_batch_indices = selected_batches
        
        # Update UI
        self.start_all_batches_button.config(state=tk.DISABLED)
        self.batch_progress['maximum'] = len(selected_batches)
        self.batch_progress['value'] = 0
        
        # Start with first batch
        self.process_next_batch()
    
    def process_next_batch(self):
        """Process the next batch in the sequence"""
        if not self.processing_all_batches or self.current_batch_index >= len(self.selected_batch_indices):
            self.complete_all_batches_processing()
            return
        
        try:
            # Get current batch to process
            batch_index = self.selected_batch_indices[self.current_batch_index]
            batch_data = self.available_batches[batch_index]
            
            # Update UI
            self.current_batch_label.config(text=f"Processing Batch {batch_index + 1} ({len(batch_data)} sets)")
            self.batch_progress['value'] = self.current_batch_index
            
            # Set batch data and start processing
            self.automation_system.set_batch_data(batch_data)
            self.automation_system.start_form_input()
            
            self.update_status(f"Processing batch {batch_index + 1}/{len(self.available_batches)}")
            
            # Schedule next batch processing (with delay for current batch to complete)
            self.root.after(5000, self.check_current_batch_completion)
            
        except Exception as e:
            messagebox.showerror("Error", f"Failed to process batch: {e}")
            self.complete_all_batches_processing()
    
    def check_current_batch_completion(self):
        """Check if current batch processing is complete"""
        # This is a simplified check - in a real implementation, you'd want to 
        # monitor the automation system's state more carefully
        if self.automation_system and not self.automation_system.form_input_ready:
            # Current batch might be complete, move to next
            self.current_batch_index += 1
            self.process_next_batch()
        else:
            # Still processing, check again later
            self.root.after(2000, self.check_current_batch_completion)
    
    def complete_all_batches_processing(self):
        """Complete all batches processing"""
        self.processing_all_batches = False
        self.current_batch_label.config(text="All batches completed")
        self.batch_progress['value'] = self.batch_progress['maximum']
        self.start_all_batches_button.config(state=tk.NORMAL)
        self.update_status("All selected batches processed successfully")
    
    def update_status(self, message):
        """Update status bar message"""
        self.status_label.config(text=message)
    
    def run(self):
        """Run the GUI application"""
        self.root.mainloop()

def main():
    """Main entry point for enhanced GUI application"""
    app = EnhancedAutomationGUI()
    app.run()

if __name__ == "__main__":
    main()
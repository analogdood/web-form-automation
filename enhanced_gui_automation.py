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

# Try to import selenium-dependent components
try:
    from enhanced_automation import EnhancedAutomationSystem, AutomationMode
    from action_manager import ActionFileManager
    from toto_round_selector import TotoRoundSelector
    from complete_toto_automation import CompleteTotoAutomation
    SELENIUM_AVAILABLE = True
except ImportError as e:
    print(f"⚠️ Selenium components not available: {e}")
    print("📝 GUI will run in limited mode (data preview only)")
    SELENIUM_AVAILABLE = False
    
    # Define dummy classes to prevent errors
    class EnhancedAutomationSystem:
        pass
    class AutomationMode:
        BASIC = "basic"
        RECORD = "record"
        EXECUTE = "execute"
    class ActionFileManager:
        def __init__(self):
            self.actions_dir = Path("actions")
        def list_action_files(self):
            return []
    class TotoRoundSelector:
        def __init__(self, driver=None):
            pass
        def select_round_by_number(self, rounds, round_number):
            return False
        def navigate_to_start_page(self, url: str):
            return False
        def detect_toto_rounds(self):
            return []
        def click_voting_prediction_button(self):
            return False
        def click_single_button(self):
            return False
    class CompleteTotoAutomation:
        pass

class EnhancedAutomationGUI:
    """Enhanced GUI application with action recording and playback"""
    
    def __init__(self):
        self.root = tk.Tk()
        self.root.title("Enhanced Web Form Automation System")
        self.root.geometry("950x800")
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
        
        # Error recovery settings
        self.max_retries = tk.IntVar(value=3)
        self.retry_delay = tk.IntVar(value=5)
        self.error_recovery_enabled = tk.BooleanVar(value=True)
        
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
        
        # Toto round selector
        self.round_selector: Optional[TotoRoundSelector] = None
        self.available_rounds = []
        
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
        self.notebook.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)
        
        # Create tabs
        self.create_main_tab()
        self.create_actions_tab()
        self.create_settings_tab()
        self.create_logs_tab()
        
        # Status bar
        self.create_status_bar()
        
        # Configure widgets based on selenium availability
        self.configure_selenium_widgets()
    
    def create_main_tab(self):
        """Create main control tab"""
        main_frame = ttk.Frame(self.notebook)
        self.notebook.add(main_frame, text="Main")
        
        # Mode selection
        mode_frame = ttk.LabelFrame(main_frame, text="Automation Mode", padding=5)
        mode_frame.pack(fill=tk.X, padx=5, pady=3)
        
        ttk.Radiobutton(mode_frame, text="Basic Mode (Original)", 
                       variable=self.automation_mode, value="basic").pack(anchor=tk.W)
        ttk.Radiobutton(mode_frame, text="Record Mode (Record Actions)", 
                       variable=self.automation_mode, value="record").pack(anchor=tk.W)
        ttk.Radiobutton(mode_frame, text="Execute Mode (CSV + Actions)", 
                       variable=self.automation_mode, value="execute").pack(anchor=tk.W)
        
        # File selection section
        file_frame = ttk.LabelFrame(main_frame, text="File Selection", padding=5)
        file_frame.pack(fill=tk.X, padx=5, pady=3)
        
        # CSV file
        ttk.Label(file_frame, text="CSV File:").grid(row=0, column=0, sticky=tk.W, pady=2)
        ttk.Entry(file_frame, textvariable=self.csv_path, width=50).grid(row=0, column=1, padx=5, pady=2)
        ttk.Button(file_frame, text="Browse", command=self.browse_csv_file).grid(row=0, column=2, padx=5, pady=2)
        
        # Action file
        ttk.Label(file_frame, text="Action File:").grid(row=1, column=0, sticky=tk.W, pady=2)
        self.action_combo = ttk.Combobox(file_frame, textvariable=self.action_file, width=47)
        self.action_combo.grid(row=1, column=1, padx=5, pady=2)
        ttk.Button(file_frame, text="Refresh", command=self.refresh_action_files).grid(row=1, column=2, padx=5, pady=2)
        
        # Toto round selection section
        round_frame = ttk.LabelFrame(main_frame, text="Toto Round Selection", padding=5)
        round_frame.pack(fill=tk.X, padx=5, pady=3)
        
        ttk.Label(round_frame, text="Round:").grid(row=0, column=0, sticky=tk.W, pady=2)
        self.round_combo = ttk.Combobox(round_frame, width=35, state="readonly")
        self.round_combo.grid(row=0, column=1, padx=5, pady=2)
        ttk.Button(round_frame, text="Detect", command=self.detect_toto_rounds).grid(row=0, column=2, padx=2, pady=2)
        ttk.Button(round_frame, text="Select", command=self.select_toto_round).grid(row=0, column=3, padx=2, pady=2)
        
        # Navigation buttons
        nav_buttons_frame = ttk.Frame(round_frame)
        nav_buttons_frame.grid(row=2, column=0, columnspan=4, pady=5)
        
        ttk.Button(nav_buttons_frame, text="Start Voting Prediction", 
                  command=self.click_voting_prediction).pack(side=tk.LEFT, padx=5)
        ttk.Button(nav_buttons_frame, text="Click Single", 
                  command=self.click_single_button).pack(side=tk.LEFT, padx=5)
        ttk.Button(nav_buttons_frame, text="Auto Navigation", 
                  command=self.auto_navigate_to_voting).pack(side=tk.LEFT, padx=5)
        
        # Round status
        self.round_status = ttk.Label(round_frame, text="No round selected", foreground="orange")
        self.round_status.grid(row=1, column=0, columnspan=3, pady=2)
        
        # Batch selection section
        batch_frame = ttk.LabelFrame(main_frame, text="Batch Selection", padding=5)
        batch_frame.pack(fill=tk.X, padx=5, pady=3)
        
        ttk.Label(batch_frame, text="Batch:").grid(row=0, column=0, sticky=tk.W, pady=2)
        self.batch_combo = ttk.Combobox(batch_frame, width=47, state="readonly")
        self.batch_combo.grid(row=0, column=1, padx=5, pady=2)
        self.batch_combo.bind('<<ComboboxSelected>>', self.on_batch_selected)
        ttk.Button(batch_frame, text="Update Batches", command=self.update_batches).grid(row=0, column=2, padx=5, pady=2)
        
        # URL section (hidden by default to save space - already set in config)
        # url_frame = ttk.LabelFrame(main_frame, text="Target URL (Optional)", padding=5)
        # url_frame.pack(fill=tk.X, padx=5, pady=3)
        # 
        # ttk.Label(url_frame, text="URL:").grid(row=0, column=0, sticky=tk.W, pady=2)
        # ttk.Entry(url_frame, textvariable=self.url, width=70).grid(row=0, column=1, padx=5, pady=2)
        
        # Data preview section
        preview_frame = ttk.LabelFrame(main_frame, text="Data Preview", padding=5)
        preview_frame.pack(fill=tk.X, padx=5, pady=3)
        
        self.data_preview = scrolledtext.ScrolledText(preview_frame, height=3, state=tk.DISABLED)
        self.data_preview.pack(fill=tk.X)
        
        ttk.Button(preview_frame, text="Load Data", command=self.preview_data).pack(pady=3)
        
        # Control buttons
        control_frame = ttk.Frame(main_frame)
        control_frame.pack(fill=tk.X, padx=5, pady=5)
        
        self.start_button = ttk.Button(control_frame, text="Start Automation", command=self.start_automation)
        self.start_button.pack(side=tk.LEFT, padx=5)
        
        self.complete_workflow_button = ttk.Button(control_frame, text="Complete Workflow", 
                                                  command=self.start_complete_workflow)
        self.complete_workflow_button.pack(side=tk.LEFT, padx=5)
        
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
        self.form_input_batch_combo.bind('<<ComboboxSelected>>', self.on_batch_selection_changed)
        
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
        
        # Error recovery settings
        recovery_frame = ttk.LabelFrame(settings_frame, text="Error Recovery Settings", padding=10)
        recovery_frame.pack(fill=tk.X, padx=10, pady=5)
        
        ttk.Checkbutton(recovery_frame, text="Enable Error Recovery", variable=self.error_recovery_enabled).grid(row=0, column=0, columnspan=2, sticky=tk.W, pady=2)
        
        ttk.Label(recovery_frame, text="Max Retries:").grid(row=1, column=0, sticky=tk.W, pady=2)
        retry_spin = ttk.Spinbox(recovery_frame, from_=1, to=10, textvariable=self.max_retries, width=10)
        retry_spin.grid(row=1, column=1, sticky=tk.W, padx=5, pady=2)
        
        ttk.Label(recovery_frame, text="Retry Delay (seconds):").grid(row=2, column=0, sticky=tk.W, pady=2)
        delay_spin = ttk.Spinbox(recovery_frame, from_=1, to=30, textvariable=self.retry_delay, width=10)
        delay_spin.grid(row=2, column=1, sticky=tk.W, padx=5, pady=2)
        
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
        
        # Add workflow progress label
        self.workflow_progress = ttk.Label(self.status_frame, text="", relief=tk.SUNKEN, anchor=tk.CENTER, width=25)
        self.workflow_progress.pack(side=tk.RIGHT, padx=5, pady=2)
        
        self.progress = ttk.Progressbar(self.status_frame, mode='determinate', length=200)
        self.progress.pack(side=tk.RIGHT, padx=5, pady=2)
    
    def configure_selenium_widgets(self):
        """Configure widgets based on selenium availability"""
        if not SELENIUM_AVAILABLE:
            # Disable automation-related buttons
            if hasattr(self, 'start_button'):
                self.start_button.config(state=tk.DISABLED)
            if hasattr(self, 'complete_workflow_button'):
                self.complete_workflow_button.config(state=tk.DISABLED)
            if hasattr(self, 'stop_button'):
                self.stop_button.config(state=tk.DISABLED)
            
            # Update status
            if hasattr(self, 'status_label'):
                self.status_label.config(text="Ready (Selenium not available - limited mode)")
                
            # Show warning in round status if exists
            if hasattr(self, 'round_status'):
                self.round_status.config(text="Selenium required for automation", foreground="red")
        else:
            # Update status for full functionality
            if hasattr(self, 'status_label'):
                self.status_label.config(text="Ready (Full automation available)")
    
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
            
            # Show round number detection info after CSV selection
            round_number = self._extract_round_number_from_csv_filename()
            if round_number:
                self.update_status(f"CSV selected with round number {round_number} detected from filename")
                # Update round status to show detected round
                if hasattr(self, 'round_status'):
                    self.round_status.config(text=f"🔍 Detected round {round_number} from CSV filename", foreground="blue")
            else:
                self.update_status("CSV selected - no round number detected in filename")
                if hasattr(self, 'round_status'):
                    self.round_status.config(text="No round number detected in CSV filename", foreground="gray")
    
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
            
            # Apply error recovery settings to automation system if it exists
            if self.automation_system:
                self.automation_system.max_retries = self.max_retries.get()
                self.automation_system.retry_delay = self.retry_delay.get()
                self.automation_system.error_recovery_enabled = self.error_recovery_enabled.get()
            
            # Update logging level
            logging.getLogger().setLevel(getattr(logging, self.log_level.get()))
            
            self.update_status("Settings applied successfully")
            messagebox.showinfo("Settings", "Settings applied successfully!")
            
        except Exception as e:
            messagebox.showerror("Error", f"Failed to apply settings: {e}")
    
    def start_automation(self):
        """Start the automation process"""
        if not SELENIUM_AVAILABLE:
            messagebox.showerror("Error", "Selenium not available. Please install selenium to use automation features.")
            return
            
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
                # Don't automatically set to first batch - let user choose
                if not self.form_input_batch_combo.get():
                    self.form_input_batch_combo.set("")
        
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
                # Enable button only if a batch is selected and voting page is ready
                batch_selected = hasattr(self, 'form_input_batch_combo') and self.form_input_batch_combo.get()
                page_ready = self.automation_system and self.automation_system.is_voting_page_ready()
                self.start_form_input_button.config(state=tk.NORMAL if batch_selected and page_ready else tk.DISABLED)
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
    
    def on_batch_selection_changed(self, event):
        """Handle batch selection change in single batch mode"""
        self.update_batch_mode()
    
    def detect_toto_rounds(self):
        """Detect available toto rounds from the start page"""
        try:
            if not self.automation_system:
                messagebox.showerror("Error", "Please start automation system first")
                return
            
            # Initialize round selector if not exists
            if not self.round_selector:
                self.round_selector = TotoRoundSelector(self.automation_system.webdriver_manager.driver)
            
            # Navigate to start page
            if not self.round_selector.navigate_to_start_page(Config.START_URL):
                messagebox.showerror("Error", "Failed to navigate to start page")
                return
            
            # Detect rounds
            self.available_rounds = self.round_selector.detect_toto_rounds()
            
            if not self.available_rounds:
                messagebox.showwarning("Warning", "No toto rounds found on the page")
                self.round_status.config(text="No rounds found", foreground="red")
                return
            
            # Update GUI
            round_options = []
            for round_info in self.available_rounds:
                round_text = f"{round_info['text']} (第{round_info['round_number']}回)"
                round_options.append(round_text)
            
            self.round_combo['values'] = round_options
            if round_options:
                self.round_combo.set(round_options[0])  # Select first round by default
            
            self.round_status.config(text=f"Found {len(self.available_rounds)} rounds", foreground="green")
            self.update_status(f"Detected {len(self.available_rounds)} toto rounds")
            
        except Exception as e:
            messagebox.showerror("Error", f"Failed to detect rounds: {e}")
            self.round_status.config(text="Detection failed", foreground="red")
    
    def select_toto_round(self):
        """Select the chosen toto round"""
        try:
            if not self.available_rounds:
                messagebox.showerror("Error", "No rounds detected. Please detect rounds first.")
                return
            
            if not self.round_combo.get():
                messagebox.showerror("Error", "Please select a round")
                return
            
            # Get selected round index
            selected_index = self.round_combo.current()
            if selected_index < 0 or selected_index >= len(self.available_rounds):
                messagebox.showerror("Error", "Invalid round selection")
                return
            
            selected_round = self.available_rounds[selected_index]
            
            # Click on the selected round
            if self.round_selector.select_round_by_number(self.available_rounds, selected_round['round_number']):
                self.round_status.config(text=f"Selected: {selected_round['text']}", foreground="blue")
                self.update_status(f"Selected round: {selected_round['text']}")
                messagebox.showinfo("Success", f"Successfully selected {selected_round['text']}")
            else:
                messagebox.showerror("Error", f"Failed to select {selected_round['text']}")
                
        except Exception as e:
            messagebox.showerror("Error", f"Failed to select round: {e}")
    
    def click_voting_prediction(self):
        """Click the '今すぐ投票予想する' button (automatically clicks 'シングル' too)"""
        try:
            if not self.automation_system:
                messagebox.showerror("Error", "Please start automation system first")
                return
            
            if not self.round_selector:
                messagebox.showerror("Error", "Round selector not initialized. Please detect rounds first.")
                return
            
            # Click the voting prediction button (now automatically clicks single too)
            if self.round_selector.click_voting_prediction_button():
                self.round_status.config(text="Navigated to single voting page", foreground="green")
                self.update_status("Successfully clicked '今すぐ投票予想する' and 'シングル' buttons")
                messagebox.showinfo("Success", "Successfully navigated to single voting page!\n(Automatically clicked both '今すぐ投票予想する' and 'シングル' buttons)")
            else:
                messagebox.showerror("Error", "Failed to complete voting prediction and single button sequence")
                
        except Exception as e:
            messagebox.showerror("Error", f"Failed to click voting prediction button: {e}")
    
    def click_single_button(self):
        """Click the 'シングル' button to go to single voting page"""
        try:
            if not self.automation_system:
                messagebox.showerror("Error", "Please start automation system first")
                return
            
            if not self.round_selector:
                messagebox.showerror("Error", "Round selector not initialized. Please detect rounds first.")
                return
            
            # Click the single button
            if self.round_selector.click_single_button():
                self.round_status.config(text="Navigated to single voting page", foreground="green")
                self.update_status("Successfully clicked 'シングル' button")
                messagebox.showinfo("Success", "Successfully navigated to single voting page!")
            else:
                messagebox.showerror("Error", "Failed to click 'シングル' button")
                
        except Exception as e:
            messagebox.showerror("Error", f"Failed to click single button: {e}")
    
    def auto_navigate_to_voting(self):
        """Automatically navigate through the complete flow to single voting page"""
        try:
            if not self.automation_system:
                messagebox.showerror("Error", "Please start automation system first")
                return
            
            # Initialize round selector if not exists
            if not self.round_selector:
                self.round_selector = TotoRoundSelector(self.automation_system.webdriver_manager.driver)
            
            # Show progress dialog
            self.update_status("Starting auto navigation to single voting page...")
            
            # Execute complete navigation flow
            if self.round_selector.navigate_to_voting_prediction():
                # Update GUI state
                self.round_status.config(text="Auto navigation completed", foreground="green")
                self.update_status("Auto navigation to single voting page completed successfully")
                
                # Try to update round combo if rounds were detected
                try:
                    selected_info = self.round_selector.get_selected_round_info()
                    if selected_info:
                        round_text = f"{selected_info['round_text']} (第{selected_info['round_number']}回)"
                        self.round_combo.set(round_text)
                except:
                    pass  # Ignore errors in GUI update
                
                messagebox.showinfo("Success", "Auto navigation completed successfully!\nYou should now be on the single voting page and ready for form filling.")
            else:
                messagebox.showerror("Error", "Auto navigation failed. Check the logs for details.")
                self.round_status.config(text="Auto navigation failed", foreground="red")
                
        except Exception as e:
            messagebox.showerror("Error", f"Auto navigation failed: {e}")
            self.round_status.config(text="Auto navigation error", foreground="red")
    
    def start_complete_workflow(self):
        """Start the complete end-to-end toto automation workflow"""
        if not SELENIUM_AVAILABLE:
            messagebox.showerror("Error", "Selenium not available. Please install selenium to use automation features.")
            return
            
        try:
            # Validate inputs
            if not self.csv_path.get():
                messagebox.showerror("Error", "Please select a CSV file first")
                return
            
            if not Path(self.csv_path.get()).exists():
                messagebox.showerror("Error", f"CSV file not found: {self.csv_path.get()}")
                return
            
            # Check if CSV filename contains round number for smart confirmation
            csv_round_number = self._extract_round_number_from_csv_filename()
            
            if csv_round_number:
                # Simplified confirmation for CSV with round number
                result = messagebox.askyesno(
                    "Complete Workflow", 
                    f"🎯 CSV filename contains round {csv_round_number}!\n\n"
                    f"Complete workflow will:\n"
                    f"• Auto-select round {csv_round_number} if available\n"
                    f"• Process all batches automatically\n"
                    f"• Add items to cart\n\n"
                    f"Continue with smart automation?",
                    icon='question'
                )
            else:
                # Standard confirmation for regular CSV files
                result = messagebox.askyesno(
                    "Complete Workflow", 
                    "This will run the complete automation workflow:\n\n"
                    "1. Navigate to toto site\n"
                    "2. Detect available rounds\n"
                    "3. Wait for you to select round\n"
                    "4. Fill betting forms automatically\n"
                    "5. Add all batches to cart\n\n"
                    "Continue?",
                    icon='question'
                )
            
            if not result:
                return
            
            # Get selected round number (if any)
            round_number = None
            if self.round_combo.get():
                try:
                    # Extract round number from selection like "第1558回 (第1558回)"
                    import re
                    match = re.search(r'第(\d+)回', self.round_combo.get())
                    if match:
                        round_number = match.group(1)
                except:
                    pass  # Use auto-selection if parsing fails
            
            # Disable UI during processing
            self.complete_workflow_button.config(state=tk.DISABLED)
            self.start_button.config(state=tk.DISABLED)
            self.update_workflow_progress('init', 0)
            self.update_status("Complete Workflow開始...")
            
            # Start workflow in background thread using existing automation system
            def run_complete_workflow():
                try:
                    # Initialize automation system if not exists
                    if not self.automation_system:
                        self.automation_system = EnhancedAutomationSystem(
                            mode=AutomationMode.BASIC,
                            csv_path=self.csv_path.get(),
                            headless=self.headless.get(),
                            timeout=self.timeout.get()
                        )
                    else:
                        # Clear any existing batch_data to ensure multi-batch processing
                        self.automation_system.batch_data = None
                        print("🔧 Cleared existing batch_data to ensure multi-batch processing")
                    
                    # Set up progress callback for real-time updates
                    def progress_callback(current_batch, total_batches, current_set, total_sets, stage):
                        # Update GUI from main thread
                        self.root.after(0, lambda: self.update_batch_progress_detailed(
                            current_batch, total_batches, current_set, total_sets, stage))
                    
                    self.automation_system.set_progress_callback(progress_callback)
                    
                    # Apply error recovery settings
                    self.automation_system.max_retries = self.max_retries.get()
                    self.automation_system.retry_delay = self.retry_delay.get() 
                    self.automation_system.error_recovery_enabled = self.error_recovery_enabled.get()
                    
                    # Setup webdriver if needed
                    if not self.automation_system._setup_webdriver():
                        raise Exception("Failed to setup webdriver")
                    
                    # Load CSV data
                    if not self.automation_system._load_data():
                        raise Exception("Failed to load CSV data")
                    
                    # Initialize round selector if not exists
                    if not self.round_selector:
                        self.round_selector = TotoRoundSelector(self.automation_system.webdriver_manager.driver)
                        self.automation_system.round_selector = self.round_selector
                    
                    # Step 1: Navigate to start page and detect rounds
                    self.root.after(0, lambda: self.update_workflow_progress('detecting_rounds', 10))
                    if not self.round_selector.navigate_to_start_page("https://www.toto-dream.com/toto/index.html"):
                        raise Exception("Failed to navigate to start page")
                    
                    self.root.after(0, lambda: self.update_workflow_progress('detecting_rounds', 20))
                    rounds = self.round_selector.detect_toto_rounds()
                    if not rounds:
                        raise Exception("No rounds detected")
                    
                    # Update GUI with detected rounds and wait for user selection
                    self.root.after(0, lambda: self.update_workflow_progress('round_selection', 30))
                    self.root.after(0, self._update_rounds_and_wait, rounds)
                    return  # Exit thread, continue after user selection
                    
                except Exception as e:
                    self.root.after(0, self._complete_workflow_error, str(e))
            
            # Continue workflow after round selection
            def continue_workflow_after_round_selection():
                try:
                    # Execute navigation to voting page with selected round
                    self.root.after(0, lambda: self.update_workflow_progress('voting_page', 50))
                    if not self.round_selector.click_voting_prediction_button():
                        raise Exception("Failed to click voting prediction button")
                    
                    # Execute batch processing using enhanced automation system
                    self.root.after(0, lambda: self.update_workflow_progress('batch_processing', 60))
                    success = self.automation_system._process_data_batches()
                    
                    # Get stats from automation system
                    stats = self.automation_system.processing_stats
                    
                    # Update UI from main thread
                    self.root.after(0, self._complete_workflow_finished, success, stats)
                    
                except Exception as e:
                    self.root.after(0, self._complete_workflow_error, str(e))
            
            # Store the continuation function for later use
            self.continue_workflow_function = continue_workflow_after_round_selection
            
            # Start background thread
            workflow_thread = threading.Thread(target=run_complete_workflow, daemon=True)
            workflow_thread.start()
            
        except Exception as e:
            messagebox.showerror("Error", f"Failed to start complete workflow: {e}")
            self.complete_workflow_button.config(state=tk.NORMAL)
            self.start_button.config(state=tk.NORMAL)
    
    def _complete_workflow_finished(self, success: bool, stats: dict):
        """Handle completion of complete workflow"""
        try:
            # Re-enable UI
            self.complete_workflow_button.config(state=tk.NORMAL)
            self.start_button.config(state=tk.NORMAL)
            
            if success:
                # Show success message
                # Build success message with recovery stats
                duration = stats.get('end_time', 0) - stats.get('start_time', 0)
                message_parts = [
                    f"🎉 Complete Workflow Successful! 🎉\n",
                    f"✅ Successful Batches: {stats.get('successful_batches', 0)}",
                    f"❌ Failed Batches: {stats.get('failed_batches', 0)}",
                    f"📊 Total Sets: {stats.get('total_sets', 0)}",
                    f"⏱️ Duration: {duration:.1f}s"
                ]
                
                # Add recovery stats if there were any retries
                if stats.get('retry_attempts', 0) > 0:
                    message_parts.extend([
                        f"",
                        f"🚑 Error Recovery Stats:",
                        f"🔄 Retry Attempts: {stats.get('retry_attempts', 0)}",
                        f"✅ Recovered Errors: {stats.get('recovered_errors', 0)}"
                    ])
                
                message_parts.extend([
                    f"",
                    f"🛒 All items added to cart!",
                    f"💳 Ready for checkout!"
                ])
                
                message = "\n".join(message_parts)
                
                messagebox.showinfo("Success", message)
                self.update_workflow_progress('completion', 100)
                self.update_status("Complete workflow finished successfully!")
                
                # Update round status if we have round info
                if stats.get('successful_batches', 0) > 0:
                    self.round_status.config(text="Workflow completed successfully", foreground="green")
                
            else:
                messagebox.showerror("Error", 
                    f"Complete workflow failed!\n\n"
                    f"Successfully processed: {stats.get('successful_batches', 0)} batches\n"
                    f"Failed: {stats.get('failed_batches', 0)} batches\n\n"
                    f"Check the logs for details.")
                self.update_workflow_progress('error', 0)
                self.update_status("Complete workflow failed")
                self.round_status.config(text="Workflow failed", foreground="red")
                
        except Exception as e:
            messagebox.showerror("Error", f"Error handling workflow completion: {e}")
    
    def _complete_workflow_error(self, error_message: str):
        """Handle error in complete workflow"""
        self.complete_workflow_button.config(state=tk.NORMAL)
        self.start_button.config(state=tk.NORMAL)
        self.update_workflow_progress('error', 0)
        messagebox.showerror("Error", f"Complete workflow error: {error_message}")
        self.update_status("Complete workflow error")
    
    def _extract_round_number_from_csv_filename(self):
        """Extract 4-digit round number from CSV filename"""
        if not self.csv_path.get():
            return None
        
        try:
            import re
            from pathlib import Path
            
            filename = Path(self.csv_path.get()).name
            print(f"🔍 Extracting round number from filename: {filename}")
            
            # Search for 4-digit numbers in filename (like X-1558.csv or data-1558.csv)
            match = re.search(r'(\d{4})', filename)
            if match:
                round_number = match.group(1)
                print(f"✅ Found round number in filename: {round_number}")
                return round_number
            else:
                print("❌ No 4-digit round number found in filename")
                return None
                
        except Exception as e:
            print(f"Failed to extract round number from filename: {e}")
            return None

    def _update_rounds_and_wait(self, rounds):
        """Update GUI with detected rounds and wait for user selection"""
        try:
            # Filter out minitoto rounds automatically
            valid_rounds = []
            minitoto_count = 0
            
            for round_info in rounds:
                round_text = round_info['text']
                # Check if it's minitoto (contains 'mini' or specific patterns)
                if 'mini' in round_text.lower() or 'ミニ' in round_text:
                    minitoto_count += 1
                    continue
                valid_rounds.append(round_info)
            
            # Try to extract round number from CSV filename first
            csv_round_number = self._extract_round_number_from_csv_filename()
            
            # Update round combo box with filtered rounds
            round_options = []
            recommended_round = None
            csv_matched_round = None
            
            for round_info in valid_rounds:
                round_text = round_info['text']
                round_options.append(round_text)
                
                # Check if this round matches the CSV filename
                if csv_round_number:
                    if csv_round_number in round_text:
                        csv_matched_round = (round_text, round_info['round_number'])
                        print(f"🎯 Found matching round for CSV filename: {round_text}")
                
                # Find the latest/highest round number as fallback recommended
                try:
                    import re
                    match = re.search(r'第(\d+)回', round_text)
                    if match:
                        round_number = int(match.group(1))
                        if not recommended_round or round_number > recommended_round[1]:
                            recommended_round = (round_text, round_number)
                except:
                    pass
            
            self.round_combo['values'] = round_options
            self.available_rounds = valid_rounds
            
            # Prioritize CSV filename match over latest round
            selected_round = csv_matched_round if csv_matched_round else recommended_round
            
            if selected_round:
                self.round_combo.set(selected_round[0])
                
                if csv_matched_round:
                    # CSV filename match found - highest priority
                    self.update_status(f"🎯 Perfect match! Auto-continuing with round {selected_round[0]}...")
                    self.round_status.config(text=f"🎯 CSV Match: {selected_round[0]} (auto-continuing)", foreground="green")
                    
                    # Auto-continue workflow after 2 seconds for CSV filename matches
                    self.root.after(2000, self._auto_continue_workflow)
                else:
                    # Fallback to latest round
                    self.update_status(f"✅ Auto-selected latest round: {selected_round[0]} - Click 'Continue Workflow' or change selection")
                    self.round_status.config(text=f"✅ Recommended: {selected_round[0]} (latest)", foreground="green")
            else:
                self.update_status(f"Detected {len(valid_rounds)} valid rounds - Please select and click 'Continue Workflow'")
                self.round_status.config(text=f"Found {len(valid_rounds)} valid rounds - Select one to continue", foreground="blue")
            
            # Enable round selection
            self.round_combo.config(state="readonly")
            
            # Add continue button if not exists
            if not hasattr(self, 'continue_workflow_button'):
                # Find the navigation buttons frame in round_frame
                nav_frame = None
                for child in self.round_combo.master.winfo_children():
                    if isinstance(child, ttk.Frame):
                        nav_frame = child
                        break
                
                if nav_frame:
                    self.continue_workflow_button = ttk.Button(nav_frame, text="Continue Workflow", 
                                                              command=self.continue_complete_workflow)
                    self.continue_workflow_button.pack(side=tk.LEFT, padx=5)
            
            # Enable continue button
            if hasattr(self, 'continue_workflow_button'):
                self.continue_workflow_button.config(state=tk.NORMAL)
            
            # Show improved message to user
            if minitoto_count > 0:
                filter_info = f"\n🚫 Filtered out {minitoto_count} minitoto round(s)"
            else:
                filter_info = ""
            
            if csv_matched_round:
                # Prefer CSV filename match in the message
                message = (
                    f"✅ Found {len(valid_rounds)} valid round(s){filter_info}\n\n"
                    f"🎯 CSV match: {csv_matched_round[0]} (auto-continue in 2s)\n\n"
                    "Options:\n"
                    "• Change selection if needed, or wait to auto-continue\n"
                    "• You can also click 'Continue Workflow' now"
                )
            elif recommended_round:
                message = (
                    f"✅ Found {len(valid_rounds)} valid round(s){filter_info}\n\n"
                    f"🎯 Auto-selected: {recommended_round[0]} (latest)\n\n"
                    "Options:\n"
                    "• Click 'Continue Workflow' to proceed with selected round\n"
                    "• Or change selection from dropdown first\n\n"
                    "Ready to continue!"
                )
            else:
                message = (
                    f"Found {len(valid_rounds)} valid round(s){filter_info}\n\n"
                    "Please:\n"
                    "1. Select the desired round from dropdown\n"
                    "2. Click 'Continue Workflow' to proceed"
                )
            
            messagebox.showinfo("🎯 Round Selection Ready", message)
            
        except Exception as e:
            messagebox.showerror("Error", f"Failed to update rounds: {e}")
    
    def continue_complete_workflow(self):
        """Continue complete workflow after round selection"""
        try:
            # Validate round selection
            if not self.round_combo.get():
                messagebox.showerror("Error", "Please select a round first")
                return
            
            # Find selected round info
            selected_text = self.round_combo.get()
            selected_round = None
            for round_info in self.available_rounds:
                if round_info['text'] == selected_text:
                    selected_round = round_info
                    break
            
            if not selected_round:
                messagebox.showerror("Error", "Selected round not found")
                return
            
            # Select the round
            if not self.round_selector.select_round_by_number(self.available_rounds, selected_round['round_number']):
                messagebox.showerror("Error", "Failed to select round")
                return
            
            # Update status and progress
            self.update_workflow_progress('navigation', 40)
            self.update_status("Round selected - continuing workflow...")
            self.round_status.config(text=f"Selected: {selected_text}", foreground="green")
            
            # Disable continue button
            if hasattr(self, 'continue_workflow_button'):
                self.continue_workflow_button.config(state=tk.DISABLED)
            
            # Continue with the stored workflow function
            if hasattr(self, 'continue_workflow_function'):
                workflow_thread = threading.Thread(target=self.continue_workflow_function, daemon=True)
                workflow_thread.start()
            else:
                messagebox.showerror("Error", "Workflow continuation function not found")
                
        except Exception as e:
            messagebox.showerror("Error", f"Failed to continue workflow: {e}")
    
    def _auto_continue_workflow(self):
        """Auto-continue workflow when CSV filename matches detected round"""
        try:
            # Only auto-continue if the continue button exists and is enabled
            if (hasattr(self, 'continue_workflow_button') and 
                self.continue_workflow_button['state'] == 'normal'):
                
                self.update_status("🚀 Auto-continuing workflow due to CSV filename match...")
                self.continue_complete_workflow()
            
        except Exception as e:
            print(f"Auto-continue failed: {e}")
            # Just log the error, don't show dialog to avoid interrupting auto-flow
    
    def update_status(self, message):
        """Update status bar message"""
        self.status_label.config(text=message)
    
    def update_workflow_progress(self, stage, progress_percent=None):
        """Update workflow progress with current stage and optional progress percentage"""
        stage_messages = {
            'init': '初期化中...',
            'detecting_rounds': 'ラウンド検出中...',
            'round_selection': 'ラウンド選択中...',
            'navigation': 'ページ遷移中...',
            'voting_page': '投票ページ移動中...',
            'batch_processing': 'バッチ処理中...',
            'cart_addition': 'カート追加中...',
            'next_batch': '次バッチ準備中...',
            'completion': '処理完了',
            'error': 'エラー発生',
            'ready': '待機中'
        }
        
    message = stage_messages.get(stage, str(stage)) or str(stage)
        self.workflow_progress.config(text=message)
        
        if progress_percent is not None:
            self.progress['value'] = progress_percent
    
    def update_batch_progress_detailed(self, current_batch, total_batches, current_set=None, total_sets=None, stage=None):
        """Update detailed batch progress with current batch, set info, and stage"""
        # Update batch progress bar
        if total_batches > 0:
            batch_percent = (current_batch / total_batches) * 100
            self.batch_progress['value'] = batch_percent
        
        # Create detailed progress message
        progress_parts = []
        if current_batch and total_batches:
            progress_parts.append(f"バッチ {current_batch}/{total_batches}")
        
        if current_set and total_sets:
            progress_parts.append(f"セット {current_set}/{total_sets}")
        
        if stage:
            stage_map = {
                'processing': '処理中',
                'input': '入力中',
                'cart': 'カート追加',
                'navigation': 'ナビゲーション',
                'waiting': '待機中'
            }
            progress_parts.append(stage_map.get(stage, stage))
        
        if progress_parts:
            detailed_message = " | ".join(progress_parts)
            self.update_status(detailed_message)
        
        # Update overall progress if we have complete information
        if current_batch and total_batches and current_set and total_sets:
            # Calculate overall progress across all batches
            completed_batches = current_batch - 1
            current_batch_progress = (current_set / total_sets) if total_sets > 0 else 0
            overall_progress = ((completed_batches + current_batch_progress) / total_batches) * 100
            self.progress['value'] = min(overall_progress, 100)
    
    def run(self):
        """Run the GUI application"""
        self.root.mainloop()

def main():
    """Main entry point for enhanced GUI application"""
    app = EnhancedAutomationGUI()
    app.run()

if __name__ == "__main__":
    main()
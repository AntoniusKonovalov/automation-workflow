"""
Main Application File - Modular Git Workflow Automator
Uses React-style component decomposition for better maintainability
"""

import tkinter as tk
from tkinter import ttk, messagebox, filedialog, scrolledtext
import os
import threading
from pathlib import Path

# Import our components
from components import ThemeManager, GitManager, FileManager, ChangedFile, APIClient, UIUtils, CustomScrollbar, ChatHistoryManager, ClaudeRunner
from components.ui import FileListPanel, AnalysisPanel


class WorkflowAutomator:
    """Main application class - orchestrates all components"""
    
    def __init__(self, root):
        self.root = root
        self.root.title("Git Workflow Automator")
        
        # Remove default title bar for custom styling
        self.root.overrideredirect(True)
        
        # Start maximized - get screen dimensions and set window to full size
        screen_width = self.root.winfo_screenwidth()
        screen_height = self.root.winfo_screenheight()
        self.root.geometry(f"{screen_width}x{screen_height}+0+0")
        
        # Window state tracking
        self.is_maximized = True  # Start in maximized state
        self.normal_geometry = "1400x900+100+50"  # Fallback for restore
        
        # Initialize managers
        self.theme_manager = ThemeManager(root)
        self.git_manager = GitManager()
        self.file_manager = FileManager()
        self.api_client = APIClient()
        self.ui_utils = UIUtils()
        self.chat_history_manager = ChatHistoryManager()
        self.claude_runner = ClaudeRunner()
        
        # Application state
        self.project_path = ""
        self.changed_files = []
        self.selected_files = []
        self.files_section_collapsed = True
        self.selected_expanded = False
        self.history_section_collapsed = True
        
        # Status tracking
        self.status_var = tk.StringVar()
        self.status_var.set("Ready")
        
        # UI Components (will be initialized in setup_ui)
        self.file_list_panel = None
        self.analysis_panel = None
        self.selected_text = None
        self.files_toggle_btn = None
        
        self.setup_ui()
        
        # Try to auto-detect current project if in git repo
        self.auto_detect_project()
    
    def setup_ui(self):
        """Set up the main UI layout"""
        # Create custom title bar
        self.setup_title_bar()
        
        # Main frame with no padding to maximize space
        main_frame = ttk.Frame(self.root, style='TFrame')
        main_frame.grid(row=1, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))
        
        # Configure grid weights
        self.root.columnconfigure(0, weight=1)
        self.root.rowconfigure(0, weight=0)  # Title bar row - fixed height
        self.root.rowconfigure(1, weight=1)  # Main content row - expandable
        main_frame.columnconfigure(0, weight=0)  # Sidebar column - fixed width
        main_frame.columnconfigure(1, weight=1)  # Main content column - expandable
        main_frame.columnconfigure(2, weight=0)  # Button column - fixed width
        main_frame.rowconfigure(3, weight=1)  # Main content row
        main_frame.rowconfigure(4, weight=0)  # Status bar row
        
        # Create header section
        self.setup_header(main_frame)
        
        # Create main content area
        self.setup_main_content(main_frame)
        
        # Create chat history panel (initially hidden)
        self.setup_chat_history_panel(main_frame)
        
        # Create status bar at bottom
        self.setup_status_bar(main_frame)
    
    def setup_title_bar(self):
        """Create custom title bar with window controls"""
        title_bar = ttk.Frame(self.root, style='TitleBar.TFrame')
        title_bar.grid(row=0, column=0, sticky=(tk.W, tk.E), padx=0, pady=0)
        
        # Make title bar draggable
        title_bar.bind('<Button-1>', self.start_move)
        title_bar.bind('<B1-Motion>', self.on_move)
        title_bar.bind('<Double-Button-1>', self.toggle_maximize)
        
        # App title and icon
        title_left = ttk.Frame(title_bar, style='TitleBar.TFrame')
        title_left.pack(side=tk.LEFT, fill=tk.Y, padx=(15, 0))
        
        app_icon = ttk.Label(title_left, text="🚀", style='TitleIcon.TLabel')
        app_icon.pack(side=tk.LEFT, padx=(0, 8), pady=8)
        app_icon.bind('<Button-1>', self.start_move)
        app_icon.bind('<B1-Motion>', self.on_move)
        app_icon.bind('<Double-Button-1>', self.toggle_maximize)
        
        app_title = ttk.Label(title_left, text="Git Workflow Automator", style='TitleText.TLabel')
        app_title.pack(side=tk.LEFT, pady=8)
        app_title.bind('<Button-1>', self.start_move)
        app_title.bind('<B1-Motion>', self.on_move)
        app_title.bind('<Double-Button-1>', self.toggle_maximize)
        
        # Window control buttons
        controls_frame = ttk.Frame(title_bar, style='TitleBar.TFrame')
        controls_frame.pack(side=tk.RIGHT, padx=0, pady=0)
        
        # Minimize button
        minimize_btn = ttk.Button(controls_frame, text="─", style='TitleButton.TButton',
                                 command=self.minimize_window, width=3)
        minimize_btn.pack(side=tk.LEFT)
        self.ui_utils.bind_hover_cursor(minimize_btn)
        self.ui_utils.add_tooltip(minimize_btn, "Minimize")
        
        # Maximize/Restore button (start with restore icon since we're maximized)
        self.maximize_btn = ttk.Button(controls_frame, text="❐", style='TitleButton.TButton',
                                      command=self.toggle_maximize, width=3)
        self.maximize_btn.pack(side=tk.LEFT)
        self.ui_utils.bind_hover_cursor(self.maximize_btn)
        self.ui_utils.add_tooltip(self.maximize_btn, "Restore")
        
        # Close button
        close_btn = ttk.Button(controls_frame, text="✕", style='TitleButtonClose.TButton',
                              command=self.close_window, width=3)
        close_btn.pack(side=tk.LEFT)
        self.ui_utils.bind_hover_cursor(close_btn)
        self.ui_utils.add_tooltip(close_btn, "Close")
    
    # Window control methods
    def start_move(self, event):
        """Start window move operation"""
        self.x_offset = event.x_root - self.root.winfo_rootx()
        self.y_offset = event.y_root - self.root.winfo_rooty()
    
    def on_move(self, event):
        """Handle window move"""
        if not self.is_maximized:
            x = event.x_root - self.x_offset
            y = event.y_root - self.y_offset
            self.root.geometry(f"+{x}+{y}")
    
    def minimize_window(self):
        """Minimize the window"""
        self.root.iconify()
    
    def toggle_maximize(self, event=None):
        """Toggle between maximize and restore"""
        if self.is_maximized:
            # Restore window
            self.root.geometry(self.normal_geometry)
            self.maximize_btn.config(text="□")
            self.ui_utils.add_tooltip(self.maximize_btn, "Maximize")
            self.is_maximized = False
        else:
            # Maximize window
            self.normal_geometry = self.root.geometry()
            # Get screen dimensions
            screen_width = self.root.winfo_screenwidth()
            screen_height = self.root.winfo_screenheight()
            self.root.geometry(f"{screen_width}x{screen_height}+0+0")
            self.maximize_btn.config(text="❐")
            self.ui_utils.add_tooltip(self.maximize_btn, "Restore")
            self.is_maximized = True
    
    def close_window(self):
        """Handle window close with session save dialog"""
        # Check if there's an active session with unsaved changes
        if (self.chat_history_manager.current_session and 
            self.chat_history_manager.current_session.entries and 
            not self.chat_history_manager.current_session.is_saved):
            
            # Show save session dialog
            result = self.show_save_session_dialog()
            
            if result == "save":
                # Mark session as saved
                self.chat_history_manager.current_session.is_saved = True
                self.chat_history_manager.save_project_sessions()
                self.status_var.set("Session saved")
            elif result == "discard":
                # Don't save, just close
                pass
            elif result == "cancel":
                # Cancel closing
                return
        
        # Save all sessions before closing
        if self.chat_history_manager.current_project_path:
            self.chat_history_manager.save_project_sessions()
        
        self.root.destroy()
    
    def show_save_session_dialog(self):
        """Show dialog asking if user wants to save current session"""
        from tkinter import messagebox
        
        session = self.chat_history_manager.current_session
        session_name = session.session_name if session else "Current Session"
        entry_count = len(session.entries) if session else 0
        
        dialog_message = f"Save chat session '{session_name}'?\n\n"
        dialog_message += f"This session contains {entry_count} conversation(s).\n"
        dialog_message += "Your progress will be lost if you don't save it."
        
        # Custom dialog with three options
        result = messagebox.askyesnocancel(
            "Save Session", 
            dialog_message,
            icon='question'
        )
        
        if result is True:
            return "save"
        elif result is False:
            return "discard" 
        else:
            return "cancel"
    
    def setup_header(self, main_frame):
        """Create the header with project path and API status"""
        # Project path selection
        path_label = ttk.Label(main_frame, text="📂 Project Path:", 
                              style='Heading.TLabel')
        path_label.grid(row=0, column=1, sticky=tk.W, padx=(10, 0), pady=(10, 5))
        
        self.path_var = tk.StringVar()
        ttk.Entry(main_frame, textvariable=self.path_var, width=50, style='TEntry').grid(
            row=0, column=1, sticky=(tk.W, tk.E), padx=(150, 5))
        
        browse_btn = ttk.Button(main_frame, text="Browse", command=self.browse_project, style='TButton')
        browse_btn.grid(row=0, column=2, padx=(0, 10))
        self.ui_utils.bind_hover_cursor(browse_btn)
        
        # API status and key management
        api_status = self.api_client.get_api_status()
        api_label = ttk.Label(main_frame, text=f"🔑 API Status: {api_status}",
                             style='Secondary.TLabel')
        api_label.grid(row=1, column=1, sticky=tk.W, padx=(10, 0), pady=(5, 5))
        
        # Claude Code CLI status
        claude_status = "Available" if self.claude_runner.is_claude_available() else "Not Found"
        claude_status_emoji = "🤖" if claude_status == "Available" else "⚠️"
        claude_label = ttk.Label(main_frame, text=f"{claude_status_emoji} Claude Code: {claude_status}",
                                style='Secondary.TLabel')
        claude_label.grid(row=2, column=1, sticky=tk.W, padx=(10, 0), pady=(0, 5))
        
        self.api_key_var = tk.StringVar()
        if self.api_client.preferred_api == 'anthropic':
            self.api_key_var.set("Claude API key loaded from .env")
        elif self.api_client.preferred_api == 'openai':
            self.api_key_var.set("OpenAI API key loaded from .env")
        else:
            self.api_key_var.set("No API key found in .env file")
        
        api_entry = ttk.Entry(main_frame, textvariable=self.api_key_var, 
                             width=50, state='readonly')
        api_entry.grid(row=1, column=1, sticky=(tk.W, tk.E), padx=(150, 5))
        
        # GPT Model selector dropdown
        model_var = tk.StringVar(value=self.api_client.get_current_model_display_name())
        self.model_var = model_var
        model_menu = ttk.Menubutton(main_frame, textvariable=model_var, 
                                   width=20, style='TButton')
        model_menu.grid(row=2, column=2, padx=(0, 10))
        self.ui_utils.bind_hover_cursor(model_menu)
        
        # Create model dropdown menu
        model_dropdown = tk.Menu(model_menu, tearoff=0,
                               bg=self.theme_manager.colors['bg_secondary'],
                               fg=self.theme_manager.colors['text_primary'],
                               activebackground=self.theme_manager.colors['accent'],
                               activeforeground='white',
                               borderwidth=0)
        
        # Add model options
        for display_name, model_id in self.api_client.available_models.items():
            model_dropdown.add_command(
                label=display_name,
                command=lambda name=display_name: self.select_model(name)
            )
        
        model_menu.config(menu=model_dropdown)
        self.model_menu = model_menu
    
    def setup_main_content(self, main_frame):
        """Create the main content area with panels"""
        # Create sidebar toggle
        self.setup_sidebar(main_frame)
        
        # Paned window for split view
        self.main_paned = tk.PanedWindow(main_frame, 
                                        orient=tk.HORIZONTAL,
                                        sashwidth=8,
                                        sashrelief=tk.FLAT,
                                        bg=self.theme_manager.colors['border'],
                                        sashcursor='sb_h_double_arrow',
                                        showhandle=False,
                                        opaqueresize=True)
        self.main_paned.grid(row=3, column=1, columnspan=2,
                            sticky=(tk.W, tk.E, tk.N, tk.S), padx=(0, 10), pady=(10, 0))
        
        # Create file list panel (left side - collapsible)
        self.file_list_panel = FileListPanel(self.main_paned, self.theme_manager, 
                                            self.file_manager, self.ui_utils)
        
        # Set up callbacks for file list panel
        self.setup_file_list_callbacks()
        
        # Right panel - Contains Selected and Analysis sections
        right_frame = ttk.Frame(self.main_paned, style='Card.TFrame')
        self.main_paned.add(right_frame, minsize=400)
        
        # Create vertical split for Selected and Analysis
        self.setup_right_panel(right_frame)
        
        # Start with left panel collapsed
        self.main_paned.forget(self.file_list_panel.frame)
    
    def setup_sidebar(self, main_frame):
        """Create the collapsible sidebar"""
        self.toggle_frame = ttk.Frame(main_frame, style='Sidebar.TFrame')
        self.toggle_frame.grid(row=3, column=0, sticky=(tk.N, tk.S, tk.W), padx=(10, 0), pady=(10, 0))
        
        sidebar_content = ttk.Frame(self.toggle_frame, style='TFrame')
        sidebar_content.pack(fill=tk.BOTH, expand=True, padx=8, pady=15)
        
        # Files icon
        files_icon = ttk.Label(sidebar_content, text="📁", 
                              style='SidebarIcon.TLabel', font=('Segoe UI', 16))
        files_icon.pack(pady=(0, 10))
        
        # Toggle button
        self.files_toggle_btn = ttk.Button(sidebar_content, text="▶",
                                          command=self.toggle_files_section, 
                                          style='Sidebar.TButton', width=3)
        self.files_toggle_btn.pack()
        self.ui_utils.bind_hover_cursor(self.files_toggle_btn)
        self.ui_utils.add_tooltip(self.files_toggle_btn, "Toggle Files Panel")
        
        # Chat history icon (clickable) - attached below files toggle
        self.history_icon = ttk.Label(sidebar_content, text="💬", 
                                     style='SidebarIcon.TLabel', font=('Segoe UI', 16))
        self.history_icon.pack(pady=(5, 10))  # Reduced top padding
        
        # Make the icon clickable
        self.history_icon.bind("<Button-1>", lambda e: self.toggle_history_section())
        self.ui_utils.bind_hover_cursor(self.history_icon)
        self.ui_utils.add_tooltip(self.history_icon, "Toggle Chat History")
    
    def setup_right_panel(self, right_frame):
        """Set up the right panel with Selected and Analysis sections"""
        # Create vertical PanedWindow
        vertical_paned = tk.PanedWindow(right_frame, 
                                       orient=tk.VERTICAL,
                                       sashwidth=6,
                                       sashrelief=tk.FLAT,
                                       bg=self.theme_manager.colors['border'])
        vertical_paned.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
        
        # Top section - Selected for Analysis (reduced to half size)
        selected_container = ttk.Frame(vertical_paned, style='TFrame')
        vertical_paned.add(selected_container, minsize=150, height=125)
        
        self.setup_selected_section(selected_container)
        
        # Bottom section - Analysis
        analysis_container = ttk.Frame(vertical_paned, style='TFrame')
        vertical_paned.add(analysis_container, minsize=300)
        
        # Create analysis panel
        self.analysis_panel = AnalysisPanel(analysis_container, self.theme_manager, self.ui_utils)
        self.analysis_panel.frame.pack(fill=tk.BOTH, expand=True)
        
        # Set up analysis panel callbacks
        self.setup_analysis_callbacks()
        
        # Store references
        self.vertical_paned = vertical_paned
        self.selected_container = selected_container
        self.analysis_container = analysis_container
    
    def setup_status_bar(self, main_frame):
        """Create status bar at bottom of window"""
        status_frame = ttk.Frame(main_frame, style='TFrame')
        status_frame.grid(row=4, column=0, columnspan=3, sticky=(tk.W, tk.E), 
                         padx=10, pady=(0, 5))
        
        # Status label (left)
        status_label = ttk.Label(status_frame, textvariable=self.status_var,
                                style='Secondary.TLabel')
        status_label.pack(side=tk.LEFT)
        
        # Token counter (center-right)
        self.token_var = tk.StringVar()
        self.update_token_display()
        token_label = ttk.Label(status_frame, textvariable=self.token_var,
                               style='Secondary.TLabel')
        token_label.pack(side=tk.RIGHT, padx=(0, 20))
        
        # Refresh button (moved from sidebar)
        refresh_btn = ttk.Button(status_frame, text="🔄", width=3,
                                command=self.refresh_with_reset, 
                                style='TButton')
        refresh_btn.pack(side=tk.RIGHT, padx=(0, 5))
        self.ui_utils.bind_hover_cursor(refresh_btn)
        self.ui_utils.add_tooltip(refresh_btn, "Refresh Files")
        
        # Clear tokens button
        clear_tokens_btn = ttk.Button(status_frame, text="🗑️", width=3,
                                     command=self.clear_token_history,
                                     style='TButton')
        clear_tokens_btn.pack(side=tk.RIGHT, padx=(0, 5))
        self.ui_utils.bind_hover_cursor(clear_tokens_btn)
        self.ui_utils.add_tooltip(clear_tokens_btn, "Clear Token History")
        
        # Current model indicator (right)
        model_indicator = ttk.Label(status_frame, 
                                   text=f"Model: {self.api_client.get_current_model_display_name()}",
                                   style='Secondary.TLabel')
        model_indicator.pack(side=tk.RIGHT, padx=(0, 10))
        self.model_indicator = model_indicator
    
    def setup_chat_history_panel(self, main_frame):
        """Create the expandable chat history panel with session list"""
        self.history_frame = ttk.Frame(main_frame, style='Card.TFrame')
        # Don't grid yet - will be shown when toggled
        
        # Header
        history_header = ttk.Frame(self.history_frame, style='TFrame')
        history_header.pack(fill=tk.X, padx=10, pady=(10, 5))
        
        history_label = ttk.Label(history_header, text="💬 Chat Sessions:",
                                 style='Heading.TLabel')
        history_label.pack(side=tk.LEFT)
        
        # Buttons
        history_buttons = ttk.Frame(history_header, style='TFrame')
        history_buttons.pack(side=tk.RIGHT)
        
        new_session_btn = ttk.Button(history_buttons, text="New",
                                    command=self.start_new_session,
                                    style='Accent.TButton')
        new_session_btn.pack(side=tk.LEFT, padx=2)
        self.ui_utils.bind_hover_cursor(new_session_btn)
        self.ui_utils.add_tooltip(new_session_btn, "Start New Session")
        
        clear_history_btn = ttk.Button(history_buttons, text="Clear All",
                                      command=self.clear_chat_history,
                                      style='TButton')
        clear_history_btn.pack(side=tk.LEFT, padx=2)
        self.ui_utils.bind_hover_cursor(clear_history_btn)
        self.ui_utils.add_tooltip(clear_history_btn, "Clear All Sessions")
        
        # Session list with scrollbar - no padding for full width
        sessions_list_frame = ttk.Frame(self.history_frame, style='TFrame')
        sessions_list_frame.pack(fill=tk.BOTH, expand=True, padx=0, pady=(0, 0))
        
        # Create custom scrollable frame with no padding for full-width sessions
        canvas_frame = tk.Frame(sessions_list_frame)
        canvas_frame.pack(fill=tk.BOTH, expand=True, padx=0, pady=0)  # No padding
        
        sessions_canvas = tk.Canvas(canvas_frame, 
                                   bg=self.theme_manager.colors['bg_primary'],
                                   highlightthickness=0,
                                   borderwidth=0)
        
        sessions_scrollbar = CustomScrollbar(canvas_frame, orient=tk.VERTICAL, 
                                            command=sessions_canvas.yview)
        self.sessions_container = tk.Frame(sessions_canvas, bg=self.theme_manager.colors['bg_primary'])
        
        self.sessions_container.bind(
            "<Configure>",
            lambda e: sessions_canvas.configure(scrollregion=sessions_canvas.bbox("all"))
        )
        
        # Create window that fills the canvas width
        canvas_window = sessions_canvas.create_window((0, 0), window=self.sessions_container, anchor="nw")
        
        # Configure the frame to match canvas width
        def configure_frame_width(event=None):
            canvas_width = sessions_canvas.winfo_width()
            sessions_canvas.itemconfig(canvas_window, width=canvas_width)
        
        sessions_canvas.bind('<Configure>', configure_frame_width)
        sessions_canvas.configure(yscrollcommand=sessions_scrollbar.set)
        
        sessions_canvas.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        sessions_scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        
        # Bind mousewheel to canvas
        def on_sessions_mousewheel(event):
            sessions_canvas.yview_scroll(int(-1*(event.delta/120)), "units")
            sessions_scrollbar.show_scrollbar()
        
        sessions_canvas.bind("<MouseWheel>", on_sessions_mousewheel)
        
        # Store session widgets for management
        self.session_widgets = []
        self.current_session_widget = None
    
    def setup_selected_section(self, container):
        """Set up the Selected for Analysis section"""
        # Header
        selected_label_frame = ttk.Frame(container, style='TFrame')
        selected_label_frame.pack(fill=tk.X, padx=10, pady=(10, 5))
        
        selected_label = ttk.Label(selected_label_frame, text="📋 Selected for Analysis:",
                                  style='Heading.TLabel')
        selected_label.pack(side=tk.LEFT)
        
        # Buttons
        button_frame = ttk.Frame(selected_label_frame, style='TFrame')
        button_frame.pack(side=tk.RIGHT)
        
        self.expand_selected_btn = ttk.Button(button_frame, text="Expand ↓",
                                             command=self.toggle_selected_size, 
                                             style='TButton')
        self.expand_selected_btn.pack(side=tk.LEFT, padx=2)
        self.ui_utils.bind_hover_cursor(self.expand_selected_btn)
        
        copy_all_btn = ttk.Button(button_frame, text="Copy All",
                                 command=self.copy_all_selected, style='TButton')
        copy_all_btn.pack(side=tk.LEFT, padx=2)
        self.ui_utils.bind_hover_cursor(copy_all_btn)
        
        append_all_btn = ttk.Button(button_frame, text="Append All",
                                   command=self.append_all_files, style='TButton')
        append_all_btn.pack(side=tk.LEFT, padx=2)
        self.ui_utils.bind_hover_cursor(append_all_btn)
        
        clear_all_btn = ttk.Button(button_frame, text="Clear All",
                                  command=self.clear_selection, style='TButton')
        clear_all_btn.pack(side=tk.LEFT, padx=2)
        self.ui_utils.bind_hover_cursor(clear_all_btn)
        
        # Selected files text area
        selected_frame = ttk.Frame(container, style='TFrame')
        selected_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=(0, 10))
        
        # Create custom scrollable text area for selected files
        selected_text_frame = ttk.Frame(selected_frame, style='TFrame')
        selected_text_frame.pack(fill=tk.BOTH, expand=True)
        
        self.selected_text = tk.Text(
            selected_text_frame, 
            wrap=tk.WORD, 
            font=self.theme_manager.fonts['code'],
            bg=self.theme_manager.colors['chat_user'],
            fg=self.theme_manager.colors['text_primary'],
            highlightthickness=0,
            borderwidth=0)
        self.selected_text.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        
        # Add custom scrollbar
        selected_scrollbar = CustomScrollbar(selected_text_frame, orient=tk.VERTICAL, 
                                           command=self.selected_text.yview)
        selected_scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        self.selected_text.configure(yscrollcommand=selected_scrollbar.set)
        
        # Add mousewheel support
        def on_selected_mousewheel(event):
            self.selected_text.yview_scroll(int(-1*(event.delta/120)), "units")
            selected_scrollbar.show_scrollbar()
        
        self.selected_text.bind("<MouseWheel>", on_selected_mousewheel)
        self.selected_text.insert('1.0', "No files selected for analysis")
    
    def setup_file_list_callbacks(self):
        """Set up callbacks for file list panel interactions"""
        callbacks = {
            'copy_path': self.copy_path,
            'copy_append': self.copy_and_append,
            'toggle_content': self.toggle_content,
            'toggle_selection': self.toggle_selection,
            'remove_file': self.remove_file
        }
        self.file_list_callbacks = callbacks
    
    def setup_analysis_callbacks(self):
        """Set up callbacks for analysis panel"""
        # Connect button callbacks
        self.analysis_panel.toggle_orchestrator_btn.configure(
            command=self.analysis_panel.toggle_orchestrator_section)
        self.analysis_panel.toggle_prompt_btn.configure(
            command=self.analysis_panel.toggle_prompt_section)
        self.analysis_panel.clear_chat_btn.configure(
            command=self.analysis_panel.clear_chat)
        
        # Connect send buttons
        self.analysis_panel.orchestrator_send_btn.configure(
            command=lambda: self.send_to_ai('orchestrator'))
        self.analysis_panel.prompt_send_btn.configure(
            command=lambda: self.send_to_ai('prompt'))
        
        # Set up send to agent callback
        self.analysis_panel.send_to_agent_callback = self.send_to_claude_headless
    
    # ========== EVENT HANDLERS ==========
    
    def select_model(self, display_name):
        """Handle model selection from dropdown"""
        self.api_client.set_model(display_name)
        self.model_var.set(display_name)
        
        # Update model indicator in status bar
        if hasattr(self, 'model_indicator'):
            self.model_indicator.config(text=f"Model: {display_name}")
        
        # Update token display for new model
        self.update_token_display()
        
        # Update status to show selected model
        model_id = self.api_client.selected_model
        self.status_var.set(f"Model changed to: {display_name} ({model_id})")
        
        # Auto-clear status after 3 seconds
        self.root.after(3000, lambda: self.status_var.set("Ready"))
    
    def update_token_display(self):
        """Update the token counter display"""
        token_info = self.api_client.get_token_usage_info()
        used = token_info['used']
        limit = token_info['limit']
        remaining = token_info['remaining']
        percentage = token_info['percentage']
        
        # Color code based on usage percentage
        if percentage >= 90:
            indicator = "🔴"  # Red - almost full
        elif percentage >= 70:
            indicator = "🟡"  # Yellow - getting full
        else:
            indicator = "🟢"  # Green - plenty of space
        
        self.token_var.set(f"{indicator} Tokens: {used:,}/{limit:,} ({remaining:,} left)")
    
    def clear_token_history(self):
        """Clear token usage history"""
        self.api_client.reset_session_tokens()
        self.update_token_display()
        self.status_var.set("Token history cleared")
        self.root.after(2000, lambda: self.status_var.set("Ready"))
    
    def refresh_chat_history_display(self):
        """Refresh the session list display"""
        if not hasattr(self, 'sessions_container'):
            return
        
        # Load project sessions if needed
        if self.project_path and self.chat_history_manager.current_project_path != self.project_path:
            print(f"Loading sessions for project: {self.project_path}")
            self.chat_history_manager.load_project_sessions(self.project_path)
        
        # Clear existing session widgets
        for widget in self.session_widgets:
            widget.destroy()
        self.session_widgets.clear()
        self.current_session_widget = None
        
        # Get sessions for current project
        sessions = self.chat_history_manager.get_project_sessions()
        
        if not sessions:
            # Show empty state
            empty_label = ttk.Label(self.sessions_container, 
                                   text="No sessions yet.\nClick 'New' to start!",
                                   style='Secondary.TLabel',
                                   justify='center')
            empty_label.pack(pady=20)
            self.session_widgets.append(empty_label)
        else:
            # Display sessions in reverse order (newest first)
            for session in reversed(sessions):
                session_widget = self.create_session_widget(session)
                self.session_widgets.append(session_widget)
    
    def create_session_widget(self, session):
        """Create a widget for a chat session"""
        # Session container - full width edge to edge
        session_frame = tk.Frame(self.sessions_container, 
                                bg=self.theme_manager.colors['bg_tertiary'],
                                relief='flat',
                                bd=0,
                                highlightthickness=0)
        session_frame.pack(fill=tk.BOTH, padx=0, pady=1)  # Use BOTH to ensure full width
        
        # Session info frame with padding for text
        info_frame = tk.Frame(session_frame, bg=self.theme_manager.colors['bg_tertiary'])
        info_frame.pack(fill=tk.BOTH, padx=15, pady=10)  # Padding only for the text content
        
        # Session name
        name_label = tk.Label(info_frame,
                             text=session.session_name,
                             font=self.theme_manager.fonts['default'],
                             fg=self.theme_manager.colors['text_primary'],
                             bg=self.theme_manager.colors['bg_tertiary'],
                             anchor='w')
        name_label.pack(fill=tk.X)
        
        # Session details (date and time only)
        details_text = session.get_formatted_date()
        details_label = tk.Label(info_frame,
                                text=details_text,
                                font=self.theme_manager.fonts['small'],
                                fg=self.theme_manager.colors['text_secondary'],
                                bg=self.theme_manager.colors['bg_tertiary'],
                                anchor='w')
        details_label.pack(fill=tk.X)
        
        # Hover effects
        def on_enter(event):
            session_frame.config(bg=self.theme_manager.colors['bg_secondary'])
            info_frame.config(bg=self.theme_manager.colors['bg_secondary'])
            name_label.config(bg=self.theme_manager.colors['bg_secondary'])
            details_label.config(bg=self.theme_manager.colors['bg_secondary'])
        
        def on_leave(event):
            # Don't change if this is the active session
            if session_frame != self.current_session_widget:
                session_frame.config(bg=self.theme_manager.colors['bg_tertiary'])
                info_frame.config(bg=self.theme_manager.colors['bg_tertiary'])
                name_label.config(bg=self.theme_manager.colors['bg_tertiary'])
                details_label.config(bg=self.theme_manager.colors['bg_tertiary'])
        
        def on_click(event):
            self.switch_to_session(session.session_id, session_frame)
        
        # Bind events to all components
        for widget in [session_frame, info_frame, name_label, details_label]:
            widget.bind("<Enter>", on_enter)
            widget.bind("<Leave>", on_leave)
            widget.bind("<Button-1>", on_click)
            widget.config(cursor="hand2")
        
        # Highlight if this is the current session
        if (self.chat_history_manager.current_session and 
            session.session_id == self.chat_history_manager.current_session.session_id):
            self.current_session_widget = session_frame
            session_frame.config(bg=self.theme_manager.colors['accent'])
            info_frame.config(bg=self.theme_manager.colors['accent'])
            name_label.config(bg=self.theme_manager.colors['accent'], fg='white')
            details_label.config(bg=self.theme_manager.colors['accent'], fg='white')
        
        return session_frame
    
    def start_new_session(self):
        """Start a new chat session"""
        if not self.project_path:
            messagebox.showwarning("No Project", "Please load a project first.")
            return
        
        # Start new session in the chat history manager
        new_session = self.chat_history_manager.start_new_session()
        
        # Refresh the display
        self.refresh_chat_history_display()
        
        # Clear the analysis panel for the new session
        if hasattr(self.analysis_panel, 'clear_chat'):
            self.analysis_panel.clear_chat()
        
        self.status_var.set("Started new chat session")
        self.root.after(2000, lambda: self.status_var.set("Ready"))
    
    def switch_to_session(self, session_id, session_widget):
        """Switch to a specific session"""
        # Switch session in the chat history manager
        session = self.chat_history_manager.switch_to_session(session_id)
        
        if session:
            # Update visual selection
            if self.current_session_widget:
                # Reset previous selection
                self.current_session_widget.config(bg=self.theme_manager.colors['bg_tertiary'])
                old_widgets = self.current_session_widget.winfo_children()
                if old_widgets:
                    info_frame = old_widgets[0]
                    info_frame.config(bg=self.theme_manager.colors['bg_tertiary'])
                    info_widgets = info_frame.winfo_children()
                    
                    for widget in info_widgets:
                        widget.config(bg=self.theme_manager.colors['bg_tertiary'])
                        if widget.winfo_class() == 'Label':
                            if len(str(widget.cget('text'))) < 20:  # Name label (shorter text)
                                widget.config(fg=self.theme_manager.colors['text_primary'])
                            else:  # Details label (longer text with date)
                                widget.config(fg=self.theme_manager.colors['text_secondary'])
            
            # Highlight new selection
            self.current_session_widget = session_widget
            session_widget.config(bg=self.theme_manager.colors['accent'])
            widgets = session_widget.winfo_children()
            if widgets:
                info_frame = widgets[0]
                info_frame.config(bg=self.theme_manager.colors['accent'])
                info_widgets = info_frame.winfo_children()
                
                for widget in info_widgets:
                    widget.config(bg=self.theme_manager.colors['accent'], fg='white')
            
            # Load session chat history into analysis panel
            if hasattr(self.analysis_panel, 'display_session_history'):
                self.analysis_panel.display_session_history(session)
            
            self.status_var.set(f"Switched to session: {session.session_name}")
            self.root.after(2000, lambda: self.status_var.set("Ready"))
    
    def clear_chat_history(self):
        """Clear chat history for current project"""
        if not self.project_path:
            self.status_var.set("No project loaded")
            return
        
        self.chat_history_manager.clear_current_project_history()
        self.refresh_chat_history_display()
        self.status_var.set("Chat history cleared")
        self.root.after(2000, lambda: self.status_var.set("Ready"))
    
    def auto_detect_project(self):
        """Auto-detect current working directory as project if it's a git repo"""
        import os
        current_dir = os.getcwd()
        
        # Check if current directory is a git repository
        if os.path.exists(os.path.join(current_dir, '.git')):
            print(f"DEBUG: Auto-detected git project: {current_dir}")
            self.project_path = current_dir
            self.chat_history_manager.load_project_sessions(current_dir)
            
            # Refresh display if history panel is visible
            if not self.history_section_collapsed:
                self.refresh_chat_history_display()
            
            self.status_var.set(f"Auto-detected project: {os.path.basename(current_dir)}")
    
    def browse_project(self):
        """Browse for project directory"""
        directory = filedialog.askdirectory()
        if directory:
            self.reset_all_content()
            self.path_var.set(directory)
            self.project_path = directory
            # Load chat history for this project
            self.chat_history_manager.load_project_sessions(directory)
            self.refresh_changed_files()
    
    def refresh_with_reset(self):
        """Refresh files with content reset"""
        if self.project_path:
            self.reset_all_content()
            self.refresh_changed_files()
        else:
            messagebox.showwarning("Warning", "Please select a project path first")
    
    def reset_all_content(self):
        """Reset all content when switching projects"""
        # Clear file data
        self.changed_files.clear()
        self.selected_files.clear()
        self.file_manager.exclude_paths.clear()
        
        # Clear UI
        if self.file_list_panel:
            self.file_list_panel.clear_all()
        
        self.selected_text.delete('1.0', tk.END)
        self.selected_text.insert('1.0', "No files selected for analysis")
        
        if self.analysis_panel:
            self.analysis_panel.clear_chat()
        
        # Set button to loading state (red)
        self.set_button_loading()
        self.status_var.set("Loading new project...")
    
    def set_button_green(self):
        """Set the toggle button to green (loaded) state"""
        self.files_toggle_btn.configure(style='SidebarLoaded.TButton')
        self.files_toggle_btn.update()
        self.root.update()
    
    def set_button_loading(self):
        """Set the toggle button to red (loading) state"""
        self.files_toggle_btn.configure(style='SidebarLoading.TButton')
        self.files_toggle_btn.update()
        self.root.update()
    
    def refresh_changed_files(self):
        """Get changed files from git and update UI"""
        if not self.project_path:
            messagebox.showwarning("Warning", "Please select a project path first")
            return
        
        try:
            self.set_button_loading()
            self.status_var.set("Refreshing changed files...")
            
            # Get changed files from git
            result, error = self.git_manager.get_changed_files(self.project_path)
            
            if error:
                messagebox.showerror("Error", error)
                self.status_var.set("Error getting changed files")
                self.files_toggle_btn.configure(style='Sidebar.TButton')
                return
            
            # Parse the git output
            self.parse_and_create_files(result)
            
            # Update UI
            self.create_file_widgets()
            self.status_var.set(f"Found {len(self.changed_files)} changed files")
            
            # Update button color
            if len(self.changed_files) > 0:
                self.root.after(10, self.set_button_green)
            else:
                self.files_toggle_btn.configure(style='Sidebar.TButton')
                
        except Exception as e:
            messagebox.showerror("Error", f"Failed to refresh files: {e}")
            self.status_var.set("Error")
            self.files_toggle_btn.configure(style='Sidebar.TButton')
    
    def parse_and_create_files(self, git_output):
        """Parse git output and create ChangedFile objects"""
        self.changed_files.clear()
        
        lines = git_output.strip().split('\n') if git_output.strip() else []
        
        for line in lines:
            if not line.strip():
                continue
            
            status, filepath = self.git_manager.parse_porcelain_line(line)
            
            if status is None or filepath is None:
                continue
            
            if self.file_manager.is_path_excluded(filepath):
                continue
            
            # Create paths
            abs_path = os.path.join(self.git_manager.repo_root, filepath)
            
            # Skip directories
            if os.path.exists(abs_path) and os.path.isdir(abs_path):
                continue
            
            try:
                rel_path = Path(abs_path).relative_to(Path(self.git_manager.repo_root)).as_posix()
                changed_file = ChangedFile(abs_path, rel_path, status)
                self.changed_files.append(changed_file)
            except Exception:
                continue
    
    def create_file_widgets(self):
        """Create UI widgets for each changed file"""
        if not self.file_list_panel:
            return
        
        # Clear existing widgets
        self.file_list_panel.clear_all()
        
        # Create widgets for each file
        for i, file_obj in enumerate(self.changed_files):
            self.file_list_panel.create_file_widget(file_obj, i, self.file_list_callbacks)
    
    def toggle_files_section(self):
        """Toggle the horizontal visibility of the Changed Files section"""
        if self.files_section_collapsed:
            # Expand the left panel
            self.main_paned.add(self.file_list_panel.frame, 
                               before=self.main_paned.panes()[0] if self.main_paned.panes() else None)
            self.main_paned.paneconfigure(self.file_list_panel.frame, minsize=400)
            self.files_toggle_btn.config(text="◀")
            self.files_section_collapsed = False
        else:
            # Collapse the left panel
            self.main_paned.forget(self.file_list_panel.frame)
            self.files_toggle_btn.config(text="▶")
            self.files_section_collapsed = True
    
    def toggle_selected_size(self):
        """Toggle between compact and expanded view for Selected section"""
        if self.selected_expanded:
            self.vertical_paned.paneconfig(self.selected_container, height=125)  # Half the original size
            self.expand_selected_btn.config(text="Expand ↓")
            self.selected_expanded = False
        else:
            self.vertical_paned.paneconfig(self.selected_container, height=450)  # Keep expanded size the same
            self.expand_selected_btn.config(text="Collapse ↑")
            self.selected_expanded = True
    
    def toggle_history_section(self):
        """Toggle the chat history panel visibility in the main paned window"""
        if self.history_section_collapsed:
            # Add history panel to the left side of the paned window
            panes = self.main_paned.panes()
            if panes:
                # If files panel is open, add history after it
                # If files panel is closed, add history as first panel
                if len(panes) > 1:
                    # Files panel is open, add history before right panel  
                    self.main_paned.add(self.history_frame, before=panes[-1])
                else:
                    # Files panel is closed, add history before right panel
                    self.main_paned.add(self.history_frame, before=panes[0])
            else:
                # No panes (shouldn't happen), add as first
                self.main_paned.add(self.history_frame)
            
            self.main_paned.paneconfigure(self.history_frame, minsize=500)
            # Change icon color to green when expanded (instead of adding arrow)
            self.history_icon.config(foreground='#10a37f')  # Green accent color
            self.history_section_collapsed = False
            
            # Load and display history
            self.refresh_chat_history_display()
        else:
            # Hide history panel from paned window
            self.main_paned.forget(self.history_frame)
            # Reset icon color back to normal
            self.history_icon.config(foreground=self.theme_manager.colors['text_primary'])
            self.history_section_collapsed = True
    
    # ========== FILE OPERATIONS ==========
    
    def copy_path(self, file_obj, relative=True):
        """Copy file path to clipboard"""
        path = file_obj.rel_path if relative else file_obj.abs_path
        if self.ui_utils.copy_to_clipboard(path):
            path_type = "relative" if relative else "absolute"
            self.status_var.set(f"Copied {path_type} path: {path}")
    
    def copy_and_append(self, file_obj):
        """One-click: copy path + show content + add to analysis"""
        # Copy path
        self.ui_utils.copy_to_clipboard(file_obj.rel_path)
        
        # Load content if not already loaded
        if not file_obj.content_preview and not file_obj.error:
            self.file_manager.load_file_content(file_obj)
        
        # Add to analysis
        self.add_to_analysis(file_obj)
        self.status_var.set("Appended for analysis")
    
    def toggle_content(self, file_obj, index):
        """Toggle file content display"""
        if file_obj.expanded:
            self.file_list_panel.hide_file_content(file_obj)
        else:
            # Load content in thread
            threading.Thread(target=self.load_and_show_content, 
                           args=(file_obj,), daemon=True).start()
    
    def load_and_show_content(self, file_obj):
        """Load content in background thread and show in UI"""
        file_obj.loading = True
        
        # Update UI to show loading
        self.root.after(0, lambda: file_obj.widgets['show_btn'].config(
            text="Loading...", state='disabled'))
        
        # Load content
        success = self.file_manager.load_file_content(file_obj)
        
        # Update UI in main thread
        self.root.after(0, lambda: self.file_list_panel.show_file_content(file_obj))
    
    def toggle_selection(self, file_obj, var):
        """Toggle file selection for analysis"""
        if var.get():
            self.add_to_analysis(file_obj)
        else:
            self.remove_from_analysis(file_obj)
    
    def add_to_analysis(self, file_obj):
        """Add file to analysis pane"""
        if file_obj not in self.selected_files:
            self.selected_files.append(file_obj)
            file_obj.selected_for_analysis = True
            
            # Auto-check the selection checkbox
            if 'select_var' in file_obj.widgets:
                file_obj.widgets['select_var'].set(True)
        
        self.update_selected_display()
    
    def remove_from_analysis(self, file_obj):
        """Remove file from analysis pane"""
        if file_obj in self.selected_files:
            self.selected_files.remove(file_obj)
            file_obj.selected_for_analysis = False
        
        self.update_selected_display()
    
    def remove_file(self, file_obj):
        """Remove file from the changed files list"""
        try:
            if file_obj in self.selected_files:
                self.selected_files.remove(file_obj)
                self.update_selected_display()
            
            if file_obj in self.changed_files:
                self.changed_files.remove(file_obj)
            
            if hasattr(file_obj, 'widgets') and 'frame' in file_obj.widgets:
                file_obj.widgets['frame'].destroy()
            
            # Add to exclude list
            self.file_manager.exclude_paths.append(file_obj.rel_path)
            
            self.status_var.set(f"Removed: {file_obj.rel_path}")
            
        except Exception as e:
            messagebox.showerror("Error", f"Failed to remove file: {e}")
    
    def copy_all_selected(self):
        """Copy all selected files content to clipboard"""
        content = self.selected_text.get('1.0', tk.END).strip()
        if content and content != "No files selected for analysis":
            if self.ui_utils.copy_to_clipboard(content):
                self.status_var.set("All selected files copied to clipboard")
                self.root.after(2000, lambda: self.status_var.set("Ready"))
        else:
            self.status_var.set("No content to copy")
    
    def append_all_files(self):
        """Add all visible changed files to analysis"""
        added_count = 0
        for file_obj in self.changed_files:
            if file_obj not in self.selected_files:
                # Load content if not already loaded
                if not file_obj.content_preview and not file_obj.error:
                    self.file_manager.load_file_content(file_obj)
                
                self.add_to_analysis(file_obj)
                added_count += 1
        
        if added_count > 0:
            self.status_var.set(f"Added {added_count} files to analysis")
            self.root.after(2000, lambda: self.status_var.set("Ready"))
        else:
            self.status_var.set("All files already selected")
    
    def clear_selection(self):
        """Clear all selected files from analysis"""
        self.selected_files.clear()
        
        # Uncheck all checkboxes
        for file_obj in self.changed_files:
            if hasattr(file_obj, 'widgets') and 'select_var' in file_obj.widgets:
                file_obj.widgets['select_var'].set(False)
            file_obj.selected_for_analysis = False
        
        self.update_selected_display()
        self.status_var.set("Selection cleared")
        self.root.after(2000, lambda: self.status_var.set("Ready"))

    def update_selected_display(self):
        """Update the Selected for Analysis pane"""
        self.selected_text.delete('1.0', tk.END)
        
        if not self.selected_files:
            self.selected_text.insert('1.0', "No files selected for analysis")
            return
        
        for i, file_obj in enumerate(self.selected_files, 1):
            header = f"=== File {i}: {file_obj.rel_path} ===\n"
            self.selected_text.insert(tk.INSERT, header)
            
            if file_obj.content_preview:
                self.selected_text.insert(tk.INSERT, file_obj.content_preview + "\n\n")
            else:
                self.selected_text.insert(tk.INSERT, 
                    "[Content not loaded - click 'Show Content' first]\n\n")
    
    # ========== AI INTEGRATION ==========
    
    def send_to_claude_headless(self, prompt_text):
        """Send prompt to Claude Code CLI headlessly and display response"""
        try:
            if not self.project_path:
                self.status_var.set("⚠️ No project loaded")
                return
            
            print(f"DEBUG: Sending prompt to headless Claude in directory: {self.project_path}")
            print(f"DEBUG: Prompt length: {len(prompt_text)} characters")
            
            # Update status to show we're processing
            self.status_var.set("🤖 Sending to Claude Code...")
            
            # Check if Claude is available
            if not self.claude_runner.is_claude_available():
                self.status_var.set("❌ Claude Code CLI not found")
                return
            
            # Get selected files content for context
            files_content = self.selected_text.get('1.0', tk.END).strip()
            if files_content == "No files selected for analysis":
                files_content = ""
            
            # Create comprehensive prompt with file context
            if files_content:
                full_prompt = self.claude_runner.create_session_prompt(files_content, prompt_text)
            else:
                full_prompt = prompt_text
            
            # Execute Claude headlessly in background thread
            def handle_claude_response(success, result, error):
                """Handle Claude response in main thread"""
                if success:
                    print(f"DEBUG: Claude response received successfully")
                    print(f"DEBUG: Response length: {len(result)} characters")
                    
                    # Display the response in the analysis panel
                    self.root.after(0, lambda: self.analysis_panel.display_analysis(
                        result, "Claude Agent", "Headless Claude Code execution"))
                    
                    # Save to chat history
                    self.root.after(0, lambda: self.save_claude_response_to_history(
                        prompt_text, result))
                    
                    self.root.after(0, lambda: self.status_var.set("✅ Claude response received"))
                else:
                    print(f"DEBUG: Claude execution failed: {error}")
                    self.root.after(0, lambda: self.status_var.set(f"❌ Claude failed: {error}"))
                    
                    # Show error in analysis panel
                    error_message = f"Claude Code execution failed:\n\n{error}\n\nPlease check that:\n1. Claude Code CLI is installed and in PATH\n2. You have proper authentication\n3. The prompt is valid"
                    self.root.after(0, lambda: self.analysis_panel.display_analysis(
                        error_message, "Error", "Claude execution error"))
            
            # Define allowed tools for safe file editing
            allowed_tools = [
                "Read",
                "Edit", 
                "Write",
                "MultiEdit",
                "Bash(git diff:*)",
                "Bash(git status:*)"
            ]
            
            # Execute asynchronously to avoid blocking UI
            self.claude_runner.execute_claude_prompt_async(
                prompt_text=full_prompt,
                working_directory=self.project_path,
                callback=handle_claude_response,
                enable_editing=True,
                resume_session_id=self.claude_runner.last_session_id,
                allowed_tools=allowed_tools
            )
            
        except Exception as e:
            print(f"DEBUG: Error in send_to_claude_headless: {e}")
            self.status_var.set("❌ Failed to send to Claude - check console")
    
    def save_claude_response_to_history(self, prompt_text, response_text):
        """Save Claude response to chat history"""
        try:
            if self.chat_history_manager.current_session:
                chat_entry = self.chat_history_manager.add_chat_entry(
                    prompt_type="claude_agent",
                    prompt_text=prompt_text[:200] + "..." if len(prompt_text) > 200 else prompt_text,
                    response_text=response_text,
                    model_used="Claude Code CLI",
                    token_usage={"total_tokens": len(response_text.split())}  # Rough token estimate
                )
                
                # Update history display if visible
                if not self.history_section_collapsed:
                    self.refresh_chat_history_display()
                    
        except Exception as e:
            print(f"DEBUG: Error saving Claude response to history: {e}")
    
    
    def send_to_ai(self, prompt_type):
        """Send selected files to AI for analysis"""
        if not self.api_client.preferred_api:
            messagebox.showwarning("Warning", 
                "No API key found. Please add OPENAI_API_KEY or ANTHROPIC_API_KEY to your .env file")
            return
        
        if not self.selected_files:
            messagebox.showwarning("Warning", "No files selected for analysis")
            return
        
        # Get content and prompt
        content = self.selected_text.get('1.0', tk.END).strip()
        if not content or content == "No files selected for analysis":
            messagebox.showwarning("Warning", "No content to analyze")
            return
        
        # Get prompt based on type
        if prompt_type == 'orchestrator':
            custom_prompt = self.analysis_panel.orchestrator_text.get('1.0', tk.END).strip()
            automated = self.analysis_panel.orchestrator_automated_var.get()
        else:
            custom_prompt = self.analysis_panel.prompt_text.get('1.0', tk.END).strip()
            automated = self.analysis_panel.prompt_automated_var.get()
        
        # Run in background thread
        threading.Thread(target=self.perform_ai_analysis, 
                        args=(content, custom_prompt, prompt_type, automated), 
                        daemon=True).start()
    
    def perform_ai_analysis(self, content, prompt, prompt_type, automated):
        """Perform AI analysis in background"""
        try:
            self.root.after(0, lambda: self.status_var.set("Analyzing..."))
            
            # Call appropriate API
            if self.api_client.preferred_api == 'anthropic':
                result, error = self.api_client.perform_anthropic_analysis(content, prompt)
            else:
                result, error = self.api_client.perform_openai_analysis(content, prompt)
            
            if error:
                self.root.after(0, lambda: messagebox.showwarning("API Error", error))
                self.root.after(0, lambda: self.status_var.set("Ready"))
                return
            
            # Save to chat history
            token_info = self.api_client.get_token_usage_info()
            chat_entry = self.chat_history_manager.add_chat_entry(
                prompt_type=prompt_type,
                prompt_text=prompt,
                response_text=result,
                model_used=self.api_client.selected_model,
                token_usage={
                    'prompt_tokens': self.api_client.last_prompt_tokens,
                    'completion_tokens': self.api_client.last_completion_tokens,
                    'total_tokens': self.api_client.last_prompt_tokens + self.api_client.last_completion_tokens
                }
            )
            
            # Display result in main thread with model information
            self.root.after(0, lambda: self.analysis_panel.display_analysis(
                result, prompt_type, prompt, self.api_client.selected_model))
            self.root.after(0, lambda: self.status_var.set("Analysis complete"))
            
            # If automated checkbox is checked, send result to Claude CLI automatically
            if automated:
                print(f"DEBUG: Automation enabled - will send result to headless Claude")
                self.root.after(1000, lambda: self.send_to_claude_headless(result))  # Small delay to let UI update
            else:
                print(f"DEBUG: Automation disabled - result will not be auto-sent")
            
            # Update token display and refresh history if visible
            self.root.after(0, self.update_token_display)
            if not self.history_section_collapsed:
                self.root.after(0, self.refresh_chat_history_display)
            
        except Exception as e:
            self.root.after(0, lambda: messagebox.showerror("Error", f"Analysis failed: {e}"))
            self.root.after(0, lambda: self.status_var.set("Ready"))


def main():
    """Main entry point"""
    root = tk.Tk()
    app = WorkflowAutomator(root)
    root.mainloop()


if __name__ == "__main__":
    main()
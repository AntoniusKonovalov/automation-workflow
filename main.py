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
from components import ThemeManager, GitManager, FileManager, ChangedFile, APIClient, UIUtils
from components.ui import FileListPanel, AnalysisPanel


class WorkflowAutomator:
    """Main application class - orchestrates all components"""
    
    def __init__(self, root):
        self.root = root
        self.root.title("Git Workflow Automator")
        self.root.geometry("1400x900")
        
        # Initialize managers
        self.theme_manager = ThemeManager(root)
        self.git_manager = GitManager()
        self.file_manager = FileManager()
        self.api_client = APIClient()
        self.ui_utils = UIUtils()
        
        # Application state
        self.project_path = ""
        self.changed_files = []
        self.selected_files = []
        self.files_section_collapsed = True
        self.selected_expanded = False
        
        # Status tracking
        self.status_var = tk.StringVar()
        self.status_var.set("Ready")
        
        # UI Components (will be initialized in setup_ui)
        self.file_list_panel = None
        self.analysis_panel = None
        self.selected_text = None
        self.files_toggle_btn = None
        
        self.setup_ui()
    
    def setup_ui(self):
        """Set up the main UI layout"""
        # Main frame with no padding to maximize space
        main_frame = ttk.Frame(self.root, style='TFrame')
        main_frame.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))
        
        # Configure grid weights
        self.root.columnconfigure(0, weight=1)
        self.root.rowconfigure(0, weight=1)
        main_frame.columnconfigure(0, weight=0)  # Sidebar column - fixed width
        main_frame.columnconfigure(1, weight=1)  # Main content column - expandable
        main_frame.columnconfigure(2, weight=0)  # Button column - fixed width
        main_frame.rowconfigure(2, weight=1)  # Main content row
        main_frame.rowconfigure(3, weight=0)  # Status bar row
        
        # Create header section
        self.setup_header(main_frame)
        
        # Create main content area
        self.setup_main_content(main_frame)
        
        # Create status bar at bottom
        self.setup_status_bar(main_frame)
    
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
        model_menu.grid(row=1, column=2, padx=(0, 10))
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
        self.main_paned.grid(row=2, column=1, columnspan=2,
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
        self.toggle_frame.grid(row=2, column=0, sticky=(tk.N, tk.S, tk.W), padx=(10, 0), pady=(10, 0))
        
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
        
        # Add some spacing
        ttk.Label(sidebar_content, text="", style='TLabel').pack(pady=10)
        
        # Refresh button (moved from header)
        refresh_btn = ttk.Button(sidebar_content, text="🔄",
                                command=self.refresh_with_reset, 
                                style='Sidebar.TButton', width=3)
        refresh_btn.pack()
        self.ui_utils.bind_hover_cursor(refresh_btn)
    
    def setup_right_panel(self, right_frame):
        """Set up the right panel with Selected and Analysis sections"""
        # Create vertical PanedWindow
        vertical_paned = tk.PanedWindow(right_frame, 
                                       orient=tk.VERTICAL,
                                       sashwidth=6,
                                       sashrelief=tk.FLAT,
                                       bg=self.theme_manager.colors['border'])
        vertical_paned.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
        
        # Top section - Selected for Analysis
        selected_container = ttk.Frame(vertical_paned, style='TFrame')
        vertical_paned.add(selected_container, minsize=150, height=250)
        
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
        status_frame.grid(row=3, column=0, columnspan=3, sticky=(tk.W, tk.E), 
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
        
        # Clear tokens button
        clear_tokens_btn = ttk.Button(status_frame, text="🗑️", width=3,
                                     command=self.clear_token_history,
                                     style='TButton')
        clear_tokens_btn.pack(side=tk.RIGHT, padx=(0, 5))
        self.ui_utils.bind_hover_cursor(clear_tokens_btn)
        
        # Current model indicator (right)
        model_indicator = ttk.Label(status_frame, 
                                   text=f"Model: {self.api_client.get_current_model_display_name()}",
                                   style='Secondary.TLabel')
        model_indicator.pack(side=tk.RIGHT, padx=(0, 10))
        self.model_indicator = model_indicator
    
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
        
        self.selected_text = scrolledtext.ScrolledText(
            selected_frame, 
            wrap=tk.WORD, 
            font=self.theme_manager.fonts['code'],
            bg=self.theme_manager.colors['chat_user'],
            fg=self.theme_manager.colors['text_primary'])
        self.selected_text.pack(fill=tk.BOTH, expand=True)
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
    
    def browse_project(self):
        """Browse for project directory"""
        directory = filedialog.askdirectory()
        if directory:
            self.reset_all_content()
            self.path_var.set(directory)
            self.project_path = directory
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
            self.vertical_paned.paneconfig(self.selected_container, height=250)
            self.expand_selected_btn.config(text="Expand ↓")
            self.selected_expanded = False
        else:
            self.vertical_paned.paneconfig(self.selected_container, height=450)
            self.expand_selected_btn.config(text="Collapse ↑")
            self.selected_expanded = True
    
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
            
            # Display result in main thread
            self.root.after(0, lambda: self.analysis_panel.display_analysis(
                result, prompt_type, prompt))
            self.root.after(0, lambda: self.status_var.set("Analysis complete"))
            
            # Update token display
            self.root.after(0, self.update_token_display)
            
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
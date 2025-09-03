import tkinter as tk
from tkinter import ttk, scrolledtext, messagebox, filedialog
import subprocess
import os
import pyperclip
import requests
import json
from pathlib import Path
import threading
from datetime import datetime
import re
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()


class ChangedFile:
    def __init__(self, abs_path, rel_path, status):
        self.abs_path = abs_path
        self.rel_path = rel_path
        self.status = status
        self.expanded = False
        self.loading = False
        self.error = None
        self.content_preview = None
        self.selected_for_analysis = False


class WorkflowAutomator:
    def __init__(self, root):
        self.root = root
        self.root.title("Git Workflow Automator")
        self.root.geometry("1400x900")

        self.project_path = ""
        self.repo_root = ""
        self.openai_api_key = os.getenv('OPENAI_API_KEY', '')
        self.anthropic_api_key = os.getenv('ANTHROPIC_API_KEY', '')
        self.changed_files = []
        self.selected_files = []
        self.exclude_paths = []  # List of paths/patterns to exclude
        self.prompt_expanded = False  # Track prompt section state
        self.orchestrator_expanded = False  # Track orchestrator prompt section state
        self.selected_expanded = False  # Track selected section expanded state
        
        # Determine which API to use based on available keys
        self.preferred_api = self.determine_preferred_api()

        self.setup_ui()

    def determine_preferred_api(self):
        """Determine which API to use based on available keys"""
        if self.anthropic_api_key:
            return 'anthropic'
        elif self.openai_api_key:
            return 'openai'
        else:
            return None

    def get_api_status(self):
        """Get a user-friendly API status message"""
        if self.anthropic_api_key:
            return "Claude (Anthropic) - Ready"
        elif self.openai_api_key:
            return "OpenAI - Ready" 
        else:
            return "No API Key - Add to .env file"

    def parse_porcelain_line(self, line):
        """Parse git status --porcelain line robustly - handles both XY and X formats"""
        print(f"DEBUG PARSE: Input line: '{line}' (len: {len(line) if line else 'None'})")
        
        if not line or len(line) < 2:
            print(f"DEBUG PARSE: Line too short, returning None, None")
            return None, None

        # Git porcelain format can be:
        # 1. Standard: XY<space>filename (X=index, Y=worktree)
        # 2. Simple: X<space>filename (single status char)
        
        # Try to find the space separator
        space_pos = -1
        for i in range(1, min(4, len(line))):  # Check positions 1, 2, 3
            if line[i] in [' ', '\t']:
                space_pos = i
                break
        
        if space_pos == -1:
            print(f"DEBUG PARSE: No space separator found")
            return None, None
        
        status_part = line[:space_pos]
        filepath = line[space_pos + 1:]  # Skip the separator
        
        print(f"DEBUG PARSE: Status part: '{status_part}', Filepath: '{filepath}'")
        
        if not filepath:  # Empty filename
            print(f"DEBUG PARSE: Empty filepath, returning None, None")
            return None, None

        # Normalize status to always be 2 chars (pad with space if needed)
        if len(status_part) == 1:
            # Single char status (like "M") - this means modified in worktree
            status = " " + status_part  # Convert "M" to " M"
        else:
            status = status_part
        
        status = status.strip() if len(status.strip()) > 0 else status

        # Handle rename/copy cases (R/C status)
        if status and (status[0] in 'RC'):
            print(f"DEBUG PARSE: Rename/Copy detected")
            # Format: "old -> new"
            if ' -> ' in filepath:
                old_path, new_path = filepath.split(' -> ', 1)
                print(f"DEBUG PARSE: Rename - Old: '{old_path}', New: '{new_path}'")
                # Use the new path (right side)
                filepath = new_path

        print(f"DEBUG PARSE: Final result - Status: '{status}', Filepath: '{filepath}'")
        return status, filepath

    def set_exclude_paths(self, paths):
        """Set paths/patterns to exclude from file processing"""
        if isinstance(paths, str):
            paths = [paths]
        self.exclude_paths = paths

    def is_path_excluded(self, filepath):
        """Check if a file path should be excluded"""
        if not self.exclude_paths:
            return False
        
        import fnmatch
        
        for pattern in self.exclude_paths:
            # Support both exact matches and glob patterns
            if fnmatch.fnmatch(filepath, pattern) or fnmatch.fnmatch(filepath, f"*/{pattern}") or filepath.startswith(pattern):
                return True
        return False

    def setup_ui(self):
        # Main frame
        main_frame = ttk.Frame(self.root, padding="10")
        main_frame.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))

        # Configure grid weights
        self.root.columnconfigure(0, weight=1)
        self.root.rowconfigure(0, weight=1)
        main_frame.columnconfigure(1, weight=1)
        main_frame.rowconfigure(2, weight=1)

        # Project path selection
        path_label = ttk.Label(main_frame, text="📂 Project Path:", 
                              font=("Segoe UI", 11))
        path_label.grid(row=0, column=0, sticky=tk.W, pady=5)
        self.path_var = tk.StringVar()
        ttk.Entry(main_frame, textvariable=self.path_var, width=50).grid(
            row=0, column=1, sticky=(tk.W, tk.E), padx=5)
        ttk.Button(main_frame, text="Browse", command=self.browse_project).grid(
            row=0, column=2, padx=5)

        # API status and key management
        api_status = self.get_api_status()
        api_label = ttk.Label(main_frame, text=f"🔑 API Status: {api_status}",
                             font=("Segoe UI", 11))
        api_label.grid(row=1, column=0, sticky=tk.W, pady=5)
        
        self.api_key_var = tk.StringVar()
        if self.preferred_api == 'anthropic':
            self.api_key_var.set("Claude API key loaded from .env")
        elif self.preferred_api == 'openai':
            self.api_key_var.set("OpenAI API key loaded from .env")
        else:
            self.api_key_var.set("No API key found in .env file")
            
        api_entry = ttk.Entry(main_frame, textvariable=self.api_key_var, 
                             width=50, state='readonly')
        api_entry.grid(row=1, column=1, sticky=(tk.W, tk.E), padx=5)
        
        ttk.Button(main_frame, text="Refresh Files",
                   command=self.refresh_changed_files).grid(row=1, column=2, padx=5)

        # Paned window for split view with visible sash
        # Use tk.PanedWindow instead of ttk for better customization
        paned = tk.PanedWindow(main_frame, 
                              orient=tk.HORIZONTAL,
                              sashwidth=15,
                              sashrelief=tk.RAISED,
                              bg='#d0d0d0',
                              sashcursor='sb_h_double_arrow',
                              showhandle=True,
                              handlesize=10,
                              handlepad=50,
                              opaqueresize=True)
        paned.grid(row=2, column=0, columnspan=3,
                   sticky=(tk.W, tk.E, tk.N, tk.S), pady=10)

        # Left panel - Changed files with enhanced UI
        left_frame = ttk.Frame(paned)
        paned.add(left_frame, minsize=400)

        # Changed files header with collapse button and restart
        files_header_frame = ttk.Frame(left_frame)
        files_header_frame.pack(fill=tk.X, pady=5)
        
        files_label = ttk.Label(files_header_frame, text="📁 Changed Files:", 
                               font=("Segoe UI", 12, "bold"))
        files_label.pack(side=tk.LEFT)
        
        # Button container on the right
        header_buttons = ttk.Frame(files_header_frame)
        header_buttons.pack(side=tk.RIGHT)
        
        ttk.Button(header_buttons, text="Restart",
                   command=self.restart_application).pack(side=tk.LEFT, padx=(0, 5))
        ttk.Button(header_buttons, text="Collapse All",
                   command=self.collapse_all_files).pack(side=tk.LEFT)

        # Scrollable frame for file list
        canvas_frame = ttk.Frame(left_frame)
        canvas_frame.pack(fill=tk.BOTH, expand=True, pady=5)

        self.canvas = tk.Canvas(canvas_frame)
        scrollbar_v = ttk.Scrollbar(
            canvas_frame, orient=tk.VERTICAL, command=self.canvas.yview)
        self.scrollable_frame = ttk.Frame(self.canvas)

        self.scrollable_frame.bind(
            "<Configure>",
            lambda e: self.canvas.configure(
                scrollregion=self.canvas.bbox("all"))
        )

        self.canvas.create_window(
            (0, 0), window=self.scrollable_frame, anchor="nw")
        self.canvas.configure(yscrollcommand=scrollbar_v.set)

        self.canvas.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        scrollbar_v.pack(side=tk.RIGHT, fill=tk.Y)

        # Bind mouse wheel to canvas
        self.canvas.bind_all("<MouseWheel>", self._on_mousewheel)

        # Right panel - Contains vertically split Selected and Analysis sections
        right_frame = ttk.Frame(paned)
        paned.add(right_frame, minsize=400)

        # Create a vertical PanedWindow to split Selected and Analysis 50/50
        # Use tk.PanedWindow for better visibility
        vertical_paned = tk.PanedWindow(right_frame, 
                                       orient=tk.VERTICAL,
                                       sashwidth=15,
                                       sashrelief=tk.RAISED,
                                       bg='#d0d0d0',
                                       sashcursor='sb_v_double_arrow',
                                       showhandle=True,
                                       handlesize=10,
                                       handlepad=50,
                                       opaqueresize=True)
        vertical_paned.pack(fill=tk.BOTH, expand=True)

        # Top section - Selected for Analysis (smaller by default)
        selected_container = ttk.Frame(vertical_paned)
        vertical_paned.add(selected_container, minsize=150, height=250)  # Start smaller

        # Selected files header
        selected_label_frame = ttk.Frame(selected_container)
        selected_label_frame.pack(fill=tk.X, padx=5, pady=5)

        selected_label = ttk.Label(selected_label_frame, text="📋 Selected for Analysis:",
                                  font=("Segoe UI", 12, "bold"))
        selected_label.pack(side=tk.LEFT)
        
        # Button frame for multiple buttons
        button_frame = ttk.Frame(selected_label_frame)
        button_frame.pack(side=tk.RIGHT)
        
        self.expand_selected_btn = ttk.Button(button_frame, text="Expand ↓",
                   command=self.toggle_selected_size)
        self.expand_selected_btn.pack(side=tk.LEFT, padx=2)
        ttk.Button(button_frame, text="Copy All",
                   command=self.copy_all_selected).pack(side=tk.LEFT, padx=2)
        ttk.Button(button_frame, text="Append All",
                   command=self.append_all_files).pack(side=tk.LEFT, padx=2)
        ttk.Button(button_frame, text="Clear All",
                   command=self.clear_selection).pack(side=tk.LEFT, padx=2)

        # Selected files text area
        selected_frame = ttk.Frame(selected_container)
        selected_frame.pack(fill=tk.BOTH, expand=True, padx=5, pady=(0, 5))

        self.selected_text = scrolledtext.ScrolledText(
            selected_frame, wrap=tk.WORD, font=("Consolas", 9))
        self.selected_text.pack(fill=tk.BOTH, expand=True)

        # Bottom section - AI Analysis (larger by default)
        analysis_container = ttk.Frame(vertical_paned)
        vertical_paned.add(analysis_container, minsize=300)  # Larger for AI analysis
        
        # Store reference to vertical paned window
        self.vertical_paned = vertical_paned
        self.selected_container = selected_container
        self.analysis_container = analysis_container

        # Analysis header and buttons
        analysis_header_frame = ttk.Frame(analysis_container)
        analysis_header_frame.pack(fill=tk.X, padx=5, pady=5)

        # Dynamic label text based on available API
        if self.preferred_api == 'anthropic':
            ai_button_text = "Send to Claude"
            analysis_label_text = "🤖 Claude Analysis:"
        elif self.preferred_api == 'openai':
            ai_button_text = "Send to ChatGPT"
            analysis_label_text = "🤖 ChatGPT Analysis:"
        else:
            ai_button_text = "Send to AI (No Key)"
            analysis_label_text = "🤖 AI Analysis:"

        analysis_label = ttk.Label(analysis_header_frame, text=analysis_label_text,
                                  font=("Segoe UI", 12, "bold"))
        analysis_label.pack(side=tk.LEFT)

        # Analysis buttons
        analysis_buttons = ttk.Frame(analysis_header_frame)
        analysis_buttons.pack(side=tk.RIGHT)
        
        self.toggle_orchestrator_btn = ttk.Button(analysis_buttons, text="Orchestrator ▼",
                   command=self.toggle_orchestrator_section)
        self.toggle_orchestrator_btn.pack(side=tk.LEFT, padx=2)
        
        self.toggle_prompt_btn = ttk.Button(analysis_buttons, text="Prompt ▼",
                   command=self.toggle_prompt_section)
        self.toggle_prompt_btn.pack(side=tk.LEFT, padx=2)

        # Collapsible orchestrator section (hidden by default)
        self.orchestrator_frame = ttk.Frame(analysis_container)
        # Don't pack yet - will be toggled
        
        orchestrator_label = ttk.Label(self.orchestrator_frame, text="🎭 Orchestrator Prompt:",
                                      font=("Segoe UI", 11))
        orchestrator_label.pack(anchor=tk.W, padx=5, pady=(5, 2))
        
        # Orchestrator text area with default text
        orchestrator_text_frame = ttk.Frame(self.orchestrator_frame)
        orchestrator_text_frame.pack(fill=tk.X, padx=5, pady=(0, 5))
        
        self.orchestrator_text = tk.Text(orchestrator_text_frame, height=4, wrap=tk.WORD,
                                        font=("Consolas", 9))
        self.orchestrator_text.pack(side=tk.LEFT, fill=tk.X, expand=True)
        
        # Add scrollbar to orchestrator prompt
        orchestrator_scroll = ttk.Scrollbar(orchestrator_text_frame, command=self.orchestrator_text.yview)
        orchestrator_scroll.pack(side=tk.RIGHT, fill=tk.Y)
        self.orchestrator_text.config(yscrollcommand=orchestrator_scroll.set)
        
        # Add Send button for orchestrator
        orchestrator_btn_frame = ttk.Frame(self.orchestrator_frame)
        orchestrator_btn_frame.pack(fill=tk.X, padx=5, pady=(0, 5))
        
        if self.preferred_api == 'anthropic':
            orch_send_text = "Send to Claude"
        elif self.preferred_api == 'openai':
            orch_send_text = "Send to ChatGPT"
        else:
            orch_send_text = "Send to AI"
            
        ttk.Button(orchestrator_btn_frame, text=orch_send_text,
                   command=lambda: self.send_to_ai_with_specific_prompt('orchestrator')).pack(side=tk.LEFT)
        
        # Set default orchestrator prompt text
        default_orchestrator = """Generate a text prompt for orchestrator Claude agent with clear instructions for fixing this issue.

Instructions for the orchestrator:
- Analyze the code changes and identify the root cause
- Create a step-by-step plan to resolve the issue
- Delegate tasks to specialized agents based on their expertise
- Do not add any code directly, use agents specified for their tasks
- Coordinate between different agents to ensure smooth workflow"""
        self.orchestrator_text.insert('1.0', default_orchestrator)
        
        # Collapsible prompt section (hidden by default)
        self.prompt_frame = ttk.Frame(analysis_container)
        # Don't pack yet - will be toggled
        
        prompt_label = ttk.Label(self.prompt_frame, text="✏️ AI Prompt:",
                                font=("Segoe UI", 11))
        prompt_label.pack(anchor=tk.W, padx=5, pady=(5, 2))
        
        # Prompt text area with default text
        prompt_text_frame = ttk.Frame(self.prompt_frame)
        prompt_text_frame.pack(fill=tk.X, padx=5, pady=(0, 5))
        
        self.prompt_text = tk.Text(prompt_text_frame, height=3, wrap=tk.WORD,
                                  font=("Consolas", 9))
        self.prompt_text.pack(side=tk.LEFT, fill=tk.X, expand=True)
        
        # Add scrollbar to prompt
        prompt_scroll = ttk.Scrollbar(prompt_text_frame, command=self.prompt_text.yview)
        prompt_scroll.pack(side=tk.RIGHT, fill=tk.Y)
        self.prompt_text.config(yscrollcommand=prompt_scroll.set)
        
        # Add Send button for regular prompt
        prompt_btn_frame = ttk.Frame(self.prompt_frame)
        prompt_btn_frame.pack(fill=tk.X, padx=5, pady=(0, 5))
        
        if self.preferred_api == 'anthropic':
            prompt_send_text = "Send to Claude"
        elif self.preferred_api == 'openai':
            prompt_send_text = "Send to ChatGPT"
        else:
            prompt_send_text = "Send to AI"
            
        ttk.Button(prompt_btn_frame, text=prompt_send_text,
                   command=lambda: self.send_to_ai_with_specific_prompt('prompt')).pack(side=tk.LEFT)
        
        # Set default prompt text
        default_prompt = "Make a deep analysis of these code changes. Focus on:\n- Code quality and potential issues\n- Suggestions for improvements\n- Security considerations\n- Performance implications"
        self.prompt_text.insert('1.0', default_prompt)
        
        # AI response text area
        analysis_frame = ttk.Frame(analysis_container)
        analysis_frame.pack(fill=tk.BOTH, expand=True, padx=5, pady=(0, 5))

        self.analysis_text = scrolledtext.ScrolledText(
            analysis_frame, wrap=tk.WORD)
        self.analysis_text.pack(fill=tk.BOTH, expand=True)

        # Status bar
        self.status_var = tk.StringVar()
        self.status_var.set("Ready")
        status_bar = ttk.Label(
            main_frame, textvariable=self.status_var, relief=tk.SUNKEN)
        status_bar.grid(row=3, column=0, columnspan=3,
                        sticky=(tk.W, tk.E), pady=5)

    def _on_mousewheel(self, event):
        self.canvas.yview_scroll(int(-1*(event.delta/120)), "units")

    def browse_project(self):
        directory = filedialog.askdirectory()
        if directory:
            self.path_var.set(directory)
            self.project_path = directory
            self.refresh_changed_files()

    def find_repo_root(self, start_path):
        """Find git repository root using git rev-parse"""
        try:
            result = subprocess.run(
                ['git', 'rev-parse', '--show-toplevel'],
                cwd=start_path,
                capture_output=True,
                text=True,
                check=True
            )
            return result.stdout.strip()
        except subprocess.CalledProcessError:
            # Fallback: walk up directories to find .git
            current = Path(start_path)
            for parent in [current] + list(current.parents):
                if (parent / '.git').exists():
                    return str(parent)
            return start_path

    def refresh_changed_files(self):
        if not self.project_path:
            messagebox.showwarning(
                "Warning", "Please select a project path first")
            return

        try:
            self.status_var.set("Refreshing changed files...")

            # Find repository root properly
            self.repo_root = self.find_repo_root(self.project_path)
            print(f"DEBUG: Project path: {self.project_path}")
            print(f"DEBUG: Repository root: {self.repo_root}")

            # Get changed files using git with expanded untracked files
            # Use -u flag to show individual untracked files instead of directories
            result = subprocess.run(
                ['git', 'status', '--porcelain', '-u'],
                cwd=self.repo_root,
                capture_output=True,
                text=True,
                check=True
            )

            print(f"DEBUG: Git status raw output:")
            print(f"'{result.stdout}'")
            print(f"DEBUG: Git status lines count: {len(result.stdout.strip().split())}")

            self.changed_files = []

            # Clear existing UI
            for widget in self.scrollable_frame.winfo_children():
                widget.destroy()

            lines = result.stdout.strip().split('\n')
            print(f"DEBUG: Processing {len(lines)} lines")
            
            for i, line in enumerate(lines):
                print(f"DEBUG: Line {i}: '{line}' (length: {len(line)})")
                
                if line.strip():
                    # Parse using robust regex method
                    status, filepath = self.parse_porcelain_line(line)
                    print(f"DEBUG: Parsed - Status: '{status}', Filepath: '{filepath}'")
                    
                    if status is None or filepath is None:
                        print(f"DEBUG: Skipping unparseable line: '{line}'")
                        continue

                    # Check if path should be excluded
                    if self.is_path_excluded(filepath):
                        print(f"DEBUG: Excluding path: '{filepath}'")
                        continue

                    # Create absolute path and proper relative path
                    abs_path = os.path.join(self.repo_root, filepath)
                    
                    # Skip directories - we only want files
                    if os.path.exists(abs_path) and os.path.isdir(abs_path):
                        print(f"DEBUG: Skipping directory: '{filepath}'")
                        continue
                    
                    # For nonexistent files (deleted files), we still want to show them
                    # but for existing items that aren't files, we skip them
                    if os.path.exists(abs_path) and not os.path.isfile(abs_path):
                        print(f"DEBUG: Skipping non-file: '{filepath}' (exists but not a regular file)")
                        continue
                    
                    try:
                        rel_path = Path(abs_path).relative_to(Path(self.repo_root)).as_posix()
                        print(f"DEBUG: Created paths - Abs: '{abs_path}', Rel: '{rel_path}'")
                        
                        changed_file = ChangedFile(abs_path, rel_path, status)
                        self.changed_files.append(changed_file)
                        
                    except Exception as path_error:
                        print(f"DEBUG: Path error for '{filepath}': {path_error}")
                        continue
                else:
                    print(f"DEBUG: Empty line {i}, skipping")

            print(f"DEBUG: Final changed_files count: {len(self.changed_files)}")
            for i, cf in enumerate(self.changed_files):
                print(f"DEBUG: File {i}: '{cf.rel_path}' [{cf.status}]")

            # Create UI for each file
            self.create_file_widgets()
            self.status_var.set(
                f"Found {len(self.changed_files)} changed files")

        except subprocess.CalledProcessError as e:
            print(f"DEBUG: Git command error: {e}")
            messagebox.showerror("Error", f"Git command failed: {e}")
            self.status_var.set("Error getting changed files")
        except Exception as e:
            print(f"DEBUG: General error: {e}")
            messagebox.showerror("Error", f"Failed to get changed files: {e}")
            self.status_var.set("Error")

    def create_file_widgets(self):
        """Create UI widgets for each changed file"""
        # Calculate optimal width based on longest path
        if self.changed_files:
            max_path_length = max(len(file_obj.rel_path) for file_obj in self.changed_files)
            # Estimate character width in pixels (approximate for Consolas font)
            estimated_width = min(max_path_length * 7 + 400, 800)  # Cap at 800px
            self.scrollable_frame.config(width=estimated_width)
        
        for i, file_obj in enumerate(self.changed_files):
            # Main file frame
            file_frame = ttk.Frame(self.scrollable_frame,
                                   relief=tk.RIDGE, borderwidth=1)
            file_frame.pack(fill=tk.X, padx=5, pady=2)

            # File header frame
            header_frame = ttk.Frame(file_frame)
            header_frame.pack(fill=tk.X, padx=5, pady=2)

            # Status and filename
            status_label = ttk.Label(header_frame, text=f"[{file_obj.status}]",
                                     foreground="blue", font=("TkDefaultFont", 9, "bold"))
            status_label.pack(side=tk.LEFT, padx=2)

            filename_label = ttk.Label(header_frame, text=file_obj.rel_path,
                                       font=("Consolas", 9))
            filename_label.pack(side=tk.LEFT, padx=5)

            # Buttons frame
            buttons_frame = ttk.Frame(header_frame)
            buttons_frame.pack(side=tk.RIGHT)

            # Copy Path dropdown
            path_var = tk.StringVar(value="Copy Path ▼")
            path_menu = ttk.Menubutton(
                buttons_frame, textvariable=path_var, width=12)
            path_menu.pack(side=tk.LEFT, padx=1)

            path_dropdown = tk.Menu(path_menu, tearoff=0)
            path_dropdown.add_command(label="Copy Relative Path",
                                      command=lambda f=file_obj: self.copy_path(f, relative=True))
            path_dropdown.add_command(label="Copy Absolute Path",
                                      command=lambda f=file_obj: self.copy_path(f, relative=False))
            path_menu.config(menu=path_dropdown)

            # Copy & Append button (new one-click workflow)
            copy_append_btn = ttk.Button(buttons_frame, text="Copy & Append", width=13,
                                         command=lambda f=file_obj: self.copy_and_append(f))
            copy_append_btn.pack(side=tk.LEFT, padx=1)

            # Show Content button
            show_btn = ttk.Button(buttons_frame, text="Show Content", width=12,
                                  command=lambda f=file_obj, idx=i: self.toggle_content(f, idx))
            show_btn.pack(side=tk.LEFT, padx=1)

            # Select checkbox
            select_var = tk.BooleanVar()
            select_cb = ttk.Checkbutton(buttons_frame, text="Select", variable=select_var,
                                        command=lambda f=file_obj, var=select_var: self.toggle_selection(f, var))
            select_cb.pack(side=tk.LEFT, padx=1)

            # Remove button
            remove_btn = ttk.Button(buttons_frame, text="Remove", width=8,
                                    command=lambda f=file_obj: self.remove_file(f))
            remove_btn.pack(side=tk.LEFT, padx=1)

            # Store references for later access
            file_obj.widgets = {
                'frame': file_frame,
                'show_btn': show_btn,
                'select_var': select_var,
                'select_cb': select_cb
            }

    def copy_path(self, file_obj, relative=True):
        """Copy file path to clipboard"""
        path = file_obj.rel_path if relative else file_obj.abs_path
        pyperclip.copy(path)
        path_type = "relative" if relative else "absolute"
        self.status_var.set(f"Copied {path_type} path: {path}")

        # Show toast-like feedback
        self.root.after(2000, lambda: self.status_var.set(
            "Ready") if self.status_var.get().startswith("Copied") else None)

    def copy_and_append(self, file_obj):
        """One-click: copy path + inline content + add to analysis pane"""
        # 1. Copy relative path to clipboard
        pyperclip.copy(file_obj.rel_path)
        self.status_var.set("Path copied")

        # 2. Expand content inline if not already expanded
        if not file_obj.expanded:
            self.expand_content(file_obj)

        # 3. Auto-select for analysis and add to right pane
        self.append_to_analysis_pane(file_obj)

        # Update status with multiple actions completed
        self.root.after(1000, lambda: self.status_var.set(
            "Appended for analysis"))
        self.root.after(3000, lambda: self.status_var.set(
            "Ready") if self.status_var.get() == "Appended for analysis" else None)

    def append_to_analysis_pane(self, file_obj):
        """Centralized function to add file to analysis pane"""
        # Auto-check the selection checkbox
        if 'select_var' in file_obj.widgets:
            file_obj.widgets['select_var'].set(True)

        # Mark as selected
        file_obj.selected_for_analysis = True

        # Add to selected files list if not already there
        if file_obj not in self.selected_files:
            self.selected_files.append(file_obj)

        # Update the right pane display
        self.update_selected_display()
    
    def append_all_files(self):
        """Append all currently visible changed files to the analysis pane"""
        if not self.changed_files:
            messagebox.showwarning("Warning", "No changed files to append")
            return
        
        # Count how many new files will be added
        new_files_count = 0
        total_files = len(self.changed_files)
        
        for file_obj in self.changed_files:
            # Add file to selection if not already there
            if file_obj not in self.selected_files:
                new_files_count += 1
                # Auto-check the selection checkbox
                if 'select_var' in file_obj.widgets:
                    file_obj.widgets['select_var'].set(True)
                
                # Mark as selected
                file_obj.selected_for_analysis = True
                self.selected_files.append(file_obj)
            
            # Load content for files that don't have it yet
            if not file_obj.expanded and not file_obj.loading and file_obj.content_preview is None:
                # Load content synchronously for append all
                self._load_file_content_sync(file_obj)
        
        # Update the display after all content is loaded
        self.update_selected_display()
        
        # Show status feedback
        if new_files_count > 0:
            self.status_var.set(f"Appended {new_files_count} files for analysis (Total: {total_files})")
            self.root.after(3000, lambda: self.status_var.set("Ready") if self.status_var.get().startswith("Appended") else None)
        else:
            self.status_var.set("All files already selected")
            self.root.after(2000, lambda: self.status_var.set("Ready") if self.status_var.get().startswith("All files") else None)
    
    def collapse_all_files(self):
        """Collapse all expanded file content in the Changed Files section"""
        collapsed_count = 0
        
        print(f"Starting collapse_all_files. Total files: {len(self.changed_files)}")
        
        for i, file_obj in enumerate(self.changed_files):
            print(f"File {i}: {file_obj.rel_path}, expanded: {file_obj.expanded}")
            if file_obj.expanded:
                self.collapse_content(file_obj)
                collapsed_count += 1
                print(f"  Collapsed file {i}")
        
        print(f"Collapse complete. Collapsed {collapsed_count} files")
        
        # Show status feedback
        if collapsed_count > 0:
            self.status_var.set(f"Collapsed {collapsed_count} expanded files")
            self.root.after(2000, lambda: self.status_var.set("Ready") if self.status_var.get().startswith("Collapsed") else None)
        else:
            self.status_var.set("No files are currently expanded")
            self.root.after(2000, lambda: self.status_var.set("Ready") if self.status_var.get().startswith("No files") else None)

    def toggle_content(self, file_obj, file_index):
        """Toggle file content display"""
        if file_obj.expanded:
            self.collapse_content(file_obj)
        else:
            self.expand_content(file_obj)

    def expand_content(self, file_obj):
        """Expand file to show content"""
        if file_obj.loading:
            return

        file_obj.loading = True
        file_obj.widgets['show_btn'].config(
            text="Loading...", state='disabled')

        # Load content in thread to avoid blocking
        threading.Thread(target=self._load_file_content_thread,
                         args=(file_obj,), daemon=True).start()

    def _load_file_content_sync(self, file_obj):
        """Load file content synchronously (for append all)"""
        try:
            if not os.path.exists(file_obj.abs_path):
                file_obj.content_preview = None
                file_obj.error = "File not found (deleted/renamed)"
                return
                
            if os.path.isdir(file_obj.abs_path):
                file_obj.content_preview = None
                file_obj.error = "Directory (not previewable)"
                return
                
            if not os.path.isfile(file_obj.abs_path):
                file_obj.content_preview = None
                file_obj.error = "Not a regular file"
                return

            # Try to read file content
            content = None
            encodings = ['utf-8', 'latin-1', 'cp1252']

            for encoding in encodings:
                try:
                    with open(file_obj.abs_path, 'r', encoding=encoding) as f:
                        content = f.read()
                    break
                except UnicodeDecodeError:
                    continue
                except PermissionError:
                    file_obj.content_preview = None
                    file_obj.error = "Permission denied"
                    return
                except OSError as e:
                    file_obj.content_preview = None
                    file_obj.error = f"Cannot read: {str(e)}"
                    return

            if content is None:
                file_obj.content_preview = None
                file_obj.error = "Binary or unsupported encoding"
            elif len(content) > 50000:  # Large file
                content = content[:50000] + "\n\n... (Content truncated - file is large) ..."
                file_obj.content_preview = content
                file_obj.error = None
            else:
                file_obj.content_preview = content
                file_obj.error = None

        except Exception as e:
            file_obj.content_preview = None
            file_obj.error = f"Error: {str(e)}"
    
    def _load_file_content_thread(self, file_obj):
        """Load file content in background thread"""
        try:
            if not os.path.exists(file_obj.abs_path):
                file_obj.content_preview = None
                file_obj.error = "File not found (deleted/renamed)"
                return
                
            if os.path.isdir(file_obj.abs_path):
                file_obj.content_preview = None
                file_obj.error = "Directory (not previewable) - switch to expanded listing to see files"
                return
                
            if not os.path.isfile(file_obj.abs_path):
                file_obj.content_preview = None
                file_obj.error = "Not a regular file (symlink/special file)"
                return

            # Try to read file content
            content = None
            encodings = ['utf-8', 'latin-1', 'cp1252']

            for encoding in encodings:
                try:
                    with open(file_obj.abs_path, 'r', encoding=encoding) as f:
                        content = f.read()
                    break
                except UnicodeDecodeError:
                    continue
                except PermissionError:
                    file_obj.content_preview = None
                    file_obj.error = "Permission denied - cannot read file"
                    return
                except OSError as e:
                    file_obj.content_preview = None
                    file_obj.error = f"Cannot read file: {str(e)}"
                    return

            if content is None:
                file_obj.content_preview = None
                file_obj.error = "Binary or unsupported encoding - preview disabled"
            elif len(content) > 50000:  # Large file soft limit
                content = content[:50000] + \
                    "\n\n... (Content truncated - file is large) ..."
                file_obj.content_preview = content
                file_obj.error = None
            else:
                file_obj.content_preview = content
                file_obj.error = None

        except Exception as e:
            file_obj.content_preview = None
            file_obj.error = f"Unexpected error: {str(e)}"

        # Update UI in main thread
        self.root.after(0, self._show_content_ui, file_obj)

    def _show_content_ui(self, file_obj):
        """Show content in UI (called from main thread)"""
        file_obj.loading = False
        file_obj.expanded = True

        if file_obj.error:
            # Show error
            error_frame = ttk.Frame(file_obj.widgets['frame'], style='TFrame')
            error_frame.pack(fill=tk.X, padx=20, pady=5)

            error_label = ttk.Label(
                error_frame, text=file_obj.error, foreground="red")
            error_label.pack(side=tk.LEFT)

            refresh_btn = ttk.Button(error_frame, text="Refresh",
                                     command=lambda: self.refresh_changed_files())
            refresh_btn.pack(side=tk.RIGHT)

            file_obj.widgets['content_frame'] = error_frame
        else:
            # Show content
            content_frame = ttk.Frame(file_obj.widgets['frame'])
            content_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=5)

            # Content controls
            controls_frame = ttk.Frame(content_frame)
            controls_frame.pack(fill=tk.X, pady=2)

            ttk.Button(controls_frame, text="Copy Content",
                       command=lambda: self.copy_content(file_obj)).pack(side=tk.LEFT, padx=2)

            # Content text area
            content_text = scrolledtext.ScrolledText(content_frame, height=15,
                                                     font=("Consolas", 9), wrap=tk.NONE)
            content_text.pack(fill=tk.BOTH, expand=True, pady=2)
            content_text.insert('1.0', file_obj.content_preview)
            content_text.config(state='disabled')  # Read-only

            file_obj.widgets['content_frame'] = content_frame
            file_obj.widgets['content_text'] = content_text

        file_obj.widgets['show_btn'].config(text="Collapse", state='normal')

    def collapse_content(self, file_obj):
        """Collapse file content"""
        try:
            if 'content_frame' in file_obj.widgets:
                file_obj.widgets['content_frame'].destroy()
                del file_obj.widgets['content_frame']
                if 'content_text' in file_obj.widgets:
                    del file_obj.widgets['content_text']

            file_obj.expanded = False
            if 'show_btn' in file_obj.widgets:
                file_obj.widgets['show_btn'].config(text="Show Content")
        except Exception as e:
            print(f"Error collapsing content for {file_obj.rel_path}: {e}")
            # Reset the state anyway
            file_obj.expanded = False

    def copy_content(self, file_obj):
        """Copy file content to clipboard"""
        if file_obj.content_preview:
            pyperclip.copy(file_obj.content_preview)
            self.status_var.set(f"Content copied: {file_obj.rel_path}")
            self.root.after(2000, lambda: self.status_var.set(
                "Ready") if self.status_var.get().startswith("Content copied") else None)

    def toggle_selection(self, file_obj, var):
        """Toggle file selection for analysis"""
        if var.get():
            # Use centralized append function
            self.append_to_analysis_pane(file_obj)
        else:
            # Remove from selection
            file_obj.selected_for_analysis = False
            if file_obj in self.selected_files:
                self.selected_files.remove(file_obj)
            self.update_selected_display()

    def update_selected_display(self):
        """Update the Selected for Analysis pane with alternating colors for file headers"""
        self.selected_text.delete('1.0', tk.END)

        if not self.selected_files:
            self.selected_text.insert('1.0', "No files selected for analysis")
            return

        # Configure alternating background colors for file headers
        self.selected_text.tag_configure(
            "file_header_1", background="#E8F4FD", font=("TkDefaultFont", 9, "bold"))
        self.selected_text.tag_configure(
            "file_header_2", background="#FFF2E8", font=("TkDefaultFont", 9, "bold"))
        self.selected_text.tag_configure(
            "file_header_3", background="#F0F8E8", font=("TkDefaultFont", 9, "bold"))
        self.selected_text.tag_configure(
            "file_header_4", background="#F8E8F0", font=("TkDefaultFont", 9, "bold"))

        for i, file_obj in enumerate(self.selected_files, 1):
            # Insert file header with alternating background
            header_line = f"=== File {i}: {file_obj.rel_path} ===\n"
            # Cycle through 4 colors
            header_tag = f"file_header_{((i-1) % 4) + 1}"

            start_pos = self.selected_text.index(tk.INSERT)
            self.selected_text.insert(tk.INSERT, header_line)
            end_pos = self.selected_text.index(tk.INSERT)

            # Apply background color to the header line only
            self.selected_text.tag_add(
                header_tag, start_pos, f"{start_pos.split('.')[0]}.{int(start_pos.split('.')[1]) + len(header_line) - 1}")

            # Insert content without special formatting
            if file_obj.content_preview:
                self.selected_text.insert(
                    tk.INSERT, file_obj.content_preview + "\n\n")
            else:
                self.selected_text.insert(
                    tk.INSERT, "[Content not loaded - click 'Show Content' first]\n\n")

    def clear_selection(self):
        """Clear all selected files"""
        for file_obj in self.selected_files:
            file_obj.selected_for_analysis = False
            if 'select_var' in file_obj.widgets:
                file_obj.widgets['select_var'].set(False)

        self.selected_files.clear()
        self.update_selected_display()

    def copy_all_selected(self):
        """Copy all selected files content to clipboard"""
        if not self.selected_files:
            messagebox.showwarning("Warning", "No files selected")
            return

        content = self.selected_text.get('1.0', tk.END).strip()
        if content:
            pyperclip.copy(content)
            self.status_var.set(
                f"Copied {len(self.selected_files)} selected files to clipboard")
            self.root.after(3000, lambda: self.status_var.set(
                "Ready") if self.status_var.get().startswith("Copied") else None)

    def send_to_ai_with_specific_prompt(self, prompt_type):
        """Send selected files to AI with specific prompt type (orchestrator or prompt)"""
        if not self.preferred_api:
            messagebox.showwarning(
                "Warning", "No API key found. Please add OPENAI_API_KEY or ANTHROPIC_API_KEY to your .env file")
            return

        if not self.selected_files:
            messagebox.showwarning("Warning", "No files selected for analysis")
            return

        content = self.selected_text.get('1.0', tk.END).strip()
        if not content or content == "No files selected for analysis":
            messagebox.showwarning("Warning", "No content to analyze")
            return

        # Get the specific prompt based on type
        if prompt_type == 'orchestrator':
            custom_prompt = self.orchestrator_text.get('1.0', tk.END).strip()
        else:  # prompt_type == 'prompt'
            custom_prompt = self.prompt_text.get('1.0', tk.END).strip()

        # Run analysis in separate thread
        if self.preferred_api == 'anthropic':
            threading.Thread(target=self.perform_anthropic_analysis,
                           args=(content, custom_prompt), daemon=True).start()
        elif self.preferred_api == 'openai':
            threading.Thread(target=self.perform_openai_analysis,
                           args=(content, custom_prompt), daemon=True).start()
    
    def send_to_ai(self):
        """Send selected files to AI for analysis (supports both OpenAI and Anthropic)"""
        if not self.preferred_api:
            messagebox.showwarning(
                "Warning", "No API key found. Please add OPENAI_API_KEY or ANTHROPIC_API_KEY to your .env file")
            return

        if not self.selected_files:
            messagebox.showwarning("Warning", "No files selected for analysis")
            return

        content = self.selected_text.get('1.0', tk.END).strip()
        if not content or content == "No files selected for analysis":
            messagebox.showwarning("Warning", "No content to analyze")
            return

        # Run analysis in separate thread
        if self.preferred_api == 'anthropic':
            threading.Thread(target=self.perform_anthropic_analysis,
                           args=(content,), daemon=True).start()
        elif self.preferred_api == 'openai':
            threading.Thread(target=self.perform_openai_analysis,
                           args=(content,), daemon=True).start()

    def perform_anthropic_analysis(self, content, custom_prompt=None):
        """Perform Claude analysis in background thread"""
        try:
            import anthropic
            
            self.status_var.set("Analyzing with Claude...")
            # Show progress in analysis window
            self.root.after(0, lambda: self.analysis_text.delete(1.0, tk.END))
            self.root.after(0, lambda: self.analysis_text.insert(1.0, "Processing request with Claude...\n"))
            
            # Use provided prompt or get default
            if custom_prompt is None:
                # Get custom prompt - use orchestrator if expanded, otherwise regular prompt
                if self.orchestrator_expanded:
                    custom_prompt = self.orchestrator_text.get('1.0', tk.END).strip()
                else:
                    custom_prompt = self.prompt_text.get('1.0', tk.END).strip()
            
            client = anthropic.Anthropic(api_key=self.anthropic_api_key)
            
            message = client.messages.create(
                model="claude-3-haiku-20240307",
                max_tokens=2000,
                temperature=0.7,
                system="You are a code analysis assistant. Analyze the provided code files based on the user's specific requirements.",
                messages=[
                    {
                        "role": "user",
                        "content": f"{custom_prompt}\n\nHere are the changed files to analyze:\n\n{content}"
                    }
                ]
            )
            
            analysis = message.content[0].text
            
            # Update UI in main thread
            self.root.after(0, self.display_analysis, analysis)
            
        except Exception as e:
            print(f"Claude API Error: {e}")  # Debug logging
            
            # Parse specific error types for better user feedback
            error_str = str(e)
            if "credit" in error_str.lower() or "quota" in error_str.lower():
                user_msg = "Claude API Quota Issue!\n\nYour Anthropic account may have insufficient credits.\n\nPlease check your Anthropic account billing."
                display_msg = "⚠️ Quota Issue: Please check your Anthropic account credits."
            elif "401" in error_str or "authentication" in error_str.lower():
                user_msg = "Invalid API Key!\n\nThe Claude API key appears to be invalid.\n\nPlease check your .env file and ensure you have a valid Anthropic API key."
                display_msg = "❌ Invalid API Key: Please check your Anthropic API key in the .env file."
            elif "rate" in error_str.lower():
                user_msg = "Rate Limit Reached!\n\nYou've made too many requests too quickly.\n\nPlease wait a moment and try again."
                display_msg = "⏱️ Rate limited: Please wait a moment and try again."
            else:
                user_msg = f"Claude API Error:\n\n{error_str}\n\nPlease check your API key and internet connection."
                display_msg = f"Error: {error_str}"
            
            self.root.after(0, lambda: messagebox.showwarning("Claude API Issue", user_msg))
            self.root.after(0, lambda: self.analysis_text.delete(1.0, tk.END))
            self.root.after(0, lambda: self.analysis_text.insert(1.0, display_msg))
        finally:
            self.root.after(0, lambda: self.status_var.set("Ready"))

    def perform_openai_analysis(self, content, custom_prompt=None):
        """Perform OpenAI analysis in background thread"""
        try:
            from openai import OpenAI
            
            self.status_var.set("Analyzing with ChatGPT...")
            # Show progress in analysis window
            self.root.after(0, lambda: self.analysis_text.delete(1.0, tk.END))
            self.root.after(0, lambda: self.analysis_text.insert(1.0, "Processing request with ChatGPT...\n"))
            
            # Use provided prompt or get default
            if custom_prompt is None:
                # Get custom prompt - use orchestrator if expanded, otherwise regular prompt
                if self.orchestrator_expanded:
                    custom_prompt = self.orchestrator_text.get('1.0', tk.END).strip()
                else:
                    custom_prompt = self.prompt_text.get('1.0', tk.END).strip()
            
            # Debug: Check if API key is loaded
            print(f"API Key loaded: {bool(self.openai_api_key)}")
            print(f"API Key length: {len(self.openai_api_key)}")
            print(f"API Key prefix: {self.openai_api_key[:10]}..." if self.openai_api_key else "No key")
            
            # Initialize OpenAI client with API key from environment
            client = OpenAI(api_key=self.openai_api_key)
            
            # Create chat completion using the modern OpenAI client
            print("Making API request to OpenAI...")
            response = client.chat.completions.create(
                model='gpt-3.5-turbo',
                messages=[
                    {
                        'role': 'system',
                        'content': 'You are a code analysis assistant. Analyze the provided code files based on the user\'s specific requirements.'
                    },
                    {
                        'role': 'user',
                        'content': f'{custom_prompt}\n\nHere are the changed files to analyze:\n\n{content}'
                    }
                ],
                max_tokens=2000,
                temperature=0.7
            )
            
            # Extract the response content
            analysis = response.choices[0].message.content

            # Update UI in main thread
            self.root.after(0, self.display_analysis, analysis)

        except Exception as e:
            print(f"OpenAI API Error: {e}")  # Debug logging
            
            # Parse specific error types for better user feedback
            error_str = str(e)
            if "insufficient_quota" in error_str:
                user_msg = "OpenAI API Quota Exceeded!\n\nYour OpenAI account has run out of credits or reached its usage limit.\n\nPlease:\n1. Check your OpenAI account billing at https://platform.openai.com/account/billing\n2. Add credits to your account\n3. Or use Claude if you have an Anthropic API key"
                display_msg = "⚠️ Quota Exceeded: Please add credits to your OpenAI account or use Claude instead."
            elif "401" in error_str or "invalid" in error_str.lower():
                user_msg = "Invalid API Key!\n\nThe OpenAI API key appears to be invalid.\n\nPlease check your .env file and ensure you have a valid OpenAI API key."
                display_msg = "❌ Invalid API Key: Please check your OpenAI API key in the .env file."
            elif "rate_limit" in error_str.lower():
                user_msg = "Rate Limit Reached!\n\nYou've made too many requests too quickly.\n\nPlease wait a moment and try again."
                display_msg = "⏱️ Rate limited: Please wait a moment and try again."
            else:
                user_msg = f"OpenAI API Error:\n\n{error_str}\n\nPlease check your API key and internet connection."
                display_msg = f"Error: {error_str}"
            
            self.root.after(0, lambda: messagebox.showwarning("OpenAI API Issue", user_msg))
            self.root.after(0, lambda: self.analysis_text.delete(1.0, tk.END))
            self.root.after(0, lambda: self.analysis_text.insert(1.0, display_msg))
        finally:
            self.root.after(0, lambda: self.status_var.set("Ready"))

    def remove_file(self, file_obj):
        """Remove a file from the changed files list and UI"""
        try:
            # Remove from selected files if it was selected
            if file_obj in self.selected_files:
                self.selected_files.remove(file_obj)
                self.update_selected_display()
            
            # Remove from changed files list
            if file_obj in self.changed_files:
                self.changed_files.remove(file_obj)
            
            # Remove the widget from UI
            if hasattr(file_obj, 'widgets') and 'frame' in file_obj.widgets:
                file_obj.widgets['frame'].destroy()
            
            # Add to exclude paths to prevent it from showing up again
            if file_obj.rel_path not in self.exclude_paths:
                self.exclude_paths.append(file_obj.rel_path)
            
            # Update status
            self.status_var.set(f"Removed: {file_obj.rel_path}")
            self.root.after(3000, lambda: self.status_var.set("Ready") 
                           if self.status_var.get().startswith("Removed:") else None)
            
        except Exception as e:
            print(f"Error removing file {file_obj.rel_path}: {e}")
            messagebox.showerror("Error", f"Failed to remove file: {e}")

    def display_analysis(self, analysis):
        """Display ChatGPT analysis result"""
        self.analysis_text.delete(1.0, tk.END)
        self.analysis_text.insert(1.0, analysis)
        self.status_var.set("Analysis complete")
    
    def toggle_selected_size(self):
        """Toggle between compact and expanded view for Selected section"""
        if self.selected_expanded:
            # Collapse to smaller size
            self.vertical_paned.paneconfig(self.selected_container, height=250)
            self.expand_selected_btn.config(text="Expand ↓")
            self.selected_expanded = False
        else:
            # Expand to larger size
            self.vertical_paned.paneconfig(self.selected_container, height=450)
            self.expand_selected_btn.config(text="Collapse ↑")
            self.selected_expanded = True
    
    def toggle_orchestrator_section(self):
        """Toggle the visibility of the orchestrator prompt section"""
        if self.orchestrator_expanded:
            # Hide orchestrator section
            self.orchestrator_frame.pack_forget()
            self.toggle_orchestrator_btn.config(text="Orchestrator ▼")
            self.orchestrator_expanded = False
        else:
            # Show orchestrator section - pack it before the analysis frame
            self.orchestrator_frame.pack(fill=tk.X, padx=5, pady=(0, 5), before=self.analysis_text.master.master)
            self.toggle_orchestrator_btn.config(text="Orchestrator ▲")
            self.orchestrator_expanded = True
    
    def toggle_prompt_section(self):
        """Toggle the visibility of the prompt section"""
        if self.prompt_expanded:
            # Hide prompt section
            self.prompt_frame.pack_forget()
            self.toggle_prompt_btn.config(text="Prompt ▼")
            self.prompt_expanded = False
        else:
            # Show prompt section - pack it before the analysis frame
            self.prompt_frame.pack(fill=tk.X, padx=5, pady=(0, 5), before=self.analysis_text.master.master)
            self.toggle_prompt_btn.config(text="Prompt ▲")
            self.prompt_expanded = True
    
    def restart_application(self):
        """Reset the application to initial state"""
        # Confirmation dialog
        if messagebox.askyesno("Restart Application", "This will reset all changes and clear all selections.\n\nDo you want to continue?"):
            # Clear all data
            self.changed_files.clear()
            self.selected_files.clear()
            self.exclude_paths.clear()
            
            # Clear UI elements
            for widget in self.scrollable_frame.winfo_children():
                widget.destroy()
            
            # Clear text areas
            self.selected_text.delete('1.0', tk.END)
            self.selected_text.insert('1.0', "No files selected for analysis")
            self.analysis_text.delete('1.0', tk.END)
            
            # Reset project path
            self.path_var.set("")
            self.project_path = ""
            self.repo_root = ""
            
            # Update status
            self.status_var.set("Application restarted - Ready")
            
            # Show info message
            messagebox.showinfo("Restart Complete", "The application has been reset to its initial state.\n\nPlease select a project path to begin.")


def main():
    root = tk.Tk()
    app = WorkflowAutomator(root)
    root.mainloop()


if __name__ == "__main__":
    main()

"""
File List Panel Component
Displays the list of changed files
"""

import tkinter as tk
from tkinter import ttk, scrolledtext
import threading


class FileListPanel:
    """Component for displaying and managing changed files"""
    
    def __init__(self, parent, theme_manager, file_manager, ui_utils):
        self.parent = parent
        self.theme = theme_manager
        self.file_manager = file_manager
        self.ui_utils = ui_utils
        
        self.frame = None
        self.canvas = None
        self.scrollable_frame = None
        self.changed_files = []
        
        self.setup_ui()
    
    def setup_ui(self):
        """Create the file list panel UI"""
        self.frame = ttk.Frame(self.parent, style='Card.TFrame')
        
        # Header with collapse button and restart
        files_header_frame = ttk.Frame(self.frame, style='TFrame')
        files_header_frame.pack(fill=tk.X, padx=15, pady=(15, 5))
        
        files_label = ttk.Label(files_header_frame, text="📁 Changed Files:", 
                               style='Heading.TLabel')
        files_label.pack(side=tk.LEFT)
        
        # Button container on the right
        header_buttons = ttk.Frame(files_header_frame, style='TFrame')
        header_buttons.pack(side=tk.RIGHT)
        
        self.restart_btn = ttk.Button(header_buttons, text="Restart", style='TButton')
        self.restart_btn.pack(side=tk.LEFT, padx=(0, 5))
        
        self.collapse_btn = ttk.Button(header_buttons, text="Collapse All", style='TButton')
        self.collapse_btn.pack(side=tk.LEFT)
        
        # Create scrollable frame
        self.create_scrollable_area()
    
    def create_scrollable_area(self):
        """Create the scrollable area for file list"""
        canvas_frame = ttk.Frame(self.frame, style='TFrame')
        canvas_frame.pack(fill=tk.BOTH, expand=True, padx=15, pady=(0, 15))
        
        self.canvas = tk.Canvas(canvas_frame, 
                               bg=self.theme.colors['bg_tertiary'],
                               highlightthickness=0,
                               borderwidth=0)
        
        scrollbar_v = ttk.Scrollbar(canvas_frame, orient=tk.VERTICAL, 
                                    command=self.canvas.yview)
        self.scrollable_frame = ttk.Frame(self.canvas, style='TFrame')
        
        self.scrollable_frame.bind(
            "<Configure>",
            lambda e: self.canvas.configure(scrollregion=self.canvas.bbox("all"))
        )
        
        self.canvas.create_window((0, 0), window=self.scrollable_frame, anchor="nw")
        self.canvas.configure(yscrollcommand=scrollbar_v.set)
        
        self.canvas.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        scrollbar_v.pack(side=tk.RIGHT, fill=tk.Y)
        
        # Bind mouse wheel
        self.canvas.bind_all("<MouseWheel>", self._on_mousewheel)
    
    def _on_mousewheel(self, event):
        """Handle mouse wheel scrolling"""
        self.canvas.yview_scroll(int(-1*(event.delta/120)), "units")
    
    def create_file_widget(self, file_obj, index, callbacks):
        """Create a widget for a single file"""
        # Main file frame with card styling
        file_frame = ttk.Frame(self.scrollable_frame, style='Card.TFrame')
        file_frame.pack(fill=tk.X, padx=8, pady=4)
        
        # File header frame
        header_frame = ttk.Frame(file_frame, style='TFrame')
        header_frame.pack(fill=tk.X, padx=12, pady=8)
        
        # Status and filename
        status_label = ttk.Label(header_frame, text=f"[{file_obj.status}]",
                                style='Secondary.TLabel')
        status_label.pack(side=tk.LEFT, padx=(0, 8))
        
        filename_label = ttk.Label(header_frame, text=file_obj.rel_path,
                                  style='TLabel')
        filename_label.pack(side=tk.LEFT, padx=0)
        
        # Buttons frame
        buttons_frame = ttk.Frame(header_frame, style='TFrame')
        buttons_frame.pack(side=tk.RIGHT)
        
        # Copy Path dropdown
        path_var = tk.StringVar(value="Copy Path ▼")
        path_menu = ttk.Menubutton(buttons_frame, textvariable=path_var, 
                                  width=12, style='TButton')
        path_menu.pack(side=tk.LEFT, padx=2)
        self.ui_utils.bind_hover_cursor(path_menu)
        
        path_dropdown = tk.Menu(path_menu, tearoff=0,
                               bg=self.theme.colors['bg_secondary'],
                               fg=self.theme.colors['text_primary'],
                               activebackground=self.theme.colors['accent'],
                               activeforeground='white',
                               borderwidth=0)
        path_dropdown.add_command(label="Copy Relative Path",
                                 command=lambda: callbacks['copy_path'](file_obj, True))
        path_dropdown.add_command(label="Copy Absolute Path",
                                 command=lambda: callbacks['copy_path'](file_obj, False))
        path_menu.config(menu=path_dropdown)
        
        # Copy & Append button
        copy_append_btn = ttk.Button(buttons_frame, text="Copy & Append",
                                     command=lambda: callbacks['copy_append'](file_obj),
                                     style='TButton')
        copy_append_btn.pack(side=tk.LEFT, padx=2)
        self.ui_utils.bind_hover_cursor(copy_append_btn)
        
        # Show Content button
        show_btn = ttk.Button(buttons_frame, text="Show Content",
                             command=lambda: callbacks['toggle_content'](file_obj, index),
                             style='TButton')
        show_btn.pack(side=tk.LEFT, padx=2)
        self.ui_utils.bind_hover_cursor(show_btn)
        
        # Select checkbox
        select_var = tk.BooleanVar()
        select_cb = ttk.Checkbutton(buttons_frame, text="Select", variable=select_var,
                                    command=lambda: callbacks['toggle_selection'](file_obj, select_var))
        select_cb.pack(side=tk.LEFT, padx=2)
        self.ui_utils.bind_hover_cursor(select_cb)
        
        # Remove button
        remove_btn = ttk.Button(buttons_frame, text="Remove",
                               command=lambda: callbacks['remove_file'](file_obj),
                               style='TButton')
        remove_btn.pack(side=tk.LEFT, padx=2)
        self.ui_utils.bind_hover_cursor(remove_btn)
        
        # Store widget references
        file_obj.widgets = {
            'frame': file_frame,
            'show_btn': show_btn,
            'select_var': select_var,
            'select_cb': select_cb
        }
        
        return file_frame
    
    def show_file_content(self, file_obj):
        """Display file content in the UI"""
        if file_obj.error:
            # Show error
            error_frame = ttk.Frame(file_obj.widgets['frame'], style='TFrame')
            error_frame.pack(fill=tk.X, padx=20, pady=10)
            
            error_label = ttk.Label(error_frame, text=file_obj.error, 
                                   style='Secondary.TLabel')
            error_label.pack(side=tk.LEFT)
            
            file_obj.widgets['content_frame'] = error_frame
        else:
            # Show content
            content_frame = ttk.Frame(file_obj.widgets['frame'], style='TFrame')
            content_frame.pack(fill=tk.BOTH, expand=True, padx=20, pady=10)
            
            # Content controls
            controls_frame = ttk.Frame(content_frame, style='TFrame')
            controls_frame.pack(fill=tk.X, pady=(0, 8))
            
            copy_content_btn = ttk.Button(controls_frame, text="Copy Content",
                                         style='TButton')
            copy_content_btn.pack(side=tk.LEFT)
            self.ui_utils.bind_hover_cursor(copy_content_btn)
            
            # Content text area
            content_text = scrolledtext.ScrolledText(content_frame, 
                                                    height=15,
                                                    font=self.theme.fonts['code'], 
                                                    wrap=tk.NONE,
                                                    bg=self.theme.colors['bg_input'],
                                                    fg=self.theme.colors['text_primary'])
            content_text.pack(fill=tk.BOTH, expand=True)
            content_text.insert('1.0', file_obj.content_preview)
            content_text.config(state='disabled')  # Read-only
            
            file_obj.widgets['content_frame'] = content_frame
            file_obj.widgets['content_text'] = content_text
        
        file_obj.widgets['show_btn'].config(text="Collapse", state='normal')
        file_obj.expanded = True
    
    def hide_file_content(self, file_obj):
        """Hide file content"""
        if 'content_frame' in file_obj.widgets:
            file_obj.widgets['content_frame'].destroy()
            del file_obj.widgets['content_frame']
            if 'content_text' in file_obj.widgets:
                del file_obj.widgets['content_text']
        
        file_obj.expanded = False
        if 'show_btn' in file_obj.widgets:
            file_obj.widgets['show_btn'].config(text="Show Content")
    
    def clear_all(self):
        """Clear all file widgets"""
        for widget in self.scrollable_frame.winfo_children():
            widget.destroy()
        self.changed_files.clear()
"""
UI Utilities Module
Helper functions for UI operations
"""

import tkinter as tk
import pyperclip


class UIUtils:
    """Utility functions for UI operations"""
    
    @staticmethod
    def bind_hover_cursor(widget):
        """Bind hand cursor on hover for interactive widgets"""
        widget.bind("<Enter>", lambda e: widget.configure(cursor="hand2"))
        widget.bind("<Leave>", lambda e: widget.configure(cursor=""))
    
    @staticmethod
    def copy_to_clipboard(text):
        """Copy text to clipboard"""
        try:
            pyperclip.copy(text)
            return True
        except Exception:
            return False
    
    @staticmethod
    def show_toast(status_var, message, duration=2000):
        """Show a temporary status message"""
        status_var.set(message)
        # Note: The callback to reset would be handled by the main app
    
    @staticmethod
    def create_scrollable_frame(parent, bg_color):
        """Create a scrollable frame widget"""
        canvas_frame = tk.Frame(parent)
        canvas_frame.pack(fill=tk.BOTH, expand=True, padx=15, pady=(0, 15))
        
        canvas = tk.Canvas(canvas_frame, 
                          bg=bg_color,
                          highlightthickness=0,
                          borderwidth=0)
        
        scrollbar = tk.Scrollbar(canvas_frame, orient=tk.VERTICAL, command=canvas.yview)
        scrollable_frame = tk.Frame(canvas)
        
        scrollable_frame.bind(
            "<Configure>",
            lambda e: canvas.configure(scrollregion=canvas.bbox("all"))
        )
        
        canvas.create_window((0, 0), window=scrollable_frame, anchor="nw")
        canvas.configure(yscrollcommand=scrollbar.set)
        
        canvas.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        
        return canvas, scrollable_frame
"""
UI Utilities Module
Helper functions for UI operations
"""

import tkinter as tk
from tkinter import ttk
import pyperclip


class ToolTip:
    """Simple tooltip widget for showing hover text"""
    def __init__(self, widget, text):
        self.widget = widget
        self.text = text
        self.tooltip = None
        self.widget.bind("<Enter>", self.show_tooltip)
        self.widget.bind("<Leave>", self.hide_tooltip)
        
    def show_tooltip(self, event=None):
        if self.tooltip:
            return
            
        x = self.widget.winfo_rootx() + self.widget.winfo_width() // 2
        y = self.widget.winfo_rooty() - 30
        
        self.tooltip = tk.Toplevel()
        self.tooltip.wm_overrideredirect(True)
        self.tooltip.geometry(f"+{x}+{y}")
        
        label = tk.Label(self.tooltip, text=self.text, 
                        background="#ffffe0", 
                        foreground="#000000",
                        relief="solid", 
                        borderwidth=1,
                        font=("Arial", 9))
        label.pack()
        
    def hide_tooltip(self, event=None):
        if self.tooltip:
            self.tooltip.destroy()
            self.tooltip = None


class UIUtils:
    """Utility functions for UI operations"""
    
    @staticmethod
    def bind_hover_cursor(widget):
        """Bind hand cursor on hover for interactive widgets"""
        widget.bind("<Enter>", lambda e: widget.configure(cursor="hand2"))
        widget.bind("<Leave>", lambda e: widget.configure(cursor=""))
    
    @staticmethod
    def add_tooltip(widget, text):
        """Add a tooltip to a widget"""
        return ToolTip(widget, text)
    
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
"""
UI Utilities Module
Helper functions for UI operations
"""

import tkinter as tk
from tkinter import ttk
import pyperclip


class CustomScrollbar(tk.Canvas):
    """Custom scrollbar with completely invisible background - only handle visible"""
    
    def __init__(self, parent, orient=tk.VERTICAL, command=None, **kwargs):
        # Get parent background to make scrollbar invisible
        parent_bg = self._get_parent_background_static(parent)
        
        # Initialize as Canvas with transparent background
        super().__init__(parent, 
                        width=8 if orient == tk.VERTICAL else 100,
                        height=100 if orient == tk.VERTICAL else 8,
                        highlightthickness=0,
                        borderwidth=0,
                        bg=parent_bg,
                        **kwargs)
        
        self.orient = orient
        self.command = command
        
        # Scrollbar state
        self.top = 0.0
        self.bottom = 1.0
        self.dragging = False
        self.last_y = 0
        self.handle_color = '#10a37f'  # Default handle color
        
        # Auto-hide timer
        self.hide_timer = None
        self.visible = False
        
        # Bind events directly to canvas (self)
        self.bind("<Button-1>", self.on_click)
        self.bind("<B1-Motion>", self.on_drag)
        self.bind("<ButtonRelease-1>", self.on_release)
        self.bind("<MouseWheel>", self.on_mousewheel)
    
    @staticmethod
    def _get_parent_background_static(parent):
        """Static method for background color detection before init"""
        background_methods = [
            lambda: parent.cget('bg'),
            lambda: parent.cget('background'),
            lambda: parent.master.cget('bg') if hasattr(parent, 'master') else None,
        ]
        
        for method in background_methods:
            try:
                bg_color = method()
                if bg_color and bg_color != '':
                    return bg_color
            except:
                continue
        return '#212121'  # Dark theme default
    
    def _get_parent_background(self, parent):
        """Smart background color detection for different widget types"""
        # Try different methods to get background color
        background_methods = [
            # Standard tkinter widgets
            lambda: parent.cget('bg'),
            lambda: parent.cget('background'),
            # TTK widgets might not have bg, try getting from style
            lambda: parent.master.cget('bg') if hasattr(parent, 'master') else None,
            # Try to get from canvas if it's a canvas
            lambda: parent.cget('bg') if 'canvas' in str(type(parent)).lower() else None,
            # Get from theme manager colors if available
            lambda: '#212121' if hasattr(parent, 'theme') else None,
        ]
        
        for method in background_methods:
            try:
                bg_color = method()
                if bg_color and bg_color != '':
                    return bg_color
            except:
                continue
        
        # Fallback to theme-appropriate colors
        return '#212121'  # Dark theme default
    
    def update_colors(self, bg_color=None, handle_color='#10a37f'):
        """Update scrollbar colors dynamically"""
        if bg_color is None:
            bg_color = self._get_parent_background(self.master)
        
        self.configure(bg=bg_color)
        self.handle_color = handle_color
        self.update_scrollbar()  # Redraw with new colors
        
    def set(self, top, bottom):
        """Set scrollbar position (called by scrolled widget)"""
        self.top = float(top)
        self.bottom = float(bottom)
        self.update_scrollbar()
        
        # Show scrollbar when content is scrollable
        if self.top > 0 or self.bottom < 1:
            self.show_scrollbar()
        else:
            self.hide_scrollbar()
    
    def update_scrollbar(self):
        """Update scrollbar visual appearance"""
        self.delete("scrollbar")
        
        if not self.visible or (self.top <= 0 and self.bottom >= 1):
            return
            
        if self.orient == tk.VERTICAL:
            canvas_height = self.winfo_height()
            if canvas_height <= 1:
                return
                
            # Calculate handle position and size
            handle_top = int(self.top * canvas_height)
            handle_bottom = int(self.bottom * canvas_height)
            handle_height = max(handle_bottom - handle_top, 20)  # Minimum handle size
            
            # Draw the handle with rounded appearance
            self.create_rectangle(2, handle_top, 6, handle_top + handle_height,
                                fill=self.handle_color, outline='', tags="scrollbar")
        else:
            # Horizontal scrollbar logic
            canvas_width = self.winfo_width()
            if canvas_width <= 1:
                return
                
            handle_left = int(self.top * canvas_width)
            handle_right = int(self.bottom * canvas_width)
            handle_width = max(handle_right - handle_left, 20)
            
            self.create_rectangle(handle_left, 2, handle_left + handle_width, 6,
                                fill=self.handle_color, outline='', tags="scrollbar")
    
    def show_scrollbar(self):
        """Show the scrollbar handle"""
        if not self.visible:
            self.visible = True
            self.update_scrollbar()
        
        # Reset hide timer
        if self.hide_timer:
            self.after_cancel(self.hide_timer)
        self.hide_timer = self.after(1500, self.hide_scrollbar)  # Hide after 1.5 seconds
    
    def hide_scrollbar(self):
        """Hide the scrollbar handle"""
        if not self.dragging:  # Don't hide while dragging
            self.visible = False
            self.delete("scrollbar")
            if self.hide_timer:
                self.after_cancel(self.hide_timer)
                self.hide_timer = None
    
    def on_click(self, event):
        """Handle mouse click on scrollbar"""
        if self.orient == tk.VERTICAL:
            canvas_height = self.canvas.winfo_height()
            click_pos = event.y / canvas_height
        else:
            canvas_width = self.canvas.winfo_width()
            click_pos = event.x / canvas_width
            
        # Move to clicked position
        if self.command:
            self.command("moveto", click_pos)
        
        self.dragging = True
        self.last_y = event.y if self.orient == tk.VERTICAL else event.x
        self.show_scrollbar()
    
    def on_drag(self, event):
        """Handle drag motion"""
        if not self.dragging:
            return
            
        if self.orient == tk.VERTICAL:
            delta = event.y - self.last_y
            canvas_height = self.canvas.winfo_height()
            scroll_delta = delta / canvas_height if canvas_height > 0 else 0
        else:
            delta = event.x - self.last_y
            canvas_width = self.canvas.winfo_width()
            scroll_delta = delta / canvas_width if canvas_width > 0 else 0
        
        if self.command and abs(scroll_delta) > 0.001:
            self.command("scroll", int(scroll_delta * 100), "units")
        
        self.last_y = event.y if self.orient == tk.VERTICAL else event.x
        self.show_scrollbar()
    
    def on_release(self, event):
        """Handle mouse release"""
        self.dragging = False
    
    def on_mousewheel(self, event):
        """Handle mouse wheel scrolling"""
        if self.command:
            delta = -1 if event.delta > 0 else 1
            self.command("scroll", delta, "units")
        self.show_scrollbar()


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
        """Create a scrollable frame widget with custom scrollbar"""
        canvas_frame = tk.Frame(parent)
        canvas_frame.pack(fill=tk.BOTH, expand=True, padx=15, pady=(0, 15))
        
        canvas = tk.Canvas(canvas_frame, 
                          bg=bg_color,
                          highlightthickness=0,
                          borderwidth=0)
        
        scrollbar = CustomScrollbar(canvas_frame, orient=tk.VERTICAL, command=canvas.yview)
        scrollable_frame = tk.Frame(canvas)
        
        scrollable_frame.bind(
            "<Configure>",
            lambda e: canvas.configure(scrollregion=canvas.bbox("all"))
        )
        
        canvas.create_window((0, 0), window=scrollable_frame, anchor="nw")
        canvas.configure(yscrollcommand=scrollbar.set)
        
        canvas.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        
        # Bind mousewheel to canvas
        def on_mousewheel(event):
            canvas.yview_scroll(int(-1*(event.delta/120)), "units")
            scrollbar.show_scrollbar()
        
        canvas.bind("<MouseWheel>", on_mousewheel)
        
        return canvas, scrollable_frame
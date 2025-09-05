"""
Theme Manager Module
Handles all styling and theme configuration for the application
"""

import tkinter as tk
from tkinter import ttk


class ThemeManager:
    """Manages the application's dark theme and styling"""
    
    def __init__(self, root):
        self.root = root
        self.setup_dark_theme()
    
    def setup_dark_theme(self):
        """Configure dark ChatGPT-style theme"""
        # ChatGPT-inspired dark color scheme
        self.colors = {
            'bg_primary': '#212121',      # Main background (darker gray)
            'bg_secondary': '#2f2f2f',    # Secondary background (lighter gray)
            'bg_tertiary': '#3a3a3a',     # Tertiary background (cards, panels)
            'bg_input': '#404040',        # Input fields background
            'bg_button': '#565656',       # Button background
            'bg_button_hover': '#686868', # Button hover background
            'text_primary': '#ececec',    # Primary text (white-ish)
            'text_secondary': '#b4b4b4',  # Secondary text (light gray)
            'text_muted': '#8e8e8e',      # Muted text (medium gray)
            'accent': '#10a37f',          # ChatGPT green accent
            'accent_hover': '#1a7f64',    # Darker green for hover
            'border': '#4a4a4a',          # Border color
            'border_light': '#5a5a5a',    # Lighter border
            'chat_user': '#2f2f2f',       # User message background
            'chat_ai': '#1e1e1e',         # AI message background
            'success': '#10a37f',         # Success/copy feedback
            'error': '#ef4444',           # Error color
            'warning': '#f59e0b'          # Warning color
        }
        
        # ChatGPT-style fonts
        self.fonts = {
            'default': ('Segoe UI', 10),
            'heading': ('Segoe UI', 12, 'bold'),
            'small': ('Segoe UI', 9),
            'code': ('Consolas', 9),
            'button': ('Segoe UI', 9)
        }
        
        # Configure root window
        self.root.configure(bg=self.colors['bg_primary'])
        
        # Configure ttk styles
        style = ttk.Style()
        style.theme_use('clam')  # Use clam theme as base
        
        # Configure ttk widget styles
        self.configure_ttk_styles(style)
    
    def configure_ttk_styles(self, style):
        """Configure ttk widget styles for dark theme"""
        # Configure Frame styles
        style.configure('TFrame',
                       background=self.colors['bg_primary'],
                       borderwidth=0)
        
        style.configure('Card.TFrame',
                       background=self.colors['bg_tertiary'],
                       borderwidth=1,
                       relief='flat')
        
        # Configure Label styles
        style.configure('TLabel',
                       background=self.colors['bg_primary'],
                       foreground=self.colors['text_primary'],
                       font=self.fonts['default'])
        
        style.configure('Heading.TLabel',
                       background=self.colors['bg_primary'],
                       foreground=self.colors['text_primary'],
                       font=self.fonts['heading'])
        
        style.configure('Secondary.TLabel',
                       background=self.colors['bg_primary'],
                       foreground=self.colors['text_secondary'],
                       font=self.fonts['small'])
        
        # Configure Button styles
        style.configure('TButton',
                       background=self.colors['bg_button'],
                       foreground=self.colors['text_primary'],
                       borderwidth=0,
                       focuscolor='none',
                       font=self.fonts['button'],
                       padding=(12, 8))
        
        style.map('TButton',
                 background=[('active', self.colors['bg_button_hover']),
                           ('pressed', self.colors['bg_button'])],
                 foreground=[('active', self.colors['text_primary'])])
        
        style.configure('Accent.TButton',
                       background=self.colors['accent'],
                       foreground='white')
        
        style.map('Accent.TButton',
                 background=[('active', self.colors['accent_hover']),
                           ('pressed', self.colors['accent'])])
        
        # Configure Entry styles
        style.configure('TEntry',
                       fieldbackground=self.colors['bg_input'],
                       background=self.colors['bg_input'],
                       foreground=self.colors['text_primary'],
                       borderwidth=1,
                       bordercolor=self.colors['border'],
                       insertcolor=self.colors['text_primary'],
                       font=self.fonts['default'])
        
        style.map('TEntry',
                 bordercolor=[('focus', self.colors['accent'])])
        
        # Configure PanedWindow styles  
        style.configure('TPanedwindow',
                       background=self.colors['bg_primary'])
        
        # Configure Checkbutton styles
        style.configure('TCheckbutton',
                       background=self.colors['bg_primary'],
                       foreground=self.colors['text_primary'],
                       focuscolor='none',
                       font=self.fonts['default'])
        
        style.map('TCheckbutton',
                 background=[('active', self.colors['bg_secondary'])])
        
        # Configure Menubutton styles
        style.configure('TMenubutton',
                       background=self.colors['bg_button'],
                       foreground=self.colors['text_primary'],
                       borderwidth=0,
                       focuscolor='none',
                       font=self.fonts['button'],
                       padding=(12, 8))
        
        style.map('TMenubutton',
                 background=[('active', self.colors['bg_button_hover'])])
        
        # Configure Sidebar styles
        style.configure('Sidebar.TFrame',
                       background=self.colors['bg_tertiary'],
                       borderwidth=0,
                       relief='flat')
        
        style.configure('SidebarIcon.TLabel',
                       background=self.colors['bg_tertiary'],
                       foreground=self.colors['text_primary'],
                       font=('Segoe UI', 16),
                       anchor='center')
        
        style.configure('Sidebar.TButton',
                       background=self.colors['bg_button'],
                       foreground=self.colors['text_primary'],
                       borderwidth=0,
                       focuscolor='none',
                       font=('Segoe UI', 10, 'bold'),
                       padding=(8, 6))
        
        style.map('Sidebar.TButton',
                 background=[('active', self.colors['bg_button_hover']),
                           ('pressed', self.colors['bg_button'])])

        # Style for files loaded (green) state
        style.configure('SidebarLoaded.TButton',
                       background='#10a37f',  # Use direct green color
                       foreground='white',
                       borderwidth=0,
                       focuscolor='none',
                       font=('Segoe UI', 10, 'bold'),
                       padding=(8, 6))
        
        style.map('SidebarLoaded.TButton',
                 background=[('active', '#1a7f64'),
                           ('pressed', '#10a37f')])
        
        # Style for loading (red) state
        style.configure('SidebarLoading.TButton',
                       background='#ef4444',  # Use direct red color
                       foreground='white',
                       borderwidth=0,
                       focuscolor='none',
                       font=('Segoe UI', 10, 'bold'),
                       padding=(8, 6))
        
        style.map('SidebarLoading.TButton',
                 background=[('active', '#dc2626'),
                           ('pressed', '#ef4444')])
        
        # Configure stylish scrollbars with no background and rounded handles
        # Vertical Scrollbar
        style.configure('Vertical.TScrollbar',
                       background=self.colors['bg_primary'],  # Make background invisible
                       troughcolor=self.colors['bg_primary'],  # Hide trough
                       borderwidth=0,
                       arrowcolor=self.colors['bg_primary'],  # Hide arrows
                       darkcolor=self.colors['bg_primary'],
                       lightcolor=self.colors['bg_primary'],
                       relief='flat',
                       width=8)  # Thin scrollbar
        
        # Horizontal Scrollbar
        style.configure('Horizontal.TScrollbar',
                       background=self.colors['bg_primary'],
                       troughcolor=self.colors['bg_primary'],
                       borderwidth=0,
                       arrowcolor=self.colors['bg_primary'],
                       darkcolor=self.colors['bg_primary'],
                       lightcolor=self.colors['bg_primary'],
                       relief='flat',
                       height=8)  # Thin scrollbar
        
        # Style the scrollbar thumbs (handles) with modern appearance
        thumb_color = self.colors['accent']
        thumb_hover = '#1a7f64'
        
        style.configure('Vertical.TScrollbar.thumb',
                       background=thumb_color,
                       borderwidth=1,
                       relief='flat',
                       bordercolor=thumb_color)
        
        style.configure('Horizontal.TScrollbar.thumb',
                       background=thumb_color,
                       borderwidth=1,
                       relief='flat',
                       bordercolor=thumb_color)
        
        # Hover and active states
        style.map('Vertical.TScrollbar',
                 background=[('active', self.colors['bg_primary'])],
                 troughcolor=[('active', self.colors['bg_primary'])])
        
        style.map('Horizontal.TScrollbar',
                 background=[('active', self.colors['bg_primary'])],
                 troughcolor=[('active', self.colors['bg_primary'])])
        
        style.map('Vertical.TScrollbar.thumb',
                 background=[('active', thumb_hover),
                           ('pressed', thumb_color)],
                 bordercolor=[('active', thumb_hover),
                            ('pressed', thumb_color)])
        
        style.map('Horizontal.TScrollbar.thumb',
                 background=[('active', thumb_hover),
                           ('pressed', thumb_color)],
                 bordercolor=[('active', thumb_hover),
                            ('pressed', thumb_color)])
        
        # Configure custom title bar styles
        style.configure('TitleBar.TFrame',
                       background=self.colors['bg_secondary'],
                       borderwidth=0,
                       relief='flat')
        
        style.configure('TitleIcon.TLabel',
                       background=self.colors['bg_secondary'],
                       foreground=self.colors['text_primary'],
                       font=('Segoe UI', 12))
        
        style.configure('TitleText.TLabel',
                       background=self.colors['bg_secondary'],
                       foreground=self.colors['text_primary'],
                       font=('Segoe UI', 10, 'bold'))
        
        # Title bar buttons
        style.configure('TitleButton.TButton',
                       background=self.colors['bg_secondary'],
                       foreground=self.colors['text_primary'],
                       borderwidth=0,
                       focuscolor='none',
                       font=('Segoe UI', 9),
                       padding=(8, 6))
        
        style.map('TitleButton.TButton',
                 background=[('active', self.colors['bg_button_hover']),
                           ('pressed', self.colors['bg_button'])])
        
        # Close button with red hover
        style.configure('TitleButtonClose.TButton',
                       background=self.colors['bg_secondary'],
                       foreground=self.colors['text_primary'],
                       borderwidth=0,
                       focuscolor='none',
                       font=('Segoe UI', 9),
                       padding=(8, 6))
        
        style.map('TitleButtonClose.TButton',
                 background=[('active', '#ef4444'),  # Red on hover
                           ('pressed', '#dc2626')],
                 foreground=[('active', 'white'),
                           ('pressed', 'white')])
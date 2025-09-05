"""
Analysis Panel Component
Handles the AI analysis section
"""

import tkinter as tk
from tkinter import ttk, scrolledtext
from datetime import datetime
from ..ui_utils import CustomScrollbar


class AnalysisPanel:
    """Component for AI analysis interface"""
    
    def __init__(self, parent, theme_manager, ui_utils):
        self.parent = parent
        self.theme = theme_manager
        self.ui_utils = ui_utils
        
        self.frame = None
        self.analysis_text = None
        self.prompt_text = None
        self.orchestrator_text = None
        self.prompt_expanded = False
        self.orchestrator_expanded = False
        self.chat_history = []
        
        self.setup_ui()
    
    def setup_ui(self):
        """Create the analysis panel UI"""
        self.frame = ttk.Frame(self.parent, style='TFrame')
        
        # Analysis header and buttons
        analysis_header_frame = ttk.Frame(self.frame, style='TFrame')
        analysis_header_frame.pack(fill=tk.X, padx=10, pady=(10, 5))
        
        analysis_label = ttk.Label(analysis_header_frame, text="🤖 AI Analysis:",
                                  style='Heading.TLabel')
        analysis_label.pack(side=tk.LEFT)
        
        # Analysis buttons
        analysis_buttons = ttk.Frame(analysis_header_frame, style='TFrame')
        analysis_buttons.pack(side=tk.RIGHT)
        
        self.toggle_orchestrator_btn = ttk.Button(analysis_buttons, text="Orchestrator ▼",
                                                  style='TButton')
        self.toggle_orchestrator_btn.pack(side=tk.LEFT, padx=2)
        self.ui_utils.bind_hover_cursor(self.toggle_orchestrator_btn)
        
        self.toggle_prompt_btn = ttk.Button(analysis_buttons, text="Prompt ▼",
                                           style='TButton')
        self.toggle_prompt_btn.pack(side=tk.LEFT, padx=2)
        self.ui_utils.bind_hover_cursor(self.toggle_prompt_btn)
        
        self.clear_chat_btn = ttk.Button(analysis_buttons, text="Clear Chat",
                                         style='Accent.TButton')
        self.clear_chat_btn.pack(side=tk.LEFT, padx=2)
        self.ui_utils.bind_hover_cursor(self.clear_chat_btn)
        
        # Create collapsible sections
        self.create_orchestrator_section()
        self.create_prompt_section()
        
        # AI response text area - The main chat interface
        analysis_frame = ttk.Frame(self.frame, style='TFrame')
        analysis_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=(5, 10))
        
        # Create custom scrollable analysis text area
        analysis_text_frame = ttk.Frame(analysis_frame, style='TFrame')
        analysis_text_frame.pack(fill=tk.BOTH, expand=True)
        
        self.analysis_text = tk.Text(
            analysis_text_frame, 
            wrap=tk.WORD,
            font=self.theme.fonts['code'],
            bg=self.theme.colors['chat_ai'],
            fg=self.theme.colors['text_primary'],
            insertbackground=self.theme.colors['text_primary'],
            selectbackground=self.theme.colors['accent'],
            selectforeground='white',
            borderwidth=0,
            highlightthickness=1,
            highlightcolor=self.theme.colors['accent'],
            highlightbackground=self.theme.colors['border'],
            padx=12,
            pady=12)
        self.analysis_text.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        
        # Add custom scrollbar
        analysis_scrollbar = CustomScrollbar(analysis_text_frame, orient=tk.VERTICAL, 
                                           command=self.analysis_text.yview)
        analysis_scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        self.analysis_text.configure(yscrollcommand=analysis_scrollbar.set)
        
        # Add mousewheel support
        def on_analysis_mousewheel(event):
            self.analysis_text.yview_scroll(int(-1*(event.delta/120)), "units")
            analysis_scrollbar.show_scrollbar()
        
        self.analysis_text.bind("<MouseWheel>", on_analysis_mousewheel)
    
    def create_orchestrator_section(self):
        """Create the orchestrator prompt section"""
        self.orchestrator_frame = ttk.Frame(self.frame, style='TFrame')
        # Don't pack yet - will be toggled
        
        orchestrator_label = ttk.Label(self.orchestrator_frame, 
                                      text="🎭 Orchestrator Prompt:",
                                      style='Secondary.TLabel')
        orchestrator_label.pack(anchor=tk.W, padx=10, pady=(10, 5))
        
        # Orchestrator text area with default text
        orchestrator_text_frame = ttk.Frame(self.orchestrator_frame, style='TFrame')
        orchestrator_text_frame.pack(fill=tk.X, padx=10, pady=(0, 5))
        
        self.orchestrator_text = tk.Text(orchestrator_text_frame, 
                                        height=4, 
                                        wrap=tk.WORD,
                                        font=self.theme.fonts['code'],
                                        bg=self.theme.colors['bg_input'],
                                        fg=self.theme.colors['text_primary'])
        self.orchestrator_text.pack(side=tk.LEFT, fill=tk.X, expand=True)
        
        # Add scrollbar to orchestrator prompt
        orchestrator_scroll = ttk.Scrollbar(orchestrator_text_frame, 
                                           command=self.orchestrator_text.yview)
        orchestrator_scroll.pack(side=tk.RIGHT, fill=tk.Y)
        self.orchestrator_text.config(yscrollcommand=orchestrator_scroll.set)
        
        # Add Send button for orchestrator
        orchestrator_btn_frame = ttk.Frame(self.orchestrator_frame, style='TFrame')
        orchestrator_btn_frame.pack(fill=tk.X, padx=10, pady=(0, 10))
        
        # Automated checkbox for orchestrator
        self.orchestrator_automated_var = tk.BooleanVar()
        orchestrator_auto_cb = ttk.Checkbutton(orchestrator_btn_frame, text="Automated",
                                              variable=self.orchestrator_automated_var,
                                              style='TCheckbutton')
        orchestrator_auto_cb.pack(side=tk.LEFT, padx=(0, 10))
        self.ui_utils.bind_hover_cursor(orchestrator_auto_cb)
        
        self.orchestrator_send_btn = ttk.Button(orchestrator_btn_frame, 
                                               text="Send to AI",
                                               style='Accent.TButton')
        self.orchestrator_send_btn.pack(side=tk.LEFT)
        self.ui_utils.bind_hover_cursor(self.orchestrator_send_btn)
        
        # Set default orchestrator prompt text
        default_orchestrator = """Generate a text prompt for orchestrator Claude agent with clear instructions for fixing this issue.

Instructions for the orchestrator:
- Analyze the code changes and identify the root cause
- Create a step-by-step plan to resolve the issue
- Delegate tasks to specialized agents based on their expertise
- Do not add any code directly, use agents specified for their tasks
- Coordinate between different agents to ensure smooth workflow"""
        self.orchestrator_text.insert('1.0', default_orchestrator)
    
    def create_prompt_section(self):
        """Create the regular prompt section"""
        self.prompt_frame = ttk.Frame(self.frame, style='TFrame')
        # Don't pack yet - will be toggled
        
        prompt_label = ttk.Label(self.prompt_frame, text="✏️ AI Prompt:",
                                style='Secondary.TLabel')
        prompt_label.pack(anchor=tk.W, padx=10, pady=(10, 5))
        
        # Prompt text area with default text
        prompt_text_frame = ttk.Frame(self.prompt_frame, style='TFrame')
        prompt_text_frame.pack(fill=tk.X, padx=10, pady=(0, 5))
        
        self.prompt_text = tk.Text(prompt_text_frame, 
                                  height=3, 
                                  wrap=tk.WORD,
                                  font=self.theme.fonts['code'],
                                  bg=self.theme.colors['bg_input'],
                                  fg=self.theme.colors['text_primary'])
        self.prompt_text.pack(side=tk.LEFT, fill=tk.X, expand=True)
        
        # Add scrollbar to prompt
        prompt_scroll = ttk.Scrollbar(prompt_text_frame, command=self.prompt_text.yview)
        prompt_scroll.pack(side=tk.RIGHT, fill=tk.Y)
        self.prompt_text.config(yscrollcommand=prompt_scroll.set)
        
        # Add Send button for regular prompt
        prompt_btn_frame = ttk.Frame(self.prompt_frame, style='TFrame')
        prompt_btn_frame.pack(fill=tk.X, padx=10, pady=(0, 10))
        
        # Automated checkbox for regular prompt
        self.prompt_automated_var = tk.BooleanVar()
        prompt_auto_cb = ttk.Checkbutton(prompt_btn_frame, text="Automated",
                                        variable=self.prompt_automated_var,
                                        style='TCheckbutton')
        prompt_auto_cb.pack(side=tk.LEFT, padx=(0, 10))
        self.ui_utils.bind_hover_cursor(prompt_auto_cb)
        
        self.prompt_send_btn = ttk.Button(prompt_btn_frame, 
                                         text="Send to AI",
                                         style='Accent.TButton')
        self.prompt_send_btn.pack(side=tk.LEFT)
        self.ui_utils.bind_hover_cursor(self.prompt_send_btn)
        
        # Set default prompt text
        default_prompt = """Make a deep analysis of these code changes. Focus on:
- Code quality and potential issues
- Suggestions for improvements
- Security considerations
- Performance implications"""
        self.prompt_text.insert('1.0', default_prompt)
    
    def toggle_orchestrator_section(self):
        """Toggle the visibility of the orchestrator prompt section"""
        if self.orchestrator_expanded:
            self.orchestrator_frame.pack_forget()
            self.toggle_orchestrator_btn.config(text="Orchestrator ▼")
            self.orchestrator_expanded = False
        else:
            self.orchestrator_frame.pack(fill=tk.X, padx=5, pady=(0, 5), 
                                        before=self.analysis_text.master.master)
            self.toggle_orchestrator_btn.config(text="Orchestrator ▲")
            self.orchestrator_expanded = True
    
    def toggle_prompt_section(self):
        """Toggle the visibility of the prompt section"""
        if self.prompt_expanded:
            self.prompt_frame.pack_forget()
            self.toggle_prompt_btn.config(text="Prompt ▼")
            self.prompt_expanded = False
        else:
            self.prompt_frame.pack(fill=tk.X, padx=5, pady=(0, 5), 
                                  before=self.analysis_text.master.master)
            self.toggle_prompt_btn.config(text="Prompt ▲")
            self.prompt_expanded = True
    
    def clear_chat(self):
        """Clear the chat history and analysis text"""
        self.chat_history.clear()
        self.analysis_text.delete(1.0, tk.END)
    
    def display_analysis(self, analysis, prompt_type="AI", prompt_text=""):
        """Display AI analysis result in continuous chat format"""
        current_content = self.analysis_text.get(1.0, tk.END).strip()
        
        if current_content:
            self.analysis_text.insert(tk.END, "\n\n" + "="*60 + "\n\n")
        
        # Add timestamp
        timestamp = datetime.now().strftime("%H:%M:%S")
        
        # Add prompt type and timestamp header
        if prompt_type == "orchestrator":
            header = f"🎭 ORCHESTRATOR PROMPT [{timestamp}]:\n"
        else:
            header = f"✏️ ANALYSIS PROMPT [{timestamp}]:\n"
        
        self.analysis_text.insert(tk.END, header)
        
        # Insert the actual prompt used (truncated if too long)
        if prompt_text:
            display_prompt = prompt_text[:200] + "..." if len(prompt_text) > 200 else prompt_text
            self.analysis_text.insert(tk.END, f"{display_prompt}\n\n")
        
        # Insert response
        self.analysis_text.insert(tk.END, f"🤖 RESPONSE:\n{analysis}")
        
        # Auto-scroll to bottom
        self.analysis_text.see(tk.END)
    
    def display_session_history(self, session):
        """Display all entries from a chat session"""
        self.analysis_text.delete(1.0, tk.END)
        
        if not session.entries:
            self.analysis_text.insert('1.0', f"Session: {session.session_name}\n\nNo conversations yet. Start chatting with AI!")
            return
        
        # Add session header
        session_header = f"📝 Session: {session.session_name}\n"
        session_header += f"🕒 Created: {session.get_formatted_date()}\n"
        session_header += f"💬 {len(session.entries)} conversations\n"
        session_header += "="*60 + "\n\n"
        
        self.analysis_text.insert(tk.END, session_header)
        
        # Display each entry
        for i, entry in enumerate(session.entries, 1):
            # Entry separator
            if i > 1:
                self.analysis_text.insert(tk.END, "\n" + "="*60 + "\n\n")
            
            # Entry header
            timestamp = entry.get_formatted_time()
            prompt_type = "🎭" if entry.prompt_type == "orchestrator" else "✏️"
            header = f"{i}. {prompt_type} {entry.prompt_type.upper()} [{timestamp}]:\n"
            self.analysis_text.insert(tk.END, header)
            
            # Prompt text
            self.analysis_text.insert(tk.END, f"Q: {entry.prompt_text}\n\n")
            
            # Response text
            self.analysis_text.insert(tk.END, f"🤖 RESPONSE:\n{entry.response_text}\n")
            
            # Token info if available
            if entry.token_usage and entry.token_usage.get('total_tokens', 0) > 0:
                tokens = entry.token_usage.get('total_tokens', 0)
                self.analysis_text.insert(tk.END, f"\n🔢 Tokens: {tokens:,} | Model: {entry.model_used}")
        
        # Auto-scroll to bottom
        self.analysis_text.see(tk.END)
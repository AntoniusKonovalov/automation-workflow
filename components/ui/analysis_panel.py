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
        self.send_to_agent_callback = None  # Will be set by main app
        
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
    
    def display_analysis(self, analysis, prompt_type="AI", prompt_text="", model_used=None):
        """Display AI analysis result in continuous chat format"""
        current_content = self.analysis_text.get(1.0, tk.END).strip()
        
        if current_content:
            self.analysis_text.insert(tk.END, "\n\n" + "="*60 + "\n\n")
        
        # Add timestamp
        timestamp = datetime.now().strftime("%H:%M:%S")
        
        # Add prompt type and timestamp header
        if prompt_type == "orchestrator":
            header = f"🎭 ORCHESTRATOR PROMPT [{timestamp}]:\n"
        elif prompt_type == "Claude Agent":
            header = f"🤖 CLAUDE AGENT RESPONSE [{timestamp}]:\n"
        elif prompt_type == "Error":
            header = f"❌ ERROR [{timestamp}]:\n"
        else:
            header = f"✏️ ANALYSIS PROMPT [{timestamp}]:\n"
        
        self.analysis_text.insert(tk.END, header)
        
        # Insert the actual prompt used (truncated if too long)
        # For Claude Agent responses, don't show the prompt text as it's already the response
        if prompt_text and prompt_type not in ["Claude Agent", "Error"]:
            display_prompt = prompt_text[:200] + "..." if len(prompt_text) > 200 else prompt_text
            self.analysis_text.insert(tk.END, f"{display_prompt}\n\n")
        
        # Insert response
        response_start = self.analysis_text.index(tk.END)
        
        # For Claude Agent responses, don't add "RESPONSE:" prefix as it's already a response
        if prompt_type == "Claude Agent":
            self.analysis_text.insert(tk.END, f"{analysis}")
        elif prompt_type == "Error":
            self.analysis_text.insert(tk.END, f"{analysis}")
        else:
            # Include model name if available
            if model_used:
                # Get display name for the model
                model_display = model_used.upper() if model_used else "AI"
                self.analysis_text.insert(tk.END, f"🤖 {model_display} RESPONSE:\n{analysis}")
            else:
                self.analysis_text.insert(tk.END, f"🤖 RESPONSE:\n{analysis}")
        
        response_end = self.analysis_text.index(tk.END)
        
        # Add "Send to Agent" button after the response (except for errors)
        if prompt_type != "Error":
            self.add_send_to_agent_button(analysis, response_end)
        
        # Auto-scroll to bottom
        self.analysis_text.see(tk.END)
    
    def add_send_to_agent_button(self, response_text, position):
        """Add a 'Send to Agent' button after the response"""
        print(f"DEBUG: Adding Send to Agent button for response: {response_text[:50]}...")
        
        try:
            # Add spacing before button
            self.analysis_text.insert(tk.END, "\n\n")
            
            # Create a frame that spans the full width for right alignment
            button_container = tk.Frame(self.analysis_text, bg=self.theme.colors['chat_ai'])
            
            # Create the button with custom styling
            send_button = tk.Button(button_container,
                                  text="Send to Agent →",
                                  font=self.theme.fonts['button'],
                                  fg='#10a37f',  # Green text
                                  bg=self.theme.colors['chat_ai'],  # Match background
                                  activeforeground='#1a7f64',  # Darker green on click
                                  activebackground=self.theme.colors['chat_ai'],
                                  relief='solid',  # Solid relief for grey border
                                  borderwidth=1,
                                  bd=1,
                                  highlightthickness=0,
                                  cursor='hand2',
                                  padx=15,
                                  pady=5,
                                  command=lambda text=response_text: self.handle_send_to_agent(text))
            
            # Pack button to the right of the container
            send_button.pack(side=tk.RIGHT, padx=(0, 20), pady=(0, 5))
            
            # Insert the container frame into the text widget
            self.analysis_text.window_create(tk.END, window=button_container, stretch=True)
            
            # Add final spacing
            self.analysis_text.insert(tk.END, "\n")
            
            print("DEBUG: Send to Agent button added successfully!")
            
        except Exception as e:
            print(f"DEBUG: Error adding Send to Agent button: {e}")
            # Fallback: just add text indicating where button should be
            self.analysis_text.insert(tk.END, "\n[Send to Agent button should appear here]\n")
    
    def handle_send_to_agent(self, response_text):
        """Handle the Send to Agent button click"""
        print(f"DEBUG: Send to Agent button clicked!")
        print(f"DEBUG: Response text length: {len(response_text)}")
        print(f"DEBUG: Callback available: {self.send_to_agent_callback is not None}")
        
        # Get main window and preserve its geometry
        main_window = None
        original_geometry = None
        
        try:
            # Get main window reference (traverse up the widget hierarchy)
            main_window = self.parent
            while main_window and not hasattr(main_window, 'geometry'):
                main_window = main_window.master if hasattr(main_window, 'master') else main_window.winfo_parent()
            
            if main_window and hasattr(main_window, 'geometry'):
                original_geometry = main_window.geometry()
                print(f"DEBUG: Preserving main window geometry: {original_geometry}")
        except Exception as e:
            print(f"DEBUG: Error getting main window geometry: {e}")
        
        if self.send_to_agent_callback:
            try:
                print("DEBUG: Calling send_to_agent_callback...")
                self.send_to_agent_callback(response_text)
                print("DEBUG: Callback completed successfully")
                
                # Restore original geometry if it changed
                if main_window and original_geometry:
                    try:
                        current_geometry = main_window.geometry()
                        if current_geometry != original_geometry:
                            print(f"DEBUG: Restoring window geometry from {current_geometry} to {original_geometry}")
                            main_window.geometry(original_geometry)
                    except Exception as restore_error:
                        print(f"DEBUG: Error restoring geometry: {restore_error}")
                        
            except Exception as e:
                print(f"DEBUG: Error in callback: {e}")
                import traceback
                traceback.print_exc()
        else:
            print(f"DEBUG: No callback set - response text: {response_text[:100]}...")
    
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
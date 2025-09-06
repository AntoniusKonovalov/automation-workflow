"""
Claude Runner Module
Handles headless Claude Code integration for automated workflows
"""

import subprocess
import tempfile
import os
import threading
import time
import json
import platform
from pathlib import Path


class ClaudeRunner:
    """Manages headless Claude Code execution and response handling"""
    
    def __init__(self):
        self.active_sessions = {}  # Track active Claude processes
        self.session_counter = 0
        self.last_session_id = None  # Store session ID for context continuity
        self.session_file = Path.home() / '.claude_workflow_sessions.json'
        self.load_session_data()
        
    def execute_claude_prompt(self, prompt_text, working_directory=None, timeout=300, enable_editing=True, resume_session_id=None, allowed_tools=None):
        """
        Execute a prompt using headless Claude Code with proper flags
        
        Args:
            prompt_text (str): The prompt to send to Claude
            working_directory (str): Working directory for Claude execution
            timeout (int): Timeout in seconds (default 5 minutes)
            enable_editing (bool): Allow Claude to edit files (default True)
            resume_session_id (str): Session ID to resume for context continuity
            allowed_tools (list): List of allowed tool patterns
            
        Returns:
            tuple: (success: bool, result: str, error: str)
        """
        try:
            if not working_directory:
                working_directory = os.getcwd()
            
            # Validate working directory exists
            if not os.path.exists(working_directory):
                return False, "", f"Working directory does not exist: {working_directory}"
            
            print(f"DEBUG: Executing Claude prompt in directory: {working_directory}")
            print(f"DEBUG: Prompt length: {len(prompt_text)} characters")
            
            # Create temporary file for the prompt
            with tempfile.NamedTemporaryFile(mode='w', suffix='.txt', delete=False, encoding='utf-8') as temp_file:
                temp_file.write(prompt_text)
                temp_path = temp_file.name
            
            try:
                # Build command with proper Claude Code flags for headless operation
                args = ['claude']
                
                # Context management: resume specific session or continue in repo
                if resume_session_id:
                    args.extend(['--resume', str(resume_session_id)])
                else:
                    args.append('--continue')  # Reuse latest session in this repo
                
                # Important: Only use print mode (-p) when NOT editing files
                # Print mode prevents file edits from happening
                if not enable_editing:
                    # Read-only mode: use print mode for text-only responses
                    args.extend(['-p', '--output-format', 'json'])
                    permission_mode = 'plan'
                else:
                    # Edit mode: NO print flag, but still get JSON output
                    args.extend(['--output-format', 'json'])
                    permission_mode = 'acceptEdits'
                
                # Set permission mode
                args.extend(['--permission-mode', permission_mode])
                
                # Add specific allowed tools if provided
                if allowed_tools:
                    for tool in allowed_tools:
                        args.extend(['--allowedTools', tool])
                
                # Execute Claude with proper platform handling
                use_shell = platform.system() == 'Windows'
                if use_shell:
                    # Windows: join args into string for shell=True
                    cmd = ' '.join(args)
                    result = subprocess.run(
                        cmd,
                        input=prompt_text,
                        cwd=working_directory,
                        capture_output=True,
                        text=True,
                        encoding='utf-8',
                        timeout=timeout,
                        shell=True
                    )
                else:
                    # Unix: use args list
                    result = subprocess.run(
                        args,
                        input=prompt_text,
                        cwd=working_directory,
                        capture_output=True,
                        text=True,
                        encoding='utf-8',
                        timeout=timeout
                    )
                
                # Clean up temp file
                try:
                    os.unlink(temp_path)
                except:
                    pass
                
                if result.returncode == 0:
                    print(f"DEBUG: Claude execution successful")
                    output = result.stdout.strip()
                    
                    # Try to parse JSON output and extract session_id
                    try:
                        json_output = json.loads(output)
                        
                        # Check for error responses
                        if json_output.get('is_error', False):
                            error_msg = json_output.get('error_message', 'Unknown error from Claude')
                            print(f"DEBUG: Claude returned error: {error_msg}")
                            return False, "", error_msg
                        
                        # Store session_id if present for future context
                        if 'session_id' in json_output:
                            self.last_session_id = json_output['session_id']
                            print(f"DEBUG: Stored session_id: {self.last_session_id}")
                            # Save to disk for persistence
                            self.save_session_data()
                        
                        # Handle permission denials
                        if 'permission_denials' in json_output and json_output['permission_denials']:
                            denials = json_output['permission_denials']
                            print(f"DEBUG: Permission denials: {denials}")
                        
                        # Return the actual response text
                        if 'result' in json_output:
                            result_text = json_output['result']
                            # Handle empty results
                            if not result_text or result_text.strip() == "":
                                print("DEBUG: Empty result from Claude, likely file edits were made")
                                result_text = "Claude completed the task. Check your files for changes."
                            return True, result_text, ""
                        elif 'message' in json_output:
                            # Sometimes the response is in 'message' field
                            return True, json_output['message'], ""
                        else:
                            # In plan mode, might get plain text or other structure
                            # Try to return a sensible default
                            return True, json_output.get('result', output), ""
                    except json.JSONDecodeError:
                        # Not JSON, return raw output (common in plan mode)
                        print(f"DEBUG: Response is not JSON, returning raw output")
                        return True, output, ""
                else:
                    error_msg = result.stderr.strip() if result.stderr else f"Claude failed with return code {result.returncode}"
                    print(f"DEBUG: Claude execution failed: {error_msg}")
                    return False, "", error_msg
                    
            except subprocess.TimeoutExpired:
                # Clean up temp file on timeout
                try:
                    os.unlink(temp_path)
                except:
                    pass
                return False, "", f"Claude execution timed out after {timeout} seconds"
            
            except FileNotFoundError:
                # Clean up temp file
                try:
                    os.unlink(temp_path)
                except:
                    pass
                return False, "", "Claude Code CLI not found. Please ensure 'claude' command is available in PATH."
            
        except Exception as e:
            print(f"DEBUG: Exception in execute_claude_prompt: {e}")
            return False, "", str(e)
    
    def execute_claude_prompt_async(self, prompt_text, working_directory=None, callback=None, timeout=300, enable_editing=True, resume_session_id=None, allowed_tools=None):
        """
        Execute Claude prompt asynchronously in background thread
        
        Args:
            prompt_text (str): The prompt to send to Claude
            working_directory (str): Working directory for Claude execution
            callback (callable): Callback function to handle results: callback(success, result, error)
            timeout (int): Timeout in seconds
            enable_editing (bool): Allow Claude to edit files (default True)
            resume_session_id (str): Session ID to resume for context
            allowed_tools (list): List of allowed tool patterns
        """
        def run_async():
            try:
                success, result, error = self.execute_claude_prompt(
                    prompt_text, working_directory, timeout, enable_editing,
                    resume_session_id, allowed_tools
                )
                if callback:
                    callback(success, result, error)
            except Exception as e:
                if callback:
                    callback(False, "", str(e))
        
        thread = threading.Thread(target=run_async, daemon=True)
        thread.start()
        return thread
    
    def is_claude_available(self):
        """
        Check if Claude Code CLI is available
        
        Returns:
            bool: True if Claude is available, False otherwise
        """
        try:
            if platform.system() == 'Windows':
                result = subprocess.run(
                    'claude --version',
                    capture_output=True,
                    text=True,
                    timeout=10,
                    shell=True
                )
            else:
                result = subprocess.run(
                    ['claude', '--version'],
                    capture_output=True,
                    text=True,
                    timeout=10
                )
            return result.returncode == 0
        except (subprocess.TimeoutExpired, FileNotFoundError, Exception):
            return False
    
    def get_claude_version(self):
        """
        Get Claude Code CLI version
        
        Returns:
            str: Version string or error message
        """
        try:
            if platform.system() == 'Windows':
                result = subprocess.run(
                    'claude --version',
                    capture_output=True,
                    text=True,
                    timeout=10,
                    shell=True
                )
            else:
                result = subprocess.run(
                    ['claude', '--version'],
                    capture_output=True,
                    text=True,
                    timeout=10
                )
            if result.returncode == 0:
                return result.stdout.strip()
            else:
                return "Version not available"
        except Exception as e:
            return f"Error getting version: {e}"
    
    def create_session_prompt(self, files_content, custom_prompt=""):
        """
        Create a formatted prompt for Claude with file context
        
        Args:
            files_content (str): Content of selected files
            custom_prompt (str): Additional custom prompt text
            
        Returns:
            str: Formatted prompt for Claude
        """
        session_prompt = []
        
        # Add context header
        session_prompt.append("# Git Workflow Analysis Request")
        session_prompt.append("")
        session_prompt.append("I'm working on a git project and need your analysis of the following changed files:")
        session_prompt.append("")
        
        # Add custom prompt if provided
        if custom_prompt.strip():
            session_prompt.append("## Analysis Instructions:")
            session_prompt.append(custom_prompt.strip())
            session_prompt.append("")
        
        # Add files content
        session_prompt.append("## Files for Analysis:")
        session_prompt.append("")
        session_prompt.append(files_content)
        session_prompt.append("")
        
        # Add request for actionable response with tool usage guidance
        session_prompt.append("## Please provide:")
        session_prompt.append("1. Analysis of the changes and potential issues")
        session_prompt.append("2. Specific recommendations for improvements")
        session_prompt.append("3. If fixes are needed, USE THE AVAILABLE TOOLS to make the actual changes:")
        session_prompt.append("   - Use the Edit tool to modify existing files")
        session_prompt.append("   - Use the Write tool to create new files")
        session_prompt.append("   - Use the MultiEdit tool for multiple changes to one file")
        session_prompt.append("   - Use Read tool to examine files before editing")
        session_prompt.append("")
        session_prompt.append("When you identify issues that can be fixed, please ACTUALLY FIX THEM using the tools rather than just suggesting changes.")
        session_prompt.append("Focus on actionable insights and make the necessary improvements directly to the codebase.")
        
        return "\n".join(session_prompt)
    
    def cleanup_session(self, session_id):
        """Clean up resources for a session"""
        if session_id in self.active_sessions:
            session_info = self.active_sessions[session_id]
            # Clean up any temporary files or processes
            del self.active_sessions[session_id]
            print(f"DEBUG: Cleaned up Claude session {session_id}")
    
    def load_session_data(self):
        """Load saved session data from disk"""
        try:
            if self.session_file.exists():
                with open(self.session_file, 'r') as f:
                    data = json.load(f)
                    self.last_session_id = data.get('last_session_id')
                    print(f"DEBUG: Loaded session ID from disk: {self.last_session_id}")
        except Exception as e:
            print(f"DEBUG: Could not load session data: {e}")
    
    def save_session_data(self):
        """Save session data to disk for persistence"""
        try:
            data = {'last_session_id': self.last_session_id}
            with open(self.session_file, 'w') as f:
                json.dump(data, f)
                print(f"DEBUG: Saved session ID to disk: {self.last_session_id}")
        except Exception as e:
            print(f"DEBUG: Could not save session data: {e}")
"""
Chat History Manager Module
Handles storage and retrieval of chat history per project
"""

import json
import os
from datetime import datetime
from pathlib import Path
import hashlib


class ChatEntry:
    """Represents a single chat interaction"""
    def __init__(self, timestamp, prompt_type, prompt_text, response_text, model_used, token_usage=None):
        self.timestamp = timestamp
        self.prompt_type = prompt_type  # 'orchestrator' or 'prompt'
        self.prompt_text = prompt_text
        self.response_text = response_text
        self.model_used = model_used
        self.token_usage = token_usage or {}
        self.id = self._generate_id()
    
    def _generate_id(self):
        """Generate unique ID for this chat entry"""
        content = f"{self.timestamp}{self.prompt_text[:100]}"
        return hashlib.md5(content.encode()).hexdigest()[:8]
    
    def to_dict(self):
        """Convert to dictionary for JSON storage"""
        return {
            'id': self.id,
            'timestamp': self.timestamp,
            'prompt_type': self.prompt_type,
            'prompt_text': self.prompt_text,
            'response_text': self.response_text,
            'model_used': self.model_used,
            'token_usage': self.token_usage
        }
    
    @classmethod
    def from_dict(cls, data):
        """Create ChatEntry from dictionary"""
        entry = cls(
            data['timestamp'],
            data['prompt_type'],
            data['prompt_text'],
            data['response_text'],
            data['model_used'],
            data.get('token_usage', {})
        )
        entry.id = data.get('id', entry.id)
        return entry
    
    def get_preview(self, max_length=50):
        """Get short preview of the chat"""
        preview = self.prompt_text.replace('\n', ' ').strip()
        if len(preview) > max_length:
            preview = preview[:max_length] + "..."
        return preview
    
    def get_formatted_time(self):
        """Get human-readable timestamp"""
        try:
            dt = datetime.fromisoformat(self.timestamp)
            return dt.strftime("%m/%d %H:%M")
        except:
            return self.timestamp[:16]


class ChatHistoryManager:
    """Manages chat history storage per project"""
    
    def __init__(self):
        self.history_dir = Path.home() / '.git_workflow_automator' / 'chat_history'
        self.history_dir.mkdir(parents=True, exist_ok=True)
        self.current_project_history = []
        self.current_project_path = None
    
    def _get_project_id(self, project_path):
        """Generate a unique project ID from path"""
        if not project_path:
            return "default"
        return hashlib.md5(str(project_path).encode()).hexdigest()[:12]
    
    def _get_history_file(self, project_path):
        """Get history file path for a project"""
        project_id = self._get_project_id(project_path)
        return self.history_dir / f"history_{project_id}.json"
    
    def load_project_history(self, project_path):
        """Load chat history for a specific project"""
        self.current_project_path = project_path
        history_file = self._get_history_file(project_path)
        
        if not history_file.exists():
            self.current_project_history = []
            return []
        
        try:
            with open(history_file, 'r', encoding='utf-8') as f:
                data = json.load(f)
            
            # Convert to ChatEntry objects
            self.current_project_history = [
                ChatEntry.from_dict(entry_data) for entry_data in data.get('entries', [])
            ]
            
            return self.current_project_history
            
        except Exception as e:
            print(f"Error loading chat history: {e}")
            self.current_project_history = []
            return []
    
    def save_project_history(self):
        """Save current project's chat history"""
        if not self.current_project_path:
            return
        
        history_file = self._get_history_file(self.current_project_path)
        
        try:
            data = {
                'project_path': str(self.current_project_path),
                'last_updated': datetime.now().isoformat(),
                'entries': [entry.to_dict() for entry in self.current_project_history]
            }
            
            with open(history_file, 'w', encoding='utf-8') as f:
                json.dump(data, f, indent=2, ensure_ascii=False)
                
        except Exception as e:
            print(f"Error saving chat history: {e}")
    
    def add_chat_entry(self, prompt_type, prompt_text, response_text, model_used, token_usage=None):
        """Add a new chat entry to current project"""
        timestamp = datetime.now().isoformat()
        entry = ChatEntry(timestamp, prompt_type, prompt_text, response_text, model_used, token_usage)
        
        self.current_project_history.append(entry)
        
        # Keep only last 50 entries to prevent file size issues
        if len(self.current_project_history) > 50:
            self.current_project_history = self.current_project_history[-50:]
        
        self.save_project_history()
        return entry
    
    def get_recent_chats(self, limit=10):
        """Get most recent chat entries"""
        return self.current_project_history[-limit:] if self.current_project_history else []
    
    def clear_current_project_history(self):
        """Clear chat history for current project"""
        self.current_project_history = []
        self.save_project_history()
    
    def get_history_summary(self):
        """Get summary of current project's history"""
        total_chats = len(self.current_project_history)
        if total_chats == 0:
            return "No chat history"
        
        recent_chat = self.current_project_history[-1] if self.current_project_history else None
        if recent_chat:
            last_time = recent_chat.get_formatted_time()
            return f"{total_chats} chats (Last: {last_time})"
        
        return f"{total_chats} chats"
    
    def delete_chat_entry(self, entry_id):
        """Delete a specific chat entry"""
        self.current_project_history = [
            entry for entry in self.current_project_history 
            if entry.id != entry_id
        ]
        self.save_project_history()
    
    def get_all_project_histories(self):
        """Get list of all projects with chat history"""
        history_files = list(self.history_dir.glob("history_*.json"))
        projects = []
        
        for file_path in history_files:
            try:
                with open(file_path, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                
                projects.append({
                    'project_path': data.get('project_path', 'Unknown'),
                    'last_updated': data.get('last_updated', ''),
                    'entry_count': len(data.get('entries', []))
                })
            except Exception:
                continue
        
        return projects
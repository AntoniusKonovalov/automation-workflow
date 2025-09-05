"""
Chat History Manager Module
Handles storage and retrieval of chat history per project
"""

import json
import os
from datetime import datetime
from pathlib import Path
import hashlib
import uuid


class ChatSession:
    """Represents a chat session with multiple entries"""
    def __init__(self, session_name=None, session_id=None):
        self.session_id = session_id or str(uuid.uuid4())[:8]
        self.session_name = session_name or "New Chat"
        self.created_at = datetime.now().isoformat()
        self.updated_at = self.created_at
        self.entries = []
        self.is_saved = False
        self.auto_named = False
    
    def add_entry(self, entry):
        """Add a chat entry to this session"""
        self.entries.append(entry)
        self.updated_at = datetime.now().isoformat()
        self.is_saved = False
    
    def to_dict(self):
        """Convert session to dictionary for JSON storage"""
        return {
            'session_id': self.session_id,
            'session_name': self.session_name,
            'created_at': self.created_at,
            'updated_at': self.updated_at,
            'entries': [entry.to_dict() for entry in self.entries],
            'is_saved': self.is_saved,
            'auto_named': self.auto_named
        }
    
    @classmethod
    def from_dict(cls, data):
        """Create ChatSession from dictionary"""
        session = cls(
            session_name=data.get('session_name', 'New Chat'),
            session_id=data.get('session_id')
        )
        session.created_at = data.get('created_at', session.created_at)
        session.updated_at = data.get('updated_at', session.updated_at)
        session.is_saved = data.get('is_saved', False)
        session.auto_named = data.get('auto_named', False)
        session.entries = [ChatEntry.from_dict(entry_data) for entry_data in data.get('entries', [])]
        return session
    
    def get_preview(self):
        """Get a preview of the session for display"""
        if not self.entries:
            return "Empty session"
        first_entry = self.entries[0]
        return first_entry.prompt_text[:50] + "..." if len(first_entry.prompt_text) > 50 else first_entry.prompt_text
    
    def get_formatted_date(self):
        """Get formatted date for display"""
        try:
            dt = datetime.fromisoformat(self.updated_at)
            return dt.strftime("%m/%d %H:%M")
        except:
            return self.updated_at[:16]


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
    """Manages chat sessions and history storage per project"""
    
    def __init__(self):
        self.history_dir = Path.home() / '.git_workflow_automator' / 'chat_history'
        self.history_dir.mkdir(parents=True, exist_ok=True)
        
        # Session management
        self.current_project_path = None
        self.project_sessions = {}  # Dict of project_id -> list of sessions
        self.current_session = None
        self.active_session_id = None
        
        # Legacy support
        self.current_project_history = []
    
    def _get_project_id(self, project_path):
        """Generate a unique project ID from path"""
        if not project_path:
            return "default"
        return hashlib.md5(str(project_path).encode()).hexdigest()[:12]
    
    def _get_sessions_file(self, project_path):
        """Get sessions file path for a project"""
        project_id = self._get_project_id(project_path)
        return self.history_dir / f"sessions_{project_id}.json"
    
    def _get_history_file(self, project_path):
        """Get legacy history file path for a project (for migration)"""
        project_id = self._get_project_id(project_path)
        return self.history_dir / f"history_{project_id}.json"
    
    def load_project_sessions(self, project_path):
        """Load chat sessions for a specific project"""
        self.current_project_path = project_path
        project_id = self._get_project_id(project_path)
        
        # Load existing sessions
        sessions_file = self._get_sessions_file(project_path)
        sessions = []
        
        if sessions_file.exists():
            try:
                with open(sessions_file, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                sessions = [ChatSession.from_dict(session_data) for session_data in data.get('sessions', [])]
            except Exception as e:
                print(f"Error loading sessions: {e}")
        
        # Migrate legacy history if exists and no sessions
        if not sessions:
            legacy_file = self._get_history_file(project_path)
            if legacy_file.exists():
                sessions = self._migrate_legacy_history(legacy_file)
        
        self.project_sessions[project_id] = sessions
        
        # Set up current session
        if not sessions:
            self.start_new_session()
        else:
            # Load the most recent session as current
            self.current_session = sessions[-1] if sessions else None
            self.active_session_id = self.current_session.session_id if self.current_session else None
        
        # Update legacy support
        self.current_project_history = self.current_session.entries if self.current_session else []
        
        return sessions
    
    def _migrate_legacy_history(self, legacy_file):
        """Migrate old chat history to session format"""
        try:
            with open(legacy_file, 'r', encoding='utf-8') as f:
                data = json.load(f)
            
            entries = [ChatEntry.from_dict(entry_data) for entry_data in data.get('entries', [])]
            if entries:
                # Create a session from legacy entries with auto-generated name
                first_entry = entries[0]
                session_name = self._generate_session_name(first_entry.prompt_text)
                session = ChatSession(session_name=session_name)
                session.entries = entries
                session.created_at = entries[0].timestamp if entries else session.created_at
                session.updated_at = entries[-1].timestamp if entries else session.updated_at
                session.is_saved = True
                session.auto_named = True
                return [session]
        except Exception as e:
            print(f"Error migrating legacy history: {e}")
        return []
    
    def start_new_session(self, session_name="New Chat"):
        """Start a new chat session"""
        self.current_session = ChatSession(session_name=session_name)
        self.active_session_id = self.current_session.session_id
        
        # Add to project sessions
        if self.current_project_path:
            project_id = self._get_project_id(self.current_project_path)
            if project_id not in self.project_sessions:
                self.project_sessions[project_id] = []
            self.project_sessions[project_id].append(self.current_session)
        
        # Update legacy support
        self.current_project_history = []
        return self.current_session
    
    def get_project_sessions(self, project_path=None):
        """Get all sessions for a project"""
        path = project_path or self.current_project_path
        if not path:
            return []
        project_id = self._get_project_id(path)
        return self.project_sessions.get(project_id, [])
    
    def switch_to_session(self, session_id):
        """Switch to a specific session"""
        project_id = self._get_project_id(self.current_project_path)
        sessions = self.project_sessions.get(project_id, [])
        
        for session in sessions:
            if session.session_id == session_id:
                self.current_session = session
                self.active_session_id = session_id
                self.current_project_history = session.entries  # Legacy support
                return session
        return None
    
    def save_project_sessions(self):
        """Save all sessions for current project"""
        if not self.current_project_path:
            return
        
        sessions_file = self._get_sessions_file(self.current_project_path)
        project_id = self._get_project_id(self.current_project_path)
        sessions = self.project_sessions.get(project_id, [])
        
        try:
            data = {
                'project_path': str(self.current_project_path),
                'last_updated': datetime.now().isoformat(),
                'sessions': [session.to_dict() for session in sessions]
            }
            
            with open(sessions_file, 'w', encoding='utf-8') as f:
                json.dump(data, f, indent=2, ensure_ascii=False)
                
        except Exception as e:
            print(f"Error saving sessions: {e}")
    
    def add_chat_entry(self, prompt_type, prompt_text, response_text, model_used, token_usage=None):
        """Add a new chat entry to current session"""
        timestamp = datetime.now().isoformat()
        entry = ChatEntry(timestamp, prompt_type, prompt_text, response_text, model_used, token_usage)
        
        # Ensure we have a current session
        if not self.current_session:
            self.start_new_session()
        
        # Add to current session
        self.current_session.add_entry(entry)
        
        # Update legacy support
        self.current_project_history = self.current_session.entries
        
        # Auto-name session if it's the first entry and not already named
        if len(self.current_session.entries) == 1 and not self.current_session.auto_named:
            self._schedule_auto_naming()
        
        # Keep sessions reasonable size (move old entries to separate sessions if needed)
        if len(self.current_session.entries) > 50:
            self._split_session()
        
        self.save_project_sessions()
        return entry
    
    def _schedule_auto_naming(self):
        """Schedule automatic naming of the current session"""
        if self.current_session and len(self.current_session.entries) == 1:
            # Use the first entry's prompt as basis for naming
            first_entry = self.current_session.entries[0]
            session_name = self._generate_session_name(first_entry.prompt_text)
            self.current_session.session_name = session_name
            self.current_session.auto_named = True
    
    def _generate_session_name(self, prompt_text):
        """Generate a descriptive session name from the prompt text"""
        # Clean the prompt text
        text = prompt_text.strip()
        
        # Remove common prefixes and instructions
        prefixes_to_remove = [
            "Make a deep analysis of these code changes. Focus on:",
            "Generate a text prompt for orchestrator Claude agent",
            "Please analyze",
            "Can you help me",
            "I need help with",
            "Looking at this code",
        ]
        
        for prefix in prefixes_to_remove:
            if text.startswith(prefix):
                text = text[len(prefix):].strip()
                break
        
        # Extract key words/topics
        words = text.split()
        
        # Look for code-related keywords
        code_keywords = ['bug', 'error', 'fix', 'refactor', 'optimize', 'implement', 
                        'function', 'class', 'api', 'database', 'ui', 'frontend', 
                        'backend', 'security', 'performance', 'test', 'debug']
        
        found_keywords = [word.lower() for word in words[:20] if word.lower().strip('.,!?:') in code_keywords]
        
        if found_keywords:
            # Use the first few keywords
            name = ' '.join(found_keywords[:3]).title()
        else:
            # Fallback: use first few meaningful words
            meaningful_words = [w for w in words[:10] if len(w) > 3 and w.lower() not in 
                              ['with', 'this', 'that', 'they', 'them', 'these', 'those']]
            if meaningful_words:
                name = ' '.join(meaningful_words[:4])
            else:
                # Last resort: use first few words
                name = ' '.join(words[:4]) if words else "New Session"
        
        # Capitalize and limit length
        name = name.title()
        if len(name) > 50:
            name = name[:47] + "..."
        
        return name or "Chat Session"
    
    def _split_session(self):
        """Split a session if it gets too large"""
        if len(self.current_session.entries) > 50:
            # Keep last 25 entries in current session
            old_entries = self.current_session.entries[:-25]
            self.current_session.entries = self.current_session.entries[-25:]
            
            # Create new session with old entries
            old_session = ChatSession(session_name=f"{self.current_session.session_name} (Part 1)")
            old_session.entries = old_entries
            old_session.created_at = old_entries[0].timestamp if old_entries else old_session.created_at
            old_session.updated_at = old_entries[-1].timestamp if old_entries else old_session.updated_at
            old_session.is_saved = True
            
            # Insert old session before current
            project_id = self._get_project_id(self.current_project_path)
            sessions = self.project_sessions.get(project_id, [])
            current_index = sessions.index(self.current_session) if self.current_session in sessions else len(sessions)
            sessions.insert(current_index, old_session)
    
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
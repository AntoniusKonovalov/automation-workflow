"""
File Manager Module
Handles file operations and filtering
"""

import os
import fnmatch
from pathlib import Path


class ChangedFile:
    """Represents a changed file with its metadata"""
    def __init__(self, abs_path, rel_path, status):
        self.abs_path = abs_path
        self.rel_path = rel_path
        self.status = status
        self.expanded = False
        self.loading = False
        self.error = None
        self.content_preview = None
        self.selected_for_analysis = False
        self.widgets = {}


class FileManager:
    """Manages file operations and filtering"""
    
    def __init__(self):
        self.exclude_paths = []
        self.excluded_extensions = {
            # Images
            '.jpg', '.jpeg', '.png', '.gif', '.bmp', '.svg', '.webp', '.ico', '.tiff',
            # Documents
            '.md', '.pdf', '.doc', '.docx',
            # Binaries
            '.exe', '.dll', '.so', '.dylib', '.bin', '.zip', '.tar', '.gz', '.rar',
            # Media
            '.mp4', '.avi', '.mov', '.mp3', '.wav', '.ogg',
            # Config files that are usually not for analysis
            '.lock', '.log', '.cache'
        }
        
        self.excluded_patterns = [
            '*test*', '*spec*', '*Tests*', '*__test__*', '*__spec__*',
            '*.test.*', '*.spec.*', 'test_*', 'spec_*',
            '*node_modules*', '*__pycache__*', '*dist*', '*build*',
            '*.min.*', '.gitignore', '.env*', 'package-lock.json', 'yarn.lock'
        ]
    
    def set_exclude_paths(self, paths):
        """Set paths/patterns to exclude from file processing"""
        if isinstance(paths, str):
            paths = [paths]
        self.exclude_paths = paths
    
    def is_path_excluded(self, filepath):
        """Check if a file path should be excluded"""
        # Get file extension and filename
        file_ext = os.path.splitext(filepath)[1].lower()
        filename = os.path.basename(filepath).lower()
        
        # Check file extension
        if file_ext in self.excluded_extensions:
            return True
        
        # Check filename patterns
        for pattern in self.excluded_patterns:
            if fnmatch.fnmatch(filename, pattern) or fnmatch.fnmatch(filepath, pattern):
                return True
        
        # Check user-defined exclude paths
        if self.exclude_paths:
            for pattern in self.exclude_paths:
                # Support both exact matches and glob patterns
                if fnmatch.fnmatch(filepath, pattern) or \
                   fnmatch.fnmatch(filepath, f"*/{pattern}") or \
                   filepath.startswith(pattern):
                    return True
        
        return False
    
    def load_file_content(self, file_obj):
        """Load content of a file"""
        try:
            if not os.path.exists(file_obj.abs_path):
                file_obj.content_preview = None
                file_obj.error = "File not found (deleted/renamed)"
                return False
                
            if os.path.isdir(file_obj.abs_path):
                file_obj.content_preview = None
                file_obj.error = "Directory (not previewable)"
                return False
                
            if not os.path.isfile(file_obj.abs_path):
                file_obj.content_preview = None
                file_obj.error = "Not a regular file"
                return False

            # Try to read file content
            content = None
            encodings = ['utf-8', 'latin-1', 'cp1252']

            for encoding in encodings:
                try:
                    with open(file_obj.abs_path, 'r', encoding=encoding) as f:
                        content = f.read()
                    break
                except UnicodeDecodeError:
                    continue
                except PermissionError:
                    file_obj.content_preview = None
                    file_obj.error = "Permission denied"
                    return False
                except OSError as e:
                    file_obj.content_preview = None
                    file_obj.error = f"Cannot read: {str(e)}"
                    return False

            if content is None:
                file_obj.content_preview = None
                file_obj.error = "Binary or unsupported encoding"
                return False
            elif len(content) > 50000:  # Large file
                content = content[:50000] + "\n\n... (Content truncated - file is large) ..."
                file_obj.content_preview = content
                file_obj.error = None
            else:
                file_obj.content_preview = content
                file_obj.error = None
            
            return True

        except Exception as e:
            file_obj.content_preview = None
            file_obj.error = f"Error: {str(e)}"
            return False
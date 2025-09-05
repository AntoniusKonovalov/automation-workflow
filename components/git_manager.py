"""
Git Manager Module
Handles all Git-related operations
"""

import subprocess
import os
from pathlib import Path


class GitManager:
    """Manages Git operations for the application"""
    
    def __init__(self):
        self.repo_root = ""
        
    def find_repo_root(self, start_path):
        """Find git repository root using git rev-parse"""
        try:
            result = subprocess.run(
                ['git', 'rev-parse', '--show-toplevel'],
                cwd=start_path,
                capture_output=True,
                text=True,
                check=True
            )
            self.repo_root = result.stdout.strip()
            return self.repo_root
        except subprocess.CalledProcessError:
            # Fallback: walk up directories to find .git
            current = Path(start_path)
            for parent in [current] + list(current.parents):
                if (parent / '.git').exists():
                    self.repo_root = str(parent)
                    return self.repo_root
            self.repo_root = start_path
            return start_path
    
    def get_changed_files(self, project_path):
        """Get list of changed files from git status"""
        if not project_path:
            return None, "No project path specified"
        
        try:
            # Find repository root
            repo_root = self.find_repo_root(project_path)
            
            # Get changed files using git with expanded untracked files
            result = subprocess.run(
                ['git', 'status', '--porcelain', '-u'],
                cwd=repo_root,
                capture_output=True,
                text=True,
                check=True
            )
            
            return result.stdout, None
            
        except subprocess.CalledProcessError as e:
            return None, f"Git command failed: {e}"
        except Exception as e:
            return None, f"Failed to get changed files: {e}"
    
    def parse_porcelain_line(self, line):
        """Parse git status --porcelain line robustly - handles both XY and X formats"""
        if not line or len(line) < 2:
            return None, None

        # Git porcelain format can be:
        # 1. Standard: XY<space>filename (X=index, Y=worktree)
        # 2. Simple: X<space>filename (single status char)
        
        # Try to find the space separator
        space_pos = -1
        for i in range(1, min(4, len(line))):  # Check positions 1, 2, 3
            if line[i] in [' ', '\t']:
                space_pos = i
                break
        
        if space_pos == -1:
            return None, None
        
        status_part = line[:space_pos]
        filepath = line[space_pos + 1:]  # Skip the separator
        
        if not filepath:  # Empty filename
            return None, None

        # Normalize status to always be 2 chars (pad with space if needed)
        if len(status_part) == 1:
            # Single char status (like "M") - this means modified in worktree
            status = " " + status_part  # Convert "M" to " M"
        else:
            status = status_part
        
        status = status.strip() if len(status.strip()) > 0 else status

        # Handle rename/copy cases (R/C status)
        if status and (status[0] in 'RC'):
            # Format: "old -> new"
            if ' -> ' in filepath:
                old_path, new_path = filepath.split(' -> ', 1)
                # Use the new path (right side)
                filepath = new_path

        return status, filepath
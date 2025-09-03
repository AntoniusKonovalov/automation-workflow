#!/usr/bin/env python3

"""
Test script to verify path handling fixes.
Tests the core path logic without GUI dependencies.
"""

import os
import subprocess
from pathlib import Path

def test_git_status_parsing():
    """Test git status output parsing to ensure no character truncation"""
    
    # Simulate git status --porcelain output
    sample_outputs = [
        "M  src/app.py",
        "A  src/components/header.js", 
        " M lib/utils.py",
        "?? new_file.txt",
        "D  old_file.py",
        "MM src/main.py"
    ]
    
    print("Testing git status parsing:")
    print("=" * 40)
    
    for line in sample_outputs:
        if line.strip():
            # Parse like the fixed code does
            status = line[:2].strip()
            filepath = line[3:] if len(line) > 3 else line[2:]
            
            print(f"Input: '{line}'")
            print(f"Status: '{status}'")  
            print(f"Path: '{filepath}'")
            print(f"First char of path: '{filepath[0] if filepath else 'EMPTY'}'")
            print()

def test_repo_root_finding():
    """Test repository root detection"""
    current_dir = os.getcwd()
    print(f"Testing repo root finding from: {current_dir}")
    
    try:
        # Try git rev-parse method
        result = subprocess.run(
            ['git', 'rev-parse', '--show-toplevel'], 
            cwd=current_dir,
            capture_output=True, 
            text=True, 
            check=True
        )
        git_root = result.stdout.strip()
        print(f"Git root via rev-parse: {git_root}")
    except subprocess.CalledProcessError:
        print("Git rev-parse failed - not in a git repo")
        
        # Fallback method
        current = Path(current_dir)
        for parent in [current] + list(current.parents):
            if (parent / '.git').exists():
                print(f"Git root via .git search: {parent}")
                break
        else:
            print(f"No .git found, using current dir: {current_dir}")

def test_path_normalization():
    """Test relative path creation"""
    print("\nTesting path normalization:")
    print("=" * 40)
    
    # Simulate various scenarios
    test_cases = [
        ("C:\\repo\\src\\app.py", "C:\\repo", "src/app.py"),
        ("/home/user/repo/lib/utils.py", "/home/user/repo", "lib/utils.py"),
        ("./src/main.py", ".", "src/main.py"),
        ("src/components/header.js", ".", "src/components/header.js")
    ]
    
    for abs_path, repo_root, expected_rel in test_cases:
        try:
            if os.name == 'nt':  # Windows
                abs_path_obj = Path(abs_path)
                repo_root_obj = Path(repo_root)
            else:  # Unix-like
                abs_path_obj = Path(abs_path)
                repo_root_obj = Path(repo_root)
            
            # This is how the fixed code does it
            rel_path = abs_path_obj.relative_to(repo_root_obj).as_posix()
            
            print(f"Abs: {abs_path}")
            print(f"Root: {repo_root}")
            print(f"Expected: {expected_rel}")
            print(f"Got: {rel_path}")
            print(f"Match: {rel_path == expected_rel}")
            print()
            
        except Exception as e:
            print(f"Error with {abs_path}: {e}")
            print()

if __name__ == "__main__":
    print("Path Handling Test Suite")
    print("=" * 50)
    
    test_git_status_parsing()
    test_repo_root_finding()  
    test_path_normalization()
    
    print("\nTest complete. Check output above for any issues.")
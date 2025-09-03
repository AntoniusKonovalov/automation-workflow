#!/usr/bin/env python3

"""
Debug script to analyze git status output and identify missing files
"""

import subprocess
import os
from pathlib import Path

def test_git_status(repo_path=None):
    """Test git status in the current directory or specified path"""
    
    if repo_path:
        os.chdir(repo_path)
    
    print("=== GIT STATUS DEBUG ===")
    print(f"Working directory: {os.getcwd()}")
    
    try:
        # Run git status --porcelain
        result = subprocess.run(
            ['git', 'status', '--porcelain'],
            capture_output=True,
            text=True,
            check=True
        )
        
        print(f"\nRaw git output (length: {len(result.stdout)}):")
        print(f"'{result.stdout}'")
        
        # Split into lines
        lines = result.stdout.strip().split('\n')
        print(f"\nTotal lines: {len(lines)}")
        
        for i, line in enumerate(lines):
            print(f"Line {i}: '{line}' (len: {len(line)})")
            
            if line.strip():
                # Show character by character for debugging
                print(f"  Chars: {[c for c in line[:10]]}")
                
                # Test the parsing logic
                if len(line) >= 3:
                    status_part = line[:2]
                    separator = line[2]
                    filepath = line[3:] if len(line) > 3 else ""
                    
                    print(f"  Status: '{status_part}' | Sep: '{separator}' | Path: '{filepath}'")
                    
                    if separator in [' ', '\t']:
                        print(f"  ✓ Valid format")
                    else:
                        print(f"  ✗ Invalid separator: '{separator}' (ord: {ord(separator)})")
        
        # Also try git status with different options
        print("\n=== ALTERNATIVE GIT COMMANDS ===")
        
        # Try git status short
        try:
            result2 = subprocess.run(['git', 'status', '-s'], capture_output=True, text=True, check=True)
            print(f"git status -s output:\n'{result2.stdout}'")
        except:
            print("git status -s failed")
        
        # Try git diff --name-status
        try:
            result3 = subprocess.run(['git', 'diff', '--name-status'], capture_output=True, text=True, check=True)
            print(f"git diff --name-status output:\n'{result3.stdout}'")
        except:
            print("git diff --name-status failed")
            
        # Try git diff --cached --name-status
        try:
            result4 = subprocess.run(['git', 'diff', '--cached', '--name-status'], capture_output=True, text=True, check=True)
            print(f"git diff --cached --name-status output:\n'{result4.stdout}'")
        except:
            print("git diff --cached --name-status failed")
            
    except subprocess.CalledProcessError as e:
        print(f"Git command failed: {e}")
        print(f"Error output: {e.stderr}")
    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    import sys
    
    if len(sys.argv) > 1:
        test_git_status(sys.argv[1])
    else:
        test_git_status()
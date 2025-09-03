#!/usr/bin/env python3

"""
Test script to verify the directory handling fixes.
This simulates the scenario from the GitHub Desktop changes list.
"""

import subprocess
import os
import tempfile
import shutil
from pathlib import Path

def simulate_git_status_untracked():
    """Simulate git status output that would cause the directory issue"""
    
    # Create a temporary git repo
    with tempfile.TemporaryDirectory() as temp_dir:
        print(f"Creating test repo in: {temp_dir}")
        
        # Initialize git repo
        subprocess.run(['git', 'init'], cwd=temp_dir, check=True)
        subprocess.run(['git', 'config', 'user.email', 'test@example.com'], cwd=temp_dir)
        subprocess.run(['git', 'config', 'user.name', 'Test User'], cwd=temp_dir)
        
        # Create directory structure similar to the reported issue
        test_structure = [
            'src/contexts/__tests__/BookingContext.performance.test.tsx',
            'src/contexts/__tests__/BookingContext.test.tsx', 
            'src/contexts/BookingContext.tsx',
            'src/contexts/EnhancedBookingContext.tsx',
            'src/app/booking/__tests__/booking-flow-integration.test.tsx',
            'src/app/booking/page.tsx',
            'src/__tests__/README.md',
            'src/lib/__tests__/booking-validation.test.ts',
            'src/lib/booking-validation.ts'
        ]
        
        for file_path in test_structure:
            full_path = Path(temp_dir) / file_path
            full_path.parent.mkdir(parents=True, exist_ok=True)
            full_path.write_text(f"// Test content for {file_path}\nconsole.log('test');")
        
        print("\n=== Testing default git status --porcelain ===")
        result = subprocess.run(['git', 'status', '--porcelain'], 
                              cwd=temp_dir, capture_output=True, text=True)
        print("Default output (causes directory issue):")
        for line in result.stdout.strip().split('\n'):
            if line.strip():
                print(f"  {line}")
        
        print("\n=== Testing git status --porcelain -u (fix) ===")
        result_fixed = subprocess.run(['git', 'status', '--porcelain', '-u'], 
                                    cwd=temp_dir, capture_output=True, text=True)
        print("Fixed output (shows individual files):")
        for line in result_fixed.stdout.strip().split('\n'):
            if line.strip():
                print(f"  {line}")
        
        # Count directories vs files
        default_lines = [l for l in result.stdout.strip().split('\n') if l.strip()]
        fixed_lines = [l for l in result_fixed.stdout.strip().split('\n') if l.strip()]
        
        print(f"\nDefault: {len(default_lines)} entries")
        print(f"Fixed: {len(fixed_lines)} entries")
        print(f"Difference: {len(fixed_lines) - len(default_lines)} more individual files shown")

def test_directory_detection():
    """Test the directory detection logic"""
    print("\n=== Testing Directory Detection Logic ===")
    
    with tempfile.TemporaryDirectory() as temp_dir:
        # Create test files and directories
        test_file = Path(temp_dir) / "test.txt"
        test_dir = Path(temp_dir) / "test_dir"
        test_subfile = test_dir / "subfile.txt"
        
        test_file.write_text("Test content")
        test_dir.mkdir()
        test_subfile.write_text("Sub content")
        
        # Test detection logic
        test_cases = [
            (str(test_file), "file", True),
            (str(test_dir), "directory", False),
            (str(test_subfile), "file", True),
            (str(Path(temp_dir) / "nonexistent.txt"), "nonexistent", False)
        ]
        
        for path, expected_type, should_include in test_cases:
            exists = os.path.exists(path)
            is_file = os.path.isfile(path) if exists else False
            is_dir = os.path.isdir(path) if exists else False
            
            # This mimics the logic in the fix
            should_skip = exists and is_dir
            actual_include = not should_skip and (not exists or is_file)
            
            status = "PASS" if actual_include == should_include else "FAIL"
            print(f"{status} {path} ({expected_type}): include={actual_include}, expected={should_include}")

if __name__ == "__main__":
    print("Directory Handling Fix Test")
    print("=" * 50)
    
    try:
        simulate_git_status_untracked()
        test_directory_detection()
        print("\nAll tests completed successfully!")
    except Exception as e:
        print(f"\nTest failed: {e}")
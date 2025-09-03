#!/usr/bin/env python3

"""
Comprehensive test for git status --porcelain parsing.
Tests the robust regex approach and edge cases.
"""

import re
import sys
from pathlib import Path

def parse_porcelain_line(line):
    """Parse git status --porcelain line robustly with regex"""
    if not line or len(line) < 3:
        return None, None
    
    # Git porcelain format is exactly: XY<space>filename
    # Where X and Y are status characters (can be space)
    status_part = line[:2]
    if len(line) < 3 or line[2] not in [' ', '\t']:  # Must have separator
        return None, None
        
    status = status_part.strip()
    filepath = line[3:]  # Skip the separator
    
    if not filepath:  # Empty filename
        return None, None
    
    # Handle rename/copy cases (R/C status)
    if status and (status[0] in 'RC'):
        # Format: "old -> new"  
        if ' -> ' in filepath:
            old_path, new_path = filepath.split(' -> ', 1)
            # Use the new path (right side)
            filepath = new_path
    
    return status, filepath

def test_porcelain_parsing():
    """Test various git porcelain status formats"""
    
    test_cases = [
        # Standard cases
        ("M  src/app.py", "M", "src/app.py"),
        ("A  src/components/header.js", "A", "src/components/header.js"), 
        (" M lib/utils.py", "M", "lib/utils.py"),
        ("?? new_file.txt", "??", "new_file.txt"),
        ("D  old_file.py", "D", "old_file.py"),
        ("MM src/main.py", "MM", "src/main.py"),
        
        # Files with spaces
        ("M  src/file with spaces.py", "M", "src/file with spaces.py"),
        ("A  \"src/quoted file.js\"", "A", "\"src/quoted file.js\""),
        
        # Rename cases (should use new path)
        ("R  old/name.py -> src/new_name.py", "R", "src/new_name.py"),
        # Note: R100/C50 formats don't actually exist in git porcelain
        # Git uses R or C followed by optional similarity index in extended format
        
        # Copy cases (should use new path)  
        ("C  original.py -> src/copy.py", "C", "src/copy.py"),
        
        # Complex rename with spaces
        ("R  \"old name.txt\" -> \"src/new name.txt\"", "R", "\"src/new name.txt\""),
        
        # Edge cases - these should be handled correctly
        ("   file_at_root.py", "", "file_at_root.py"),  # Weird spacing (3 spaces as status)
        ("M   src/extra_spaces.py", "M", " src/extra_spaces.py"),  # Extra spaces in filename
    ]
    
    print("Git Status Porcelain Parsing Tests")
    print("=" * 60)
    print()
    
    passed = 0
    failed = 0
    
    for i, (line, expected_status, expected_path) in enumerate(test_cases, 1):
        status, filepath = parse_porcelain_line(line)
        
        print(f"Test {i:2d}: {line!r}")
        print(f"         Expected: status='{expected_status}', path='{expected_path}'")
        print(f"         Got:      status='{status}', path='{filepath}'")
        
        if status == expected_status and filepath == expected_path:
            print(f"         [PASS]")
            passed += 1
        else:
            print(f"         [FAIL]")
            failed += 1
        print()
    
    print(f"Results: {passed} passed, {failed} failed")
    return failed == 0

def test_path_reconstruction():
    """Test path reconstruction to catch the rc/src bug"""
    print("\nPath Reconstruction Test")
    print("=" * 40)
    
    # Test the specific case that was failing
    problematic_lines = [
        "M  src/app.py",
        " M src/utils.py", 
        "A  src/components/new.js"
    ]
    
    for line in problematic_lines:
        status, filepath = parse_porcelain_line(line)
        
        print(f"Input:     '{line}'")
        print(f"Status:    '{status}'")
        print(f"Path:      '{filepath}'")
        print(f"First char: '{filepath[0] if filepath else 'EMPTY'}'")
        
        # Simulate path reconstruction
        if filepath:
            repo_root = "/fake/repo"
            abs_path = str(Path(repo_root) / filepath)
            rel_path = Path(abs_path).relative_to(repo_root).as_posix()
            
            print(f"Abs path:  {abs_path}")
            print(f"Rel path:  {rel_path}")
            print(f"Starts with 'src': {rel_path.startswith('src')}")
            
            # The key test: does it preserve the first character?
            if filepath.startswith('src') and not rel_path.startswith('src'):
                print(f"[CRITICAL BUG] Lost first character!")
                return False
            else:
                print(f"[OK] Path preserved correctly")
        
        print()
    
    return True

def test_regex_edge_cases():
    """Test regex edge cases that could break parsing"""
    print("Regex Edge Cases Test")
    print("=" * 30)
    
    edge_cases = [
        # Malformed lines that should return None, None
        ("invalid", None, None),
        ("", None, None),
        ("M", None, None),  # No space or filename
        ("  ", None, None),  # Just spaces
        
        # Valid but minimal - these fail because no space separator
        ("? x", None, None),  # Invalid: no proper separator
        ("MM x", "MM", "x"),  # Valid: proper separator
    ]
    
    all_passed = True
    
    for line, expected_status, expected_path in edge_cases:
        status, filepath = parse_porcelain_line(line)
        
        print(f"Input: {line!r}")
        print(f"Expected: status={expected_status}, path={expected_path}")
        print(f"Got:      status={status}, path={filepath}")
        
        if status == expected_status and filepath == expected_path:
            print("[PASS]")
        else:
            print("[FAIL]")
            all_passed = False
        print()
    
    return all_passed

if __name__ == "__main__":
    print("Running Porcelain Parser Test Suite")
    print("=" * 50)
    
    results = []
    results.append(test_porcelain_parsing())
    results.append(test_path_reconstruction())
    results.append(test_regex_edge_cases())
    
    print("\n" + "=" * 50)
    print("FINAL RESULTS:")
    
    if all(results):
        print("[SUCCESS] ALL TESTS PASSED - Parser is robust!")
        sys.exit(0)
    else:
        print("[ERROR] SOME TESTS FAILED - Parser needs fixes!")
        sys.exit(1)
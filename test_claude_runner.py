#!/usr/bin/env python3
"""
Test script for ClaudeRunner functionality
"""

import sys
import os
sys.path.insert(0, os.path.dirname(__file__))

from components.claude_runner import ClaudeRunner


def test_claude_availability():
    """Test if Claude Code CLI is available"""
    print("Testing Claude Code CLI availability...")
    
    runner = ClaudeRunner()
    
    # Test availability
    is_available = runner.is_claude_available()
    print(f"Claude Code CLI available: {is_available}")
    
    if is_available:
        # Test version
        version = runner.get_claude_version()
        print(f"Claude Code version: {version}")
        
        # Test prompt creation
        test_files = """=== File 1: test.py ===
def hello():
    print("Hello, World!")

=== File 2: README.md ===
# Test Project
This is a test project.
"""
        
        test_prompt = "Analyze this code and suggest improvements."
        
        formatted_prompt = runner.create_session_prompt(test_files, test_prompt)
        print(f"\nFormatted prompt preview (first 200 chars):")
        print(formatted_prompt[:200] + "...")
        
        return True
    else:
        print("Claude Code CLI not found. Please ensure 'claude' command is in PATH.")
        return False


def test_prompt_execution():
    """Test actual prompt execution (if Claude is available)"""
    print("\nTesting prompt execution...")
    
    runner = ClaudeRunner()
    
    if not runner.is_claude_available():
        print("Skipping execution test - Claude not available")
        return False
    
    # Simple test prompt
    test_prompt = "Hello, can you respond with just 'Claude Code is working!' to confirm the integration?"
    
    print("Sending test prompt to Claude...")
    success, result, error = runner.execute_claude_prompt(test_prompt, timeout=30)
    
    if success:
        print("Success!")
        print(f"Response: {result[:200]}...")
        return True
    else:
        print("Failed!")
        print(f"Error: {error}")
        return False


if __name__ == "__main__":
    print("Claude Runner Integration Test")
    print("=" * 50)
    
    # Test availability
    availability_ok = test_claude_availability()
    
    if availability_ok:
        print("\n" + "=" * 50)
        # Test execution (optional)
        user_input = input("Do you want to test actual Claude execution? (y/n): ").lower()
        if user_input in ['y', 'yes']:
            test_prompt_execution()
        else:
            print("Skipping execution test.")
    
    print("\nTest complete!")
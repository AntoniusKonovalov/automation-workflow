#!/usr/bin/env python3
"""
Test script to verify Claude CLI can edit files
Run this to test if your Claude integration is working properly
"""

from components.claude_runner import ClaudeRunner
import os
import sys

def test_claude_editing():
    """Test Claude's ability to edit files"""
    runner = ClaudeRunner()
    
    # Check if Claude is available
    if not runner.is_claude_available():
        print("❌ Claude CLI not found. Please install it first.")
        print("\nTo install Claude CLI:")
        print("1. Install Node.js from https://nodejs.org/")
        print("2. Run: npm install -g @anthropic/claude-cli")
        print("3. Run: claude auth login")
        return False
    
    print(f"✅ Claude CLI found: {runner.get_claude_version()}")
    
    # Check for existing session
    if runner.last_session_id:
        print(f"📝 Using existing session: {runner.last_session_id[:8]}...")
    
    # Create a test prompt that asks Claude to edit test.txt
    test_prompt = """
Please edit the file test.txt and change its content from 'Hello World' to 'Hello from Claude!'.

Use the Edit tool to make this change. The file is in the current directory.
"""
    
    # Execute with editing enabled
    print("\n🔄 Sending edit request to Claude...")
    print("   Mode: Edit mode (file changes enabled)")
    print("   Allowed tools: Read, Edit, Write")
    
    success, result, error = runner.execute_claude_prompt(
        prompt_text=test_prompt,
        working_directory=os.path.dirname(os.path.abspath(__file__)),
        enable_editing=True,  # This enables file editing
        allowed_tools=["Read", "Edit", "Write"],
        resume_session_id=runner.last_session_id  # Use existing session if available
    )
    
    if success:
        print("\n✅ Claude executed successfully!")
        if result:
            print(f"Response: {result[:300]}...")
        else:
            print("(Empty response - likely made file edits)")
        
        # Check if test.txt was actually modified
        test_file = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'test.txt')
        if os.path.exists(test_file):
            with open(test_file, 'r') as f:
                content = f.read().strip()
            print(f"\n📄 Current content of test.txt: '{content}'")
            
            if 'Claude' in content:
                print("✅ File was successfully edited by Claude!")
                return True
            else:
                print("⚠️ File exists but wasn't edited")
                print("   This might mean Claude is running in read-only mode")
        else:
            print("⚠️ test.txt not found")
    else:
        print(f"\n❌ Claude execution failed: {error}")
        if "not found" in error.lower():
            print("\n💡 Tip: Make sure Claude CLI is installed and in your PATH")
        elif "auth" in error.lower():
            print("\n💡 Tip: Run 'claude auth login' to authenticate")
    
    return False

def test_claude_read_only():
    """Test Claude in read-only mode"""
    runner = ClaudeRunner()
    
    print("\n🔍 Testing read-only mode...")
    
    read_prompt = "Please analyze the file test.txt and tell me what it contains."
    
    success, result, error = runner.execute_claude_prompt(
        prompt_text=read_prompt,
        working_directory=os.path.dirname(os.path.abspath(__file__)),
        enable_editing=False,  # Read-only mode
        resume_session_id=runner.last_session_id
    )
    
    if success:
        print("✅ Read-only mode works!")
        print(f"Analysis: {result[:200]}...")
        return True
    else:
        print(f"❌ Read-only mode failed: {error}")
        return False

if __name__ == "__main__":
    print("=" * 60)
    print("Claude File Editing Test")
    print("=" * 60)
    
    # Test editing mode
    edit_success = test_claude_editing()
    
    # Test read-only mode
    read_success = test_claude_read_only()
    
    print("\n" + "=" * 60)
    print("Test Results:")
    print(f"  Edit Mode: {'✅ PASSED' if edit_success else '❌ FAILED'}")
    print(f"  Read Mode: {'✅ PASSED' if read_success else '❌ FAILED'}")
    print("=" * 60)
    
    if not (edit_success or read_success):
        sys.exit(1)
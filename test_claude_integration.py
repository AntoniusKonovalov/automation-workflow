#!/usr/bin/env python3
"""
Comprehensive test script for Claude CLI integration
Tests both read-only and edit modes to ensure everything works correctly
"""

import os
import sys
import time
from components.claude_runner import ClaudeRunner


def print_section(title):
    """Print a formatted section header"""
    print("\n" + "=" * 60)
    print(f"  {title}")
    print("=" * 60)


def test_claude_availability():
    """Test if Claude CLI is available and properly configured"""
    print_section("Testing Claude CLI Availability")
    
    runner = ClaudeRunner()
    
    # Check availability
    if not runner.is_claude_available():
        print("❌ Claude CLI not found!")
        print("\nTo fix this:")
        print("1. Install: npm install -g @anthropic/claude-cli")
        print("2. Authenticate: claude auth login")
        return False
    
    # Get version
    version = runner.get_claude_version()
    print(f"✅ Claude CLI found: {version}")
    
    # Check for existing session
    if runner.last_session_id:
        print(f"📝 Found existing session: {runner.last_session_id[:8]}...")
    else:
        print("📝 No existing session found (will create new)")
    
    return True


def test_read_only_mode():
    """Test Claude in read-only mode (plan mode)"""
    print_section("Testing Read-Only Mode")
    
    runner = ClaudeRunner()
    
    # Create test prompt
    prompt = """
    Please analyze the test.txt file and tell me:
    1. What content it contains
    2. How many characters are in the file
    3. Whether it needs any improvements
    
    Do NOT make any changes, just analyze.
    """
    
    print("📤 Sending read-only analysis request...")
    success, result, error = runner.execute_claude_prompt(
        prompt_text=prompt,
        working_directory=os.path.dirname(os.path.abspath(__file__)),
        enable_editing=False,  # Read-only mode
        timeout=60
    )
    
    if success:
        print("✅ Read-only mode successful!")
        if result:
            print(f"📝 Response preview: {result[:200]}...")
        return True
    else:
        print(f"❌ Read-only mode failed: {error}")
        return False


def test_edit_mode():
    """Test Claude in edit mode (can modify files)"""
    print_section("Testing Edit Mode")
    
    runner = ClaudeRunner()
    
    # Create a test file first
    test_file = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'test_edit.txt')
    with open(test_file, 'w') as f:
        f.write("Original content")
    print(f"📝 Created test file with: 'Original content'")
    
    # Create edit prompt
    prompt = """
    Please edit the file test_edit.txt:
    1. Change the content to: "Modified by Claude CLI"
    2. Use the Edit tool to make this change
    
    Actually make the change, don't just suggest it.
    """
    
    print("📤 Sending edit request...")
    success, result, error = runner.execute_claude_prompt(
        prompt_text=prompt,
        working_directory=os.path.dirname(os.path.abspath(__file__)),
        enable_editing=True,  # Edit mode enabled
        allowed_tools=["Read", "Edit", "Write"],
        timeout=60
    )
    
    if success:
        print("✅ Edit command executed!")
        
        # Check if file was actually modified
        with open(test_file, 'r') as f:
            new_content = f.read()
        
        if "Claude" in new_content:
            print(f"✅ File successfully modified! New content: '{new_content}'")
            return True
        else:
            print(f"⚠️ File unchanged. Content: '{new_content}'")
            print("This might indicate Claude is running in read-only mode despite settings.")
            return False
    else:
        print(f"❌ Edit mode failed: {error}")
        return False


def test_session_continuity():
    """Test if session context is maintained"""
    print_section("Testing Session Continuity")
    
    runner = ClaudeRunner()
    
    # First prompt
    prompt1 = "Remember this number: 42. Just acknowledge you've remembered it."
    print("📤 Sending first prompt...")
    success1, result1, error1 = runner.execute_claude_prompt(
        prompt_text=prompt1,
        working_directory=os.path.dirname(os.path.abspath(__file__)),
        enable_editing=False,
        timeout=30
    )
    
    if not success1:
        print(f"❌ First prompt failed: {error1}")
        return False
    
    print("✅ First prompt sent")
    time.sleep(2)  # Small delay
    
    # Second prompt using session
    prompt2 = "What number did I ask you to remember?"
    print("📤 Sending second prompt (testing context)...")
    success2, result2, error2 = runner.execute_claude_prompt(
        prompt_text=prompt2,
        working_directory=os.path.dirname(os.path.abspath(__file__)),
        enable_editing=False,
        resume_session_id=runner.last_session_id,
        timeout=30
    )
    
    if success2:
        if "42" in str(result2):
            print("✅ Session context maintained! Claude remembered the number.")
            return True
        else:
            print("⚠️ Session context might be lost. Response didn't mention 42.")
            print(f"Response: {result2[:200]}...")
            return False
    else:
        print(f"❌ Second prompt failed: {error2}")
        return False


def main():
    """Run all tests"""
    print("=" * 60)
    print("  Claude CLI Integration Test Suite")
    print("=" * 60)
    
    # Track results
    results = {}
    
    # Test 1: Availability
    results['availability'] = test_claude_availability()
    if not results['availability']:
        print("\n❌ Cannot proceed without Claude CLI")
        sys.exit(1)
    
    # Test 2: Read-only mode
    results['read_only'] = test_read_only_mode()
    
    # Test 3: Edit mode
    results['edit_mode'] = test_edit_mode()
    
    # Test 4: Session continuity
    results['session'] = test_session_continuity()
    
    # Summary
    print_section("Test Results Summary")
    
    for test_name, passed in results.items():
        status = "✅ PASSED" if passed else "❌ FAILED"
        print(f"  {test_name.replace('_', ' ').title()}: {status}")
    
    # Overall result
    all_passed = all(results.values())
    print("\n" + "=" * 60)
    if all_passed:
        print("  🎉 ALL TESTS PASSED! Claude integration is working perfectly.")
    else:
        print("  ⚠️ Some tests failed. Check the output above for details.")
    print("=" * 60)
    
    return 0 if all_passed else 1


if __name__ == "__main__":
    sys.exit(main())
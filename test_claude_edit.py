#!/usr/bin/env python
"""Test script to verify Claude CLI can edit files"""

from components.claude_runner import ClaudeRunner
import os

# Initialize Claude runner
cr = ClaudeRunner()

# Check if Claude is available
if cr.is_claude_available():
    print(f"✅ Claude CLI is available: {cr.get_claude_version()}")
else:
    print("❌ Claude CLI not found")
    exit(1)

# Test directory
test_dir = os.path.dirname(os.path.abspath(__file__))
print(f"Working directory: {test_dir}")

# Create a more specific prompt that Claude will understand
prompt = """Please edit the file test.txt in the current directory to contain the text "Hello from Claude CLI".

The file currently contains "Hello World" and should be changed to "Hello from Claude CLI"."""

print("\nSending prompt to Claude...")
print(f"Prompt: {prompt[:100]}...")

# Execute Claude with editing enabled
success, result, error = cr.execute_claude_prompt(
    prompt_text=prompt,
    working_directory=test_dir,
    enable_editing=True,
    allowed_tools=["Read", "Edit", "Write"]
)

print(f"\n{'='*60}")
print(f"Success: {success}")
if success:
    print(f"Result (first 500 chars):\n{result[:500]}")
else:
    print(f"Error: {error}")

# Check if the file was actually edited
test_file = os.path.join(test_dir, "test.txt")
if os.path.exists(test_file):
    with open(test_file, 'r') as f:
        content = f.read()
    print(f"\n{'='*60}")
    print(f"Current content of test.txt: '{content}'")
    if "Claude" in content:
        print("✅ File was successfully edited by Claude!")
    else:
        print("⚠️ File exists but wasn't edited")
else:
    print("❌ test.txt doesn't exist")
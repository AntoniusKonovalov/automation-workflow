# Testing Guide for Git Workflow Automator

## Quick Start

Run the comprehensive test suite:
```bash
python test_claude_integration.py
```

This will test:
1. ✅ Claude CLI availability
2. ✅ Read-only mode (analysis without edits)
3. ✅ Edit mode (actual file modifications)
4. ✅ Session continuity (context preservation)

## What Each Test Does

### 1. **Availability Test**
- Checks if Claude CLI is installed
- Verifies authentication
- Shows version information
- Loads any existing session

### 2. **Read-Only Mode Test**
- Tests Claude in "plan" mode
- Ensures no files are modified
- Verifies analysis capabilities

### 3. **Edit Mode Test**
- Creates a test file
- Asks Claude to modify it
- Verifies the modification happened
- Confirms edit capabilities are working

### 4. **Session Continuity Test**
- Sends two related prompts
- Verifies Claude remembers context
- Tests session persistence

## Troubleshooting

### Claude CLI Not Found
```bash
# Install Claude CLI
npm install -g @anthropic/claude-cli

# Authenticate
claude auth login
```

### Edit Mode Not Working
1. Check `.claude/settings.local.json` has `"defaultMode": "acceptEdits"`
2. Ensure allowed tools include: `Read`, `Edit`, `Write`
3. Verify you're not using `-p` flag for edit operations

### Session Not Persisting
1. Check `~/.claude_workflow_sessions.json` exists
2. Verify write permissions to home directory
3. Look for session ID in debug output

## Manual Testing

### Test File Editing
```bash
# Create test file
echo "Hello World" > test.txt

# Run your app and send this to Claude:
"Edit test.txt and change 'Hello World' to 'Hello Claude'"

# Check if file was modified
cat test.txt
```

### Test Session Context
```bash
# First prompt
"Remember the color blue"

# Second prompt (should remember)
"What color did I mention?"
```

## Integration with Main App

The app uses Claude in two modes:

1. **Analysis Mode** (`enable_editing=False`)
   - Used for code review
   - No file modifications
   - Uses `-p` flag

2. **Edit Mode** (`enable_editing=True`)
   - Used when "Send to Agent" is clicked
   - Can modify files
   - No `-p` flag
   - Uses `--permission-mode acceptEdits`

## Expected Behavior

✅ **Working Correctly:**
- Claude responds to prompts
- Files are modified in edit mode
- Session context is maintained
- No permission prompts in headless mode

❌ **Issues to Fix:**
- Claude not found → Install CLI
- Auth errors → Run `claude auth login`
- No edits happening → Check permission settings
- Context lost → Check session persistence
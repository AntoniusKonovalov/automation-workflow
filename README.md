# Git Workflow Automator

A sophisticated desktop application that automates Git workflow tasks with AI-powered code analysis using ChatGPT and Claude Code CLI.

## Features

### Core Functionality
- **Git Integration**: Automatically detects and displays changed files in your Git repository
- **AI Analysis**: Integrates with OpenAI GPT models for code analysis and recommendations
- **Claude Code CLI**: Headless execution of Claude for automated code editing and improvements
- **Session Management**: Maintains conversation context across multiple interactions
- **File Preview**: View and select specific files for analysis

### UI Components
- **Modern Dark Theme**: Professional dark mode interface with custom styling
- **Collapsible Panels**: Efficient screen space usage with expandable sections
- **Chat History**: Track and revisit previous analysis sessions
- **Token Counter**: Monitor API usage with visual indicators
- **Custom Title Bar**: Draggable window with minimize/maximize/close controls

## Installation

### Prerequisites
1. Python 3.8+
2. Node.js and npm (for Claude CLI)
3. Git

### Setup Steps

1. Clone the repository:
```bash
git clone <repository-url>
cd automation-workflow
```

2. Install Python dependencies:
```bash
pip install -r requirements.txt
```

3. Install Claude Code CLI:
```bash
npm install -g @anthropic-ai/claude-cli
claude auth login
```

4. Create `.env` file with your API keys:
```env
OPENAI_API_KEY=your_openai_api_key_here
ANTHROPIC_API_KEY=your_anthropic_api_key_here
```

## Usage

### Starting the Application
```bash
python main.py
```

### Basic Workflow
1. **Select Project**: Browse to your Git repository or let the app auto-detect it
2. **View Changes**: Click the sidebar toggle to see changed files
3. **Select Files**: Choose files for analysis using checkboxes
4. **AI Analysis**: Enter a prompt and click "Send to AI" for analysis
5. **Claude Integration**: Use "Send to Agent" to execute code changes via Claude

### Claude Code Features
- **Fresh Sessions**: Default behavior - each prompt starts a new context
- **Continue Session**: Check the box to maintain conversation context
- **File Editing**: Claude can directly modify your code files
- **Safe Defaults**: Permission controls prevent unauthorized changes

## Project Structure

```
automation-workflow/
├── main.py                     # Main application entry point
├── components/
│   ├── __init__.py            # Component exports
│   ├── api_client.py          # OpenAI API integration
│   ├── claude_runner.py       # Claude CLI integration
│   ├── chat_history_manager.py # Session persistence
│   ├── file_manager.py        # File operations
│   ├── git_manager.py         # Git operations
│   ├── theme_manager.py       # UI theming
│   ├── ui_utils.py           # UI utilities
│   └── ui/
│       ├── analysis_panel.py  # AI analysis UI
│       └── file_list_panel.py # File listing UI
├── .claude/
│   └── settings.local.json    # Claude permissions
├── requirements.txt           # Python dependencies
├── package.json              # Node dependencies
└── .env                      # API keys (create this)
```

## Configuration

### Claude Permissions (.claude/settings.local.json)
The app includes safe defaults for Claude operations:
- Allows: Read, Edit, Write, MultiEdit
- Denies: Access to .env files and secrets
- Default mode: acceptEdits (can modify files)

### Available GPT Models
- GPT-5 (Latest)
- GPT-5 Mini
- GPT-4.1
- GPT-4o
- GPT-4o Mini

## Troubleshooting

### Claude CLI Not Found
- Ensure Claude is installed: `npm install -g @anthropic-ai/claude-cli`
- Verify installation: `claude --version`
- Authenticate: `claude auth login`

### API Key Issues
- Check `.env` file exists and contains valid keys
- Verify key format (no quotes needed)
- Ensure sufficient API credits

### Session Persistence
- Sessions are saved in `~/.claude_workflow_sessions.json`
- Project-specific history in `<project>/.appdata/chat_history.json`

## Security Considerations

- API keys are stored locally in `.env` (never committed)
- Claude permissions prevent access to sensitive files
- Atomic writes prevent session corruption
- Thread-safe session management

## Contributing

Feel free to submit issues and enhancement requests!

## License

[Your License Here]

## Acknowledgments

- Built with Tkinter for cross-platform compatibility
- Powered by OpenAI GPT and Anthropic Claude
- Git integration via subprocess
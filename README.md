# Evolving Assistant

Evolving Assistant is a self-modifying AI designed to dynamically adapt to user input by creating, executing, and managing commands. It leverages GPT-based models to classify user requests, generate new commands, and respond intelligently. The assistant is optimized for cross-platform compatibility (Windows, macOS, Linux) and provides a user-friendly GUI for interaction.

## Features

- **Dynamic Command Creation**: Automatically generates Python functions for user requests if a command doesn't already exist.
- **Command Execution**: Executes pre-existing or newly created commands stored in the `commands` folder.
- **OS Detection**: Detects the operating system and optimizes commands accordingly.
- **Conversation History**: Maintains a log of user interactions for context-aware responses.
- **API Integration**: Supports APIs like Spotify, with step-by-step setup instructions for credentials.
- **Error Handling**: Provides meaningful error messages and fallback implementations for common commands.

## Requirements

- Python 3.8 or higher
- Required Python libraries:
  - `g4f` ([GPT4Free](https://github.com/xtekky/gpt4free) xTekky)
  - `asyncio`
  - `platform`
  - `logging`

## Installation

1. Clone the repository:
   ```bash
   git clone https://github.com/your-username/evolving-assistant.git
   cd evolving-assistant

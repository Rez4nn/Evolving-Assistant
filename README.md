# Evolving Assistant

Evolving Assistant is a self-modifying AI assistant designed to dynamically adapt to user input by creating and executing commands. It uses GPT-based models to classify user requests, generate new commands, and respond intelligently. The assistant is optimized to work across different operating systems (Windows, Linux, macOS).

## Features

- **Dynamic Command Creation**: Automatically generates Python functions for user requests if a command doesn't already exist.
- **Command Execution**: Executes pre-existing or newly created commands stored in the `commands` folder.
- **OS Detection**: Detects the operating system (Windows, Linux, macOS) and optimizes commands accordingly.
- **Conversation History**: Maintains a log of user interactions for context-aware responses.
- **Error Handling**: Provides fallback implementations for common commands if GPT-based generation fails.
- **Customizable Configuration**: Allows customization of AI behavior, personality, and API integrations via a configuration file.

## Requirements

- Python 3.8 or higher
- Required Python libraries:
  - `g4f` ([GPT4Free](https://github.com/xtekky/gpt4free) Concept client xTekky)
  - `asyncio`
  - `platform`
  - `logging`

## Installation

1. Clone the repository:
   ```bash
   git clone https://github.com/your-username/evolving-assistant.git
   cd evolving-assistant

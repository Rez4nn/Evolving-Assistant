## File: README.md
# Evolving AI Assistant

## Overview
The **Evolving AI Assistant** is a self-adapting chatbot powered by xTekky's [GPT4Free](https://github.com/xtekky/gpt4free) (proof of concept, recommend you use the official OpenAI API. It can execute code, remember user preferences, and refine its own responses over time. It features a GUI for interaction and allows users to approve AI-generated code before execution.

## Features
- **Self-Editing AI**: The assistant refines its code dynamically.
- **Command vs. Conversation Mode**: Determines if input is a command (executes Python) or a chat (responds naturally).
- **Memory System**: Learns user preferences.
- **Code Execution Sandbox**: AI-generated Python code is reviewed before execution.
- **GUI-Based Interface**: Users can interact with the assistant and approve edits.

---

## Installation
### Prerequisites
- Python 3.8+
- `pip install -r requirements.txt`

### Run the Assistant
```sh
python main.py
```

---

## File Structure Plan:
```
evolving_ai/
│── main.py                # Main application loop
│── config.py              # Config settings
│── ai_engine.py           # GPT4Free integration
│── memory.py              # User memory system
│── code_executor.py       # Executes AI-generated Python code safely
│── self_editing.py        # Self-editing logic for AI improvements
│── gui.py                 # Tkinter GUI for interaction
│── utils.py               # Helper functions
│── data/
│   ├── memory.json        # Stores user preferences & conversation history
│   ├── pending_edits.json # AI-generated code pending review
│── tests/
│   ├── test_ai.py         # Unit tests for AI engine
│   ├── test_executor.py   # Unit tests for code execution
└── requirements.txt        # Python dependencies
```

---

## Development Plans:
### AI Engine
- Uses xTekky's [GPT4Free](https://github.com/xtekky/gpt4free) for response generation (recommended you use the official OpenAI API).
- Categorizes input into commands or chat.

### Memory System
- Stores user preferences and chat history.
- Adapts responses based on past interactions.

### Self-Editing Mechanism
- AI reviews its own output and suggests improvements.
- Pending code changes are stored in `pending_edits.json`.

### GUI
- Tkinter-based interface.
- Users can chat, approve AI edits, and review execution results.

---

## Future Enhancements
- **Voice Integration**: Add speech input/output.
- **Web API Access**: Connect to external data sources.
- **Multi-User Profiles**: Store preferences per user.

---

## License
MIT License - Feel free to modify and expand!

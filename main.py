import os
import re
import json  # Added for configuration handling
from g4f.client import Client
from collections import deque
import warnings
import asyncio
import platform

# Suppress the specific RuntimeWarning related to Proactor event loop
warnings.filterwarnings("ignore", message="Proactor event loop does not implement add_reader")
# Set the event loop policy to avoid the warning
asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())

COMMANDS_FOLDER = "commands"
CONFIG_FILE = "config.json"  # Configuration file for AI settings

class SelfModifyingAI:
    def __init__(self):
        self.client = Client()
        self.commands = {}  # category -> {command name -> function}
        self.os_info = self.detect_os()  # Detect and store OS information
        self.ensure_commands_folder()
        self.load_config()  # Load AI configuration
        self.load_commands()
        self.conversation_history = deque(maxlen=10)  # Keep last 10 messages
    
    def ensure_commands_folder(self):
        if not os.path.exists(COMMANDS_FOLDER):
            os.makedirs(COMMANDS_FOLDER)
    
    def load_config(self):
        """
        Load AI configuration from the config file. If the file doesn't exist, create a default one.
        """
        if not os.path.exists(CONFIG_FILE):
            default_config = {
                "ai_name": "Assistant",
                "behavior": "helpful and friendly",
                "personality": "curious and engaging"
            }
            with open(CONFIG_FILE, "w", encoding="utf-8") as f:
                json.dump(default_config, f, indent=4)
        with open(CONFIG_FILE, "r", encoding="utf-8") as f:
            self.config = json.load(f)
    
    def load_commands(self):
        self.commands = {}
        for category in os.listdir(COMMANDS_FOLDER):
            category_path = os.path.join(COMMANDS_FOLDER, category)
            if os.path.isdir(category_path):
                self.commands[category] = {}
                for fname in os.listdir(category_path):
                    if fname.endswith(".py"):
                        command_name = fname[:-3]  # remove .py extension
                        fpath = os.path.join(category_path, fname)
                        try:
                            with open(fpath, "r", encoding="utf-8") as f:
                                code = f.read()
                            ns = {}
                            exec(code, ns)
                            if command_name in ns and callable(ns[command_name]):
                                self.commands[category][command_name] = ns[command_name]
                        except Exception as e:
                            print(f"Error loading command {command_name} in category {category}: {e}")
    
    def sanitize_command_name(self, text):
        return re.sub(r'[^a-z0-9_]', '', text.lower().replace(" ", "_"))
    
    def classify_and_suggest(self, text):
        """
        Analyze the user input and determine if it is a conversation or command request.
        If you don't know something like the time, date, weather, etc., then it is a command.
        Return either, "command" or "conversation"
        """
        # Check if the input matches an existing command
        sanitized_name = self.sanitize_command_name(text)
        for category, commands in self.commands.items():
            if sanitized_name in commands:
                return category, sanitized_name

        # Check for real-time-related or action-related keywords to classify as a command
        real_time_keywords = ["time", "date", "weather", "temperature"]
        action_keywords = ["open", "launch", "start"]
        for keyword in real_time_keywords:
            if keyword in text.lower():
                return "utilities", self.sanitize_command_name(f"tell_the_{keyword}")
        for keyword in action_keywords:
            if keyword in text.lower():
                action_object = text.lower().replace(keyword, "").strip()
                return "actions", self.sanitize_command_name(f"{keyword}_{action_object}")

        # If no match, proceed with GPT classification
        prompt = (f"Analyze the following user input: '{text}'\n"
                "If this is a command request (e.g., for retrieving time, date, weather, opening applications, etc.), "
                "suggest an appropriate command name and category in lowercase with underscores (e.g., category: utilities, command: tell_the_time; "
                "category: actions, command: open_spotify). "
                "If it is general conversation, respond with 'conversation'.")
        try:
            response = self.client.chat.completions.create(
                model="gpt-4o-mini",
                messages=[{"role": "user", "content": prompt}],
                web_search=False
            )
            result = response.choices[0].message.content.strip().lower()
            if result == "conversation":
                return "conversation", None
            # Ensure proper parsing of category and command
            if ":" in result:
                category, command_name = result.split(":", 1)
                return category.strip(), command_name.strip()
            else:
                return "conversation", None
        except Exception:
            return "conversation", None  # Default to conversation if GPT call fails
        
    def detect_os(self):
        system = platform.system()

    def create_command(self, category, command_name, user_input):
        category_folder = os.path.join(COMMANDS_FOLDER, category)
        if not os.path.exists(category_folder):
            os.makedirs(category_folder)
        
        target_file = os.path.join(category_folder, f"{command_name}.py")
        if os.path.exists(target_file):
            print(f"Command '{command_name}' already exists in category '{category}'. Using existing command.")
            return

        # Include OS information in the prompt for command creation
        prompt = (f"Create a Python function named '{command_name}' based on the following request: '{user_input}'.\n"
                  f"The current operating system is '{self.os_info}'. Optimize the function for this OS if relevant and make it universal.\n"
                  "Ensure valid Python syntax and that the function returns a string result. "
                  "Examples: If the request is to tell the time, create a function that returns the current time.\n"
                  "Examples: If the request is to open an application (e.g., Spotify), create a function that launches the application using the appropriate system command.\n"
                  "Examples: If an API is needed, provide a basic implementation to retrieve the required information.\n"
                  "Make sure to include any necessary imports and handle exceptions if needed and file directories should be dynamic, not hardcoded.\n"
                  "Do not include any explanations; only return the valid code.")
        try:
            response = self.client.chat.completions.create(
                model="gpt-4o-mini",
                messages=[{"role": "user", "content": prompt}],
                web_search=False
            )
            new_code_segment = response.choices[0].message.content.strip()
            if '```' in new_code_segment:
                parts = new_code_segment.split('```')
                new_code_segment = next((part.replace('python', '').strip() for part in parts if 'def ' in part), new_code_segment)
            with open(target_file, "w", encoding="utf-8") as f:
                f.write(new_code_segment)
            print(f"Command '{command_name}' has been created in category '{category}'.")
            self.load_commands()
        except Exception as e:
            print(f"Failed to create command '{command_name}': {e}")
            # Fallback: Create basic functions for common commands if GPT fails
            if command_name == "tell_the_time":
                fallback_code = (
                    "def tell_the_time():\n"
                    "    from datetime import datetime\n"
                    "    return datetime.now().strftime('%Y-%m-%d %H:%M:%S')\n"
                )
            elif command_name == "open_spotify":
                fallback_code = (
                    "def open_spotify():\n"
                    "    import os\n"
                    "    os.system('spotify')\n"
                    "    return 'Spotify has been opened.'\n"
                )
            else:
                fallback_code = f"def {command_name}():\n    return 'Fallback: Command not implemented.'\n"
            with open(target_file, "w", encoding="utf-8") as f:
                f.write(fallback_code)
            print(f"Fallback: Command '{command_name}' has been created in category '{category}'.")
            self.load_commands()

    def execute_command(self, category, command, *args):
        if category in self.commands and command in self.commands[category]:
            try:
                return self.commands[category][command](*args)
            except Exception as e:
                return f"Error executing command '{command}' in category '{category}': {e}"
        else:
            # Fallback: Handle "tell the time" directly if the command is missing
            if command == "tell_the_time":
                from datetime import datetime
                return datetime.now().strftime('%Y-%m-%d %H:%M:%S')
            return f"Unknown command: {command} in category: {category}"
    
    def combine_results(self, command_output, user_input):
        """
        3rd GPT call: Generate a final response based on user input and command output.
        Uses conversation history for context.
        """
        history_text = "\n".join(self.conversation_history)
        prompt = (f"Conversation History:\n{history_text}\n"
                  f"User input: {user_input}\n"
                  f"Command output: {command_output}\n"
                  f"AI Name: {self.config['ai_name']}\n"
                  f"AI Behavior: {self.config['behavior']}\n"
                  f"AI Personality: {self.config['personality']}\n"
                  "Generate a final response to the user based on this information.")
        
        response = self.client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[{"role": "user", "content": prompt}],
            web_search=False
        )
        return response.choices[0].message.content.strip()
    
    def evolve(self, user_input):
        if not user_input.strip():
            print("No input given. Evolution cancelled.")
            return
        
        self.conversation_history.append(f"User: {user_input}")
        category, decision = self.classify_and_suggest(user_input)
        
        if category == "conversation":
            final_response = self.combine_results("", user_input)
        else:
            command_name = self.sanitize_command_name(decision)
            if category not in self.commands or command_name not in self.commands[category]:
                self.create_command(category, command_name, user_input)
            command_output = self.execute_command(category, command_name)
            final_response = self.combine_results(command_output, user_input)
        
        self.conversation_history.append(f"AI: {final_response}")
        print(f"{self.config['ai_name']} Response:", final_response)

if __name__ == "__main__":
    ai = SelfModifyingAI()
    while True:
        user_input = input(f"{ai.config['ai_name']}: Enter a command or request: ")
        ai.evolve(user_input)

import os
import re
import json  # Added for configuration handling
from g4f.client import Client
from collections import deque
import warnings
import asyncio
import platform
import logging  # Added for conversation history logging
import time  # Added for timeout handling
from difflib import SequenceMatcher  # Added for similarity checking

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
        self.setup_logging()  # Setup logging for infinite conversation history

    def setup_logging(self):
        """
        Setup logging to store infinite conversation history in a log file.
        """
        self.log_file = "conversation_history.log"
        logging.basicConfig(
            filename=self.log_file,
            level=logging.INFO,
            format="%(asctime)s - %(message)s",
            datefmt="%Y-%m-%d %H:%M:%S"
        )
        logging.info(f"{self.config['ai_name']} initialized.")

    def ensure_commands_folder(self):
        """
        Ensure the commands folder exists.
        """
        commands_folder_path = os.path.join(os.getcwd(), COMMANDS_FOLDER)
        if not os.path.exists(commands_folder_path):
            os.makedirs(commands_folder_path)
    
    def load_config(self):
        """
        Load AI configuration from the config file. If the file doesn't exist, create a default one.
        """
        config_path = os.path.join(os.getcwd(), CONFIG_FILE)
        if not os.path.exists(config_path):
            default_config = {
                "ai_name": "Assistant",
                "behavior": "helpful and friendly",
                "personality": "curious and engaging",
                "apis": {}
            }
            with open(config_path, "w", encoding="utf-8") as f:
                json.dump(default_config, f, indent=4)
        with open(config_path, "r", encoding="utf-8") as f:
            self.config = json.load(f)

    def update_config_with_api(self, api_name, api_details):
        """
        Update the configuration file with API details.
        """
        if "apis" not in self.config:
            self.config["apis"] = {}
        self.config["apis"][api_name] = api_details
        with open(CONFIG_FILE, "w", encoding="utf-8") as f:
            json.dump(self.config, f, indent=4)
        print(f"API '{api_name}' has been added to the configuration.")
    
    def load_commands(self):
        """
        Load all commands from the commands folder.
        """
        commands_folder_path = os.path.join(os.getcwd(), COMMANDS_FOLDER)
        self.commands = {}
        for category in os.listdir(commands_folder_path):
            category_path = os.path.join(commands_folder_path, category)
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
                                self.commands[category][command_name] = {
                                    "function": ns[command_name],
                                    "code": code  # Store the code for comparison
                                }
                        except Exception as e:
                            print(f"Error loading command {command_name} in category {category}: {e}")
    
    def sanitize_command_name(self, text):
        return re.sub(r'[^a-z0-9_]', '', text.lower().replace(" ", "_"))
    
    def classify_and_suggest(self, text):
        """
        Analyze the user input and determine if it is a conversation or command request.
        If it's a command request, suggest an appropriate command name and category.
        """
        # Check if the input matches an existing command
        sanitized_name = self.sanitize_command_name(text)
        for category, commands in self.commands.items():
            if sanitized_name in commands:
                return category, sanitized_name

        # Check for real-time-related or action-related keywords to classify as a command
        real_time_keywords = ["time", "date", "weather", "temperature"]
        action_keywords = ["open", "launch", "start", "resume", "play", "stop", "pause"]
        for keyword in real_time_keywords:
            if keyword in text.lower():
                return "utilities", self.sanitize_command_name(f"tell_the_{keyword}")
        for keyword in action_keywords:
            if keyword in text.lower():
                action_object = text.lower().replace(keyword, "").strip()
                return "actions", self.sanitize_command_name(f"{keyword}_{action_object}")

        # If no match, proceed with GPT classification
        prompt = (f"Summarize the following user input: '{text}'\n"
                  "Determine if it is a command request (e.g., retrieving time, date, weather, controlling applications, etc.) "
                  "or general conversation. If it is a command request, suggest a concise command name and category in lowercase "
                  "with underscores (e.g., category: utilities, command: tell_the_time; category: actions, command: resume_music). "
                  "If it is general conversation, respond with 'conversation'.")
        try:
            response = self.client.chat.completions.create(
                model="gpt-4o-mini",
                messages=[{"role": "user", "content": prompt}],
                web_search=False,
                timeout=10  # Prevent hanging
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
        except Exception as e:
            print(f"Error during GPT classification: {e}")
            return "conversation", None  # Default to conversation if GPT call fails

    def detect_os(self):
        system = platform.system()

    def find_similar_command(self, category, command_name, user_input):
        """
        Check if a similar command already exists in the specified category.
        If a similar command is found, return its name; otherwise, return None.
        """
        if category in self.commands:
            for existing_command, details in self.commands[category].items():
                # Compare the user input with the existing command's name and code
                name_similarity = SequenceMatcher(None, command_name, existing_command).ratio()
                input_similarity = SequenceMatcher(None, user_input, details["code"]).ratio()

                # Adjusted similarity threshold to reduce false positives
                if name_similarity > 0.9 or input_similarity > 0.9:
                    print(f"Found similar command '{existing_command}' in category '{category}'. Reusing it.")
                    return existing_command
        return None

    def sanitize_path_component(self, text):
        """
        Sanitize a string to make it safe for use as a file or directory name.
        """
        return re.sub(r'[<>:"/\\|?*]', '', text)

    def create_command(self, category, command_name, user_input):
        """
        Create a new command dynamically based on the user's input.
        If a similar command already exists, reuse it.
        """
        # Sanitize category and command_name
        category = self.sanitize_path_component(category)
        command_name = self.sanitize_path_component(command_name)

        commands_folder_path = os.path.join(os.getcwd(), COMMANDS_FOLDER)
        category_folder = os.path.join(commands_folder_path, category)
        if not os.path.exists(category_folder):
            os.makedirs(category_folder)

        # Check for similar commands
        similar_command = self.find_similar_command(category, command_name, user_input)
        if similar_command:
            return similar_command  # Reuse the similar command

        target_file = os.path.join(category_folder, f"{command_name}.py")
        if os.path.exists(target_file):
            print(f"Command '{command_name}' already exists in category '{category}'. Using existing command.")
            return command_name

        # Enhanced GPT prompt for dynamic command creation with configuration variables
        prompt = (f"Create a Python function named '{command_name}' based on the following request: '{user_input}'.\n"
                  f"The current operating system is '{self.os_info}'. Optimize the function for this OS and make it universal where possible.\n"
                  "Ensure valid Python syntax and that the function returns a string result.\n"
                  "At the top of the file, include a section for variables that can be edited by the user to configure the function.\n"
                  "For example, include variables for API keys, endpoints, or other configurable parameters.\n"
                  "The function must:\n"
                  "- Use the variables defined at the top of the file for configuration.\n"
                  "- Include proper error handling for any external calls or operations.\n"
                  "- Provide meaningful error messages to the user if something goes wrong.\n"
                  "- Avoid hardcoding sensitive information like API keys or tokens and avoid them if you can.\n"
                  "Handle platform-specific commands for Windows, macOS, and Linux first, use APIs as a fallback.\n"
                  "Avoid hardcoding file paths; use dynamic paths to ensure compatibility across different environments.\n"
                  "Do not include any explanations; only return the valid code.")
        try:
            response = self.client.chat.completions.create(
                model="gpt-4o-mini",
                messages=[{"role": "user", "content": prompt}],
                web_search=True
            )
            new_code_segment = response.choices[0].message.content.strip()
            if '```' in new_code_segment:
                parts = new_code_segment.split('```')
                new_code_segment = next((part.replace('python', '').strip() for part in parts if 'def ' in part), new_code_segment)

            # Write the new command to a file
            with open(target_file, "w", encoding="utf-8") as f:
                f.write(new_code_segment)
            print(f"Command '{command_name}' has been created in category '{category}'.")
            self.load_commands()
        except Exception as e:
            print(f"Failed to create command '{command_name}': {e}")

        return command_name

    def execute_command(self, category, command, *args):
        """
        Execute a command from the specified category.
        If the command is missing, return an appropriate error message.
        """
        if category in self.commands and command in self.commands[category]:
            try:
                print(f"Executing command '{command}' in category '{category}'...")
                start_time = time.time()
                result = self.commands[category][command]["function"](*args)
                elapsed_time = time.time() - start_time
                if elapsed_time > 10:  # Timeout threshold for execution
                    print(f"Warning: Command '{command}' took too long to execute ({elapsed_time:.2f} seconds).")
                return result
            except Exception as e:
                return f"Error executing command '{command}' in category '{category}': {e}"
        else:
            return f"Unknown command: {command} in category: {category}"
    
    def combine_results(self, command_output, user_input):
        """
        Generate a concise response based on user input and command output.
        Retain only important conversation history, excluding command executions but keeping command creation.
        """
        # Read the conversation history from the log file
        try:
            with open(self.log_file, "r", encoding="utf-8", errors="replace") as log:
                history_lines = log.readlines()
                # Filter history to retain only important entries (e.g., command creation)
                filtered_history = [line for line in history_lines if "created command" in line.lower()]
                history_text = "".join(filtered_history)
        except FileNotFoundError:
            history_text = "No previous conversation history available."

        prompt = (f"Be concise and keep your response short.\n"
                  f"Conversation History:\n{history_text}\n"
                  f"User input: {user_input}\n"
                  f"Command output: {command_output}\n"
                  f"AI Name: {self.config['ai_name']}\n"
                  f"AI Behavior: {self.config['behavior']}\n"
                  f"AI Personality: {self.config['personality']}\n"
                  "Generate a concise and summarized response to the user based on this information.")
        
        response = self.client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[{"role": "user", "content": prompt}],
            web_search=False
        )
        return response.choices[0].message.content.strip()
    
    def evolve(self, user_input):
        if not user_input.strip():
            logging.info("No input given. Evolution cancelled.")
            return "No input given. Please try again."
        
        logging.info(f"User: {user_input}")  # Log user input
        category, decision = self.classify_and_suggest(user_input)
        
        if category == "conversation":
            if "your name" in user_input.lower():
                final_response = f"My name is {self.config['ai_name']}."
            else:
                final_response = self.combine_results("", user_input)
        else:
            command_name = self.sanitize_command_name(decision)
            if category not in self.commands or command_name not in self.commands[category]:
                self.create_command(category, command_name, user_input)
                logging.info(f"Created command: {command_name} in category: {category}")  # Log command creation
            command_output = self.execute_command(category, command_name)
            final_response = self.combine_results(command_output, user_input)
        
        logging.info(f"AI: {final_response}")  # Log AI response
        return final_response  # Ensure the response is returned for GUI

if __name__ == "__main__":
    from gui import run_gui  # Import the GUI function

    ai = SelfModifyingAI()
    run_gui(ai)  # Launch the GUI

import tkinter as tk
from tkinter import scrolledtext

def run_gui(ai):
    """
    Launch the GUI for interacting with the AI.
    """
    def send_input():
        user_input = user_entry.get()
        if user_input.strip():
            conversation_log.insert(tk.END, f"You: {user_input}\n")
            ai_response = ai.evolve(user_input)  # Get the response from evolve
            if ai_response:
                conversation_log.insert(tk.END, f"{ai.config['ai_name']}: {ai_response}\n")
            else:
                conversation_log.insert(tk.END, f"{ai.config['ai_name']}: Sorry, I couldn't process that.\n")
            user_entry.delete(0, tk.END)
        else:
            conversation_log.insert(tk.END, "Please enter a valid input.\n")

    # Create the main window
    root = tk.Tk()
    root.title(f"{ai.config['ai_name']} - Chat")

    # Conversation log
    conversation_log = scrolledtext.ScrolledText(root, wrap=tk.WORD, width=50, height=20, state=tk.NORMAL)
    conversation_log.pack(padx=10, pady=10)
    conversation_log.insert(tk.END, f"{ai.config['ai_name']} is ready to chat!\n")

    # User input entry
    user_entry = tk.Entry(root, width=40)
    user_entry.pack(padx=10, pady=5)

    # Send button
    send_button = tk.Button(root, text="Send", command=send_input)
    send_button.pack(pady=5)

    # Start the GUI event loop
    root.mainloop()

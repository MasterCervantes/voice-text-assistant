import tkinter as tk
from tkinter import ttk, messagebox, simpledialog, filedialog
import requests
import threading
import json
import os
import subprocess
import platform
import pyttsx3
import logging
import traceback
from queue import Queue
from functools import partial
from voice_manager import VoiceManager

# Configure logging
logging.basicConfig(
    level=logging.DEBUG,
    format='%(asctime)s - %(levelname)s - %(message)s',
    filename='voice_assistant.log'
)

class OllamaChecker:
    @staticmethod
    def is_installed():
        try:
            check_cmd = ['where', 'ollama'] if platform.system() == "Windows" else ['which', 'ollama']
            return subprocess.run(check_cmd, capture_output=True).returncode == 0
        except Exception:
            return False

    @staticmethod
    def is_running():
        try:
            return requests.get("http://localhost:11434/api/tags", timeout=5).status_code == 200
        except requests.exceptions.RequestException:
            return False
    
    @staticmethod
    def get_available_models():
        try:
            response = requests.get("http://localhost:11434/api/tags", timeout=5)
            if response.status_code == 200 and 'models' in response.json():
                return [model['name'] for model in response.json()['models']]
            return []
        except requests.exceptions.RequestException:
            return []

class VoiceTextAssistant:
    def __init__(self, root):
        try:
            logging.info("Initializing VoiceTextAssistant")
            self.root = root
            self.root.title("Voice-Enabled Ollama Chat")
            self.root.geometry("800x600")
            self.root.minsize(600, 400)
            
            # Initialize voice manager
            logging.info("Initializing voice manager")
            self.voice_manager = VoiceManager()
            
            self.message_queue = Queue()
            self.current_conversation = None
            self.conversation = []
            self.displayed_message_indices = []
            self.save_folder = "conversations"
            self.settings = {}  # Initialize settings dictionary
            
            logging.info("Setting up UI")
            self.setup_ui()
            self.setup_bindings()
            self.load_data()
            self.check_ollama_status()
            self.process_messages()
            logging.info("Initialization complete")
        except Exception as e:
            logging.error(f"Error during initialization: {str(e)}")
            logging.error(traceback.format_exc())
            messagebox.showerror("Initialization Error", f"Error initializing application: {str(e)}")
            raise

    def setup_ui(self):
        try:
            logging.info("Setting up UI components")
            self.create_menu()
            self.create_chat_interface()
            self.create_status_bar()
            self.create_voice_controls()
        except Exception as e:
            logging.error(f"Error in setup_ui: {str(e)}")
            logging.error(traceback.format_exc())
            raise
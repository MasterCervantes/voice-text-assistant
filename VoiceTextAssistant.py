import tkinter as tk
from tkinter import ttk, messagebox, simpledialog, filedialog
import requests
import threading
import json
import os
import subprocess
import platform
import pyttsx3
from queue import Queue
from functools import partial
from voice_manager import VoiceManager

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
        self.root = root
        self.root.title("Voice-Enabled Ollama Chat")
        self.root.geometry("800x600")
        self.root.minsize(600, 400)
        
        # Initialize voice manager
        self.voice_manager = VoiceManager()
        
        self.message_queue = Queue()
        self.current_conversation = None
        self.conversation = []
        self.displayed_message_indices = []
        self.save_folder = "conversations"
        
        self.setup_ui()
        self.setup_bindings()
        self.load_data()
        self.check_ollama_status()
        self.process_messages()

    def setup_ui(self):
        self.create_menu()
        self.create_chat_interface()
        self.create_status_bar()
        self.create_voice_controls()

    def create_voice_controls(self):
        voice_frame = ttk.LabelFrame(self.root, text="Voice Controls")
        voice_frame.pack(fill=tk.X, padx=5, pady=2)

        # Voice selection
        ttk.Label(voice_frame, text="Voice:").pack(side=tk.LEFT, padx=5)
        self.voice_var = tk.StringVar()
        self.voice_combo = ttk.Combobox(
            voice_frame,
            textvariable=self.voice_var,
            values=[voice.name for voice in self.voice_manager.available_voices],
            state='readonly',
            width=30
        )
        self.voice_combo.pack(side=tk.LEFT, padx=5)
        self.voice_combo.bind('<<ComboboxSelected>>', self.change_voice)

        # Speech rate control
        ttk.Label(voice_frame, text="Rate:").pack(side=tk.LEFT, padx=5)
        self.rate_var = tk.IntVar(value=175)
        self.rate_scale = ttk.Scale(
            voice_frame,
            from_=100,
            to=300,
            variable=self.rate_var,
            orient=tk.HORIZONTAL,
            length=100,
            command=self.change_rate
        )
        self.rate_scale.pack(side=tk.LEFT, padx=5)

        # Volume control
        ttk.Label(voice_frame, text="Volume:").pack(side=tk.LEFT, padx=5)
        self.volume_var = tk.DoubleVar(value=1.0)
        self.volume_scale = ttk.Scale(
            voice_frame,
            from_=0.0,
            to=1.0,
            variable=self.volume_var,
            orient=tk.HORIZONTAL,
            length=100,
            command=self.change_volume
        )
        self.volume_scale.pack(side=tk.LEFT, padx=5)

        # Mute toggle
        self.mute_var = tk.BooleanVar(value=False)
        self.mute_btn = ttk.Checkbutton(
            voice_frame,
            text="Mute",
            variable=self.mute_var,
            command=self.toggle_mute
        )
        self.mute_btn.pack(side=tk.LEFT, padx=5)

    def create_menu(self):
        self.menu_bar = tk.Menu(self.root)
        self.file_menu = tk.Menu(self.menu_bar, tearoff=0)
        self.file_menu.add_command(label="New Conversation", command=self.new_conversation)
        self.file_menu.add_command(label="Open Conversation", command=self.open_conversation)
        self.file_menu.add_command(label="Save Conversation As", command=self.save_conversation_as)
        self.file_menu.add_command(label="Set Save Folder", command=self.set_save_folder)
        self.file_menu.add_separator()
        self.file_menu.add_command(label="Clear Conversation", command=self.confirm_clear_conversation)
        self.file_menu.add_separator()
        self.file_menu.add_command(label="Exit", command=self.cleanup_and_exit)
        self.menu_bar.add_cascade(label="File", menu=self.file_menu)

        # Add Voice menu
        self.voice_menu = tk.Menu(self.menu_bar, tearoff=0)
        self.voice_menu.add_command(label="Voice Settings", command=self.show_voice_settings)
        self.menu_bar.add_cascade(label="Voice", menu=self.voice_menu)
        
        self.root.config(menu=self.menu_bar)

    def create_chat_interface(self):
        self.chat_frame = ttk.Frame(self.root)
        self.chat_frame.pack(expand=True, fill='both', padx=5, pady=5)

        self.chat_display = tk.Text(self.chat_frame, wrap=tk.WORD, state='disabled')
        self.chat_display.pack(expand=True, fill='both')

        self.scrollbar = ttk.Scrollbar(self.chat_display, command=self.chat_display.yview)
        self.scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        self.chat_display.config(yscrollcommand=self.scrollbar.set)

        self.input_frame = ttk.Frame(self.root)
        self.input_frame.pack(fill=tk.X, padx=5, pady=5)
        self.input_field = ttk.Entry(self.input_frame)
        self.input_field.pack(side=tk.LEFT, expand=True, fill=tk.X)
        self.send_btn = ttk.Button(self.input_frame, text="Send", command=self.queue_message)
        self.send_btn.pack(side=tk.LEFT, padx=5)

    def create_status_bar(self):
        self.status_bar = ttk.Frame(self.root)
        self.status_bar.pack(fill=tk.X, padx=5, pady=2)

        self.memory_label = ttk.Label(self.status_bar, text="Messages: 0")
        self.memory_label.pack(side=tk.LEFT)

        self.system_prompt_var = tk.StringVar()
        self.system_prompt_combo = ttk.Combobox(
            self.status_bar, 
            textvariable=self.system_prompt_var, 
            state='normal',
            width=40
        )
        self.system_prompt_combo.pack(side=tk.LEFT, padx=10)
        self.system_prompt_combo.bind("<<ComboboxSelected>>", self.update_system_prompt)

        self.available_models = OllamaChecker.get_available_models()
        self.selected_model_var = tk.StringVar()
        self.model_combo = ttk.Combobox(
            self.status_bar,
            textvariable=self.selected_model_var,
            values=self.available_models,
            state='readonly',
            width=30
        )
        self.model_combo.pack(side=tk.LEFT, padx=10)

        self.status_label = ttk.Label(self.status_bar, text="● Connected")
        self.status_label.pack(side=tk.RIGHT)

    def change_voice(self, event=None):
        if self.voice_combo.current() >= 0:
            voice_id = self.voice_manager.available_voices[self.voice_combo.current()].id
            self.voice_manager.set_voice(voice_id)
            self.voice_manager.speak("Voice changed successfully")

    def change_rate(self, event=None):
        self.voice_manager.set_rate(self.rate_var.get())

    def change_volume(self, event=None):
        self.voice_manager.set_volume(self.volume_var.get())

    def toggle_mute(self):
        self.voice_manager.set_volume(0.0 if self.mute_var.get() else self.volume_var.get())

    def show_voice_settings(self):
        settings_window = tk.Toplevel(self.root)
        settings_window.title("Voice Settings")
        settings_window.geometry("400x300")
        settings_window.transient(self.root)
        
        ttk.Label(settings_window, text="Voice Settings", font=('Helvetica', 14, 'bold')).pack(pady=10)
        
        # Add advanced voice settings
        advanced_frame = ttk.LabelFrame(settings_window, text="Advanced Settings")
        advanced_frame.pack(fill=tk.X, padx=10, pady=5)
        
        # Add pitch control
        ttk.Label(advanced_frame, text="Pitch:").pack()
        pitch_var = tk.DoubleVar(value=1.0)
        pitch_scale = ttk.Scale(
            advanced_frame,
            from_=0.5,
            to=2.0,
            variable=pitch_var,
            orient=tk.HORIZONTAL
        )
        pitch_scale.pack(fill=tk.X, padx=5)
        
        # Add voice test button
        ttk.Button(
            settings_window,
            text="Test Voice",
            command=lambda: self.voice_manager.speak("This is a test of the current voice settings.")
        ).pack(pady=10)

    def set_save_folder(self):
        folder = filedialog.askdirectory(
            title="Select Save Folder",
            initialdir=self.save_folder
        )
        if folder:
            self.save_folder = folder
            os.makedirs(folder, exist_ok=True)

    def queue_message(self):
        if message := self.input_field.get().strip():
            self.input_field.delete(0, tk.END)
            self.message_queue.put(('user', message))

    def process_messages(self):
        try:
            while not self.message_queue.empty():
                role, content = self.message_queue.get_nowait()
                self.add_message(role, content)
                if role == 'user':
                    threading.Thread(target=self.get_ai_response, daemon=True).start()
        finally:
            self.root.after(100, self.process_messages)

    def add_message(self, role, content):
        self.conversation.append({"role": role, "content": content})
        self.save_history()
        self.update_display()

    def get_ai_response(self):
        try:
            active_model = self.selected_model_var.get()
            if not active_model:
                self.show_error("No model selected!")
                return

            context = self.conversation[-self.settings.get('context_size', 10):]
            messages = [{"role": "system", "content": self.settings.get('system_prompt', '')}]
            messages.extend(context)

            self.conversation.append({"role": "assistant", "content": ""})
            self.root.after(0, self.update_display)

            with requests.post(
                "http://localhost:11434/api/chat",
                json={
                    "model": active_model,
                    "messages": messages,
                    "stream": True,
                    "temperature": self.settings.get('temperature', 0.7)
                },
                stream=True,
                timeout=30
            ) as response:

                if response.status_code == 200:
                    complete_response = ""
                    for line in response.iter_lines():
                        if line:
                            try:
                                data = json.loads(line)
                                if content := data.get('message', {}).get('content'):
                                    complete_response += content
                                    self.conversation[-1]['content'] = complete_response
                                    self.root.after(0, self.update_display)
                            except json.JSONDecodeError:
                                continue
                    
                    # Speak the complete response
                    self.voice_manager.speak(complete_response)
                    self.save_history()
                else:
                    self.handle_api_error(response)

        except Exception as e:
            self.handle_response_error(e)
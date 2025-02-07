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
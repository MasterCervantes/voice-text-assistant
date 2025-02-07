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
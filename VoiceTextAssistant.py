            voice_id = self.available_voices[self.voice_combo.current()].id
            self.tts_engine.setProperty('voice', voice_id)
            self.current_voice = voice_id
            # Test the new voice
            self.speak("Voice changed successfully")

    def change_rate(self, event=None):
        """Change the speech rate"""
        if self.tts_engine:
            self.tts_engine.setProperty('rate', self.rate_var.get())

    def change_volume(self, event=None):
        """Change the speech volume"""
        if self.tts_engine:
            self.tts_engine.setProperty('volume', self.volume_var.get())

    def toggle_mute(self):
        """Toggle speech muting"""
        if self.tts_engine:
            self.tts_engine.setProperty('volume', 0.0 if self.mute_var.get() else self.volume_var.get())

    def speak(self, text):
        """Speak the given text"""
        if self.tts_engine and not self.mute_var.get():
            try:
                # Create a thread for speech to avoid blocking
                threading.Thread(target=self._speak_thread, args=(text,), daemon=True).start()
            except Exception as e:
                print(f"Speech error: {e}")

    def _speak_thread(self, text):
        """Thread function for speech synthesis"""
        try:
            self.tts_engine.say(text)
            self.tts_engine.runAndWait()
        except Exception as e:
            print(f"Speech thread error: {e}")

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

    def set_save_folder(self):
        """Set the folder for saving conversations"""
        folder = filedialog.askdirectory(
            title="Select Save Folder",
            initialdir=self.save_folder
        )
        if folder:
            self.save_folder = folder
            os.makedirs(folder, exist_ok=True)

    def show_voice_settings(self):
        """Show voice settings dialog"""
        settings_window = tk.Toplevel(self.root)
        settings_window.title("Voice Settings")
        settings_window.geometry("400x300")
        settings_window.transient(self.root)
        
        # Create settings widgets
        ttk.Label(settings_window, text="Voice Settings", font=('Helvetica', 14, 'bold')).pack(pady=10)
        
        # Add advanced voice settings here
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
            command=lambda: self.speak("This is a test of the current voice settings.")
        ).pack(pady=10)

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
                    for line in response.iter_lines():
                        if line:
                            try:
                                data = json.loads(line)
                                if content := data.get('message', {}).get('content'):
                                    self.conversation[-1]['content'] += content
                                    self.root.after(0, self.update_display)
                            except json.JSONDecodeError:
                                continue
                    
                    # Speak the complete response
                    self.speak(self.conversation[-1]['content'])
                    self.save_history()
                else:
                    self.handle_api_error(response)

        except Exception as e:
            self.handle_response_error(e)

    def cleanup_and_exit(self):
        """Clean up resources and exit"""
        if self.tts_engine:
            self.tts_engine.stop()
        self.root.quit()

    # Include all other methods from the original TextAssistant...
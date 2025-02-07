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
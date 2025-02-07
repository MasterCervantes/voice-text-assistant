    def update_display(self):
        self.chat_display.config(state='normal')
        self.chat_display.delete(1.0, tk.END)
        context_size = self.settings.get('context_size', 10)
        start_index = max(0, len(self.conversation) - context_size)
        self.displayed_message_indices = list(range(start_index, len(self.conversation)))

        for idx in self.displayed_message_indices:
            msg = self.conversation[idx]
            prefix = "You: " if msg['role'] == 'user' else "Assistant: "
            tag_name = f"msg_{idx}"
            self.chat_display.insert(tk.END, f"{prefix}{msg['content']}\n\n", tag_name)
            self.chat_display.tag_config(tag_name, background='white')

        self.chat_display.config(state='disabled')
        self.chat_display.see(tk.END)
        self.memory_label.config(text=f"Messages: {len(self.conversation)}")

    def load_data(self):
        self.settings = self.load_settings()
        system_prompts = self.settings.get("system_prompts", ["You are a helpful assistant."])
        self.system_prompt_combo['values'] = system_prompts
        self.system_prompt_combo.set(self.settings.get("system_prompt", "You are a helpful assistant."))

    def load_settings(self):
        try:
            if os.path.exists('settings.json'):
                with open('settings.json', 'r') as f:
                    return json.load(f)
        except Exception as e:
            print(f"Error loading settings: {e}")
        return {}

    def handle_api_error(self, response):
        if self.conversation[-1]['content'] == "":
            del self.conversation[-1]
        self.show_error(f"API Error: {response.status_code}")

    def handle_response_error(self, error):
        if self.conversation and self.conversation[-1]['content'] == "":
            del self.conversation[-1]
        self.show_error(str(error))
        self.root.after(0, self.update_display)

    def show_error(self, message):
        self.root.after(0, messagebox.showerror, "Error", message)

    def new_conversation(self):
        if self.conversation and messagebox.askyesno("New Conversation", "Save current conversation?"):
            self.save_history()
        self.conversation = []
        self.current_conversation = None
        self.update_display()

    def save_conversation_as(self):
        if name := simpledialog.askstring("Save As", "Enter conversation name:"):
            self.current_conversation = name
            self.save_history()

    def open_conversation(self):
        filepath = filedialog.askopenfilename(
            initialdir=self.save_folder,
            title="Open Conversation",
            filetypes=(("JSON files", "*.json"), ("All files", "*.*"))
        )
        if filepath:
            try:
                with open(filepath, 'r', encoding='utf-8') as f:
                    self.conversation = json.load(f)
                self.current_conversation = os.path.splitext(os.path.basename(filepath))[0]
                self.update_display()
            except Exception as e:
                messagebox.showerror("Error", f"Failed to load conversation: {e}")

    def confirm_clear_conversation(self):
        if messagebox.askyesno("Confirm Clear", "Are you sure you want to clear the current conversation?"):
            self.conversation = []
            self.save_history()
            self.update_display()

    def save_history(self):
        try:
            if not hasattr(self, 'current_conversation') or not self.current_conversation:
                self.save_conversation_as()
                return

            os.makedirs(self.save_folder, exist_ok=True)
            filepath = os.path.join(self.save_folder, f"{self.current_conversation}.json")
            with open(filepath, 'w', encoding='utf-8') as f:
                json.dump(self.conversation, f, ensure_ascii=False, indent=2)
        except Exception as e:
            print(f"Error saving history: {e}")

    def update_system_prompt(self, event=None):
        if new_prompt := self.system_prompt_var.get():
            self.settings['system_prompt'] = new_prompt
            if new_prompt not in self.system_prompt_combo['values']:
                if messagebox.askyesno("New Prompt", "Save this as a new system prompt?"):
                    self.settings.setdefault("system_prompts", []).append(new_prompt)
                    self.system_prompt_combo['values'] = self.settings["system_prompts"]
            try:
                with open('settings.json', 'w') as f:
                    json.dump(self.settings, f, indent=2)
            except Exception as e:
                messagebox.showerror("Error", f"Failed to save settings: {e}")

    def setup_bindings(self):
        self.input_field.bind("<Return>", lambda e: self.queue_message())
        self.root.bind("<Control-s>", lambda e: self.save_conversation_as())
        self.chat_display.bind("<Button-3>", self.show_context_menu)
        self.chat_display.bind("<Button-2>", self.show_context_menu)  # For macOS

    def check_ollama_status(self):
        status = OllamaChecker.is_running()
        self.status_label.config(
            text="● Connected" if status else "○ Disconnected",
            foreground="green" if status else "red"
        )
        self.root.after(10000, self.check_ollama_status)

    def cleanup_and_exit(self):
        """Clean up resources and exit"""
        self.voice_manager.cleanup()
        self.root.quit()

if __name__ == "__main__":
    root = tk.Tk()
    app = VoiceTextAssistant(root)
    root.mainloop()
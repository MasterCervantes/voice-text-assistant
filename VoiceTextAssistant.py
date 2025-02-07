    def update_display(self):
        try:
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
        except Exception as e:
            logging.error(f"Error in update_display: {str(e)}")
            logging.error(traceback.format_exc())

    def load_data(self):
        try:
            self.settings = self.load_settings()
            system_prompts = self.settings.get("system_prompts", ["You are a helpful assistant."])
            self.system_prompt_combo['values'] = system_prompts
            self.system_prompt_combo.set(self.settings.get("system_prompt", "You are a helpful assistant."))
        except Exception as e:
            logging.error(f"Error in load_data: {str(e)}")
            logging.error(traceback.format_exc())

    def load_settings(self):
        try:
            if os.path.exists('settings.json'):
                with open('settings.json', 'r') as f:
                    return json.load(f)
        except Exception as e:
            logging.error(f"Error loading settings: {str(e)}")
            logging.error(traceback.format_exc())
        return {}

    def setup_bindings(self):
        try:
            self.input_field.bind("<Return>", lambda e: self.queue_message())
            self.root.bind("<Control-s>", lambda e: self.save_conversation_as())
            self.chat_display.bind("<Button-3>", self.show_context_menu)
            self.chat_display.bind("<Button-2>", self.show_context_menu)  # For macOS
        except Exception as e:
            logging.error(f"Error in setup_bindings: {str(e)}")
            logging.error(traceback.format_exc())

    def show_context_menu(self, event):
        try:
            menu = tk.Menu(self.root, tearoff=0)
            menu.add_command(label="Copy", command=lambda: self.chat_display.event_generate('<<Copy>>'))
            menu.tk_popup(event.x_root, event.y_root)
        except Exception as e:
            logging.error(f"Error in show_context_menu: {str(e)}")
            logging.error(traceback.format_exc())

    def cleanup_and_exit(self):
        try:
            logging.info("Cleaning up and exiting")
            self.voice_manager.cleanup()
            self.root.quit()
        except Exception as e:
            logging.error(f"Error in cleanup_and_exit: {str(e)}")
            logging.error(traceback.format_exc())

if __name__ == "__main__":
    try:
        root = tk.Tk()
        app = VoiceTextAssistant(root)
        root.mainloop()
    except Exception as e:
        logging.error(f"Main execution error: {str(e)}")
        logging.error(traceback.format_exc())
        messagebox.showerror("Error", f"Application error: {str(e)}")

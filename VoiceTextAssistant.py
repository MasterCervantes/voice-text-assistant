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
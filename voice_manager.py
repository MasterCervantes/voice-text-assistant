import pyttsx3
import threading
from queue import Queue
import logging

class VoiceManager:
    def __init__(self):
        self.engine = None
        self.voice_queue = Queue()
        self.current_voice = None
        self.available_voices = []
        self.is_speaking = False
        self.speaking_thread = None
        self.initialize_engine()

    def initialize_engine(self):
        try:
            self.engine = pyttsx3.init()
            self.available_voices = self.engine.getProperty('voices')
            if self.available_voices:
                self.current_voice = self.available_voices[0].id
                self.engine.setProperty('voice', self.current_voice)
            self.engine.setProperty('rate', 175)
            self.start_speech_thread()
        except Exception as e:
            logging.error(f"Failed to initialize speech engine: {e}")
            self.engine = None

    def start_speech_thread(self):
        self.speaking_thread = threading.Thread(target=self._process_speech_queue, daemon=True)
        self.speaking_thread.start()

    def _process_speech_queue(self):
        while True:
            text = self.voice_queue.get()
            if text is None:  # Stop signal
                break
            try:
                self.is_speaking = True
                self.engine.say(text)
                self.engine.runAndWait()
            except Exception as e:
                logging.error(f"Speech error: {e}")
            finally:
                self.is_speaking = False
                self.voice_queue.task_done()

    def speak(self, text):
        if self.engine and text:
            self.voice_queue.put(text)

    def set_voice(self, voice_id):
        if self.engine and voice_id:
            try:
                self.engine.setProperty('voice', voice_id)
                self.current_voice = voice_id
            except Exception as e:
                logging.error(f"Error setting voice: {e}")

    def set_rate(self, rate):
        if self.engine:
            try:
                self.engine.setProperty('rate', rate)
            except Exception as e:
                logging.error(f"Error setting rate: {e}")

    def set_volume(self, volume):
        if self.engine:
            try:
                self.engine.setProperty('volume', max(0.0, min(1.0, volume)))
            except Exception as e:
                logging.error(f"Error setting volume: {e}")

    def stop_speaking(self):
        if self.engine:
            try:
                self.engine.stop()
                while not self.voice_queue.empty():
                    self.voice_queue.get()
                    self.voice_queue.task_done()
            except Exception as e:
                logging.error(f"Error stopping speech: {e}")

    def cleanup(self):
        if self.engine:
            self.voice_queue.put(None)  # Signal thread to stop
            if self.speaking_thread:
                self.speaking_thread.join()
            self.engine.stop()
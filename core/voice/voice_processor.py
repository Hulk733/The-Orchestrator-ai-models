
import speech_recognition as sr
import pyttsx3
import threading
import queue
import asyncio
from typing import Optional, Callable

class VoiceProcessor:
    def __init__(self):
        self.recognizer = sr.Recognizer()
        self.microphone = sr.Microphone()
        self.tts_engine = pyttsx3.init()
        self.is_listening = False
        self.voice_queue = queue.Queue()
        
        # Configure TTS
        self.tts_engine.setProperty('rate', 150)
        self.tts_engine.setProperty('volume', 0.9)
        
        # Adjust for ambient noise
        with self.microphone as source:
            self.recognizer.adjust_for_ambient_noise(source)
    
    def start_listening(self, callback: Callable[[str], None]):
        """Start continuous voice recognition"""
        self.is_listening = True
        
        def listen_continuously():
            while self.is_listening:
                try:
                    with self.microphone as source:
                        audio = self.recognizer.listen(source, timeout=1, phrase_time_limit=5)
                    
                    try:
                        text = self.recognizer.recognize_google(audio)
                        if text:
                            callback(text)
                    except sr.UnknownValueError:
                        pass  # Could not understand audio
                    except sr.RequestError as e:
                        print(f"Could not request results; {e}")
                        
                except sr.WaitTimeoutError:
                    pass  # Timeout, continue listening
        
        self.listen_thread = threading.Thread(target=listen_continuously)
        self.listen_thread.daemon = True
        self.listen_thread.start()
    
    def stop_listening(self):
        """Stop voice recognition"""
        self.is_listening = False
    
    def speak(self, text: str):
        """Convert text to speech"""
        def speak_async():
            self.tts_engine.say(text)
            self.tts_engine.runAndWait()
        
        speak_thread = threading.Thread(target=speak_async)
        speak_thread.daemon = True
        speak_thread.start()
    
    def recognize_from_audio(self, audio_data) -> Optional[str]:
        """Recognize speech from audio data"""
        try:
            return self.recognizer.recognize_google(audio_data)
        except sr.UnknownValueError:
            return None
        except sr.RequestError as e:
            print(f"Recognition error: {e}")
            return None

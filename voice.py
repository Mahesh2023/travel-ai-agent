"""
Voice Assistant Module for Travel AI Agent
Speech recognition, text-to-speech, and WebRTC for real-time voice
"""

import speech_recognition as sr
from gtts import gTTS
import io
import base64
from typing import Optional
import asyncio
from fastapi import WebSocket, WebSocketDisconnect
import json

class VoiceAssistant:
    """Voice assistant with speech recognition and synthesis"""
    
    def __init__(self):
        self.recognizer = sr.Recognizer()
    
    def speech_to_text(self, audio_data: bytes, language: str = "en-US") -> str:
        """Convert speech to text"""
        try:
            # Create audio data from bytes
            audio = sr.AudioData(audio_data, sample_rate=16000, sample_width=2)
            
            # Recognize speech
            text = self.recognizer.recognize_google(audio, language=language)
            return text
        except sr.UnknownValueError:
            return ""
        except sr.RequestError:
            return ""
        except Exception as e:
            print(f"Speech recognition error: {e}")
            return ""
    
    def text_to_speech(self, text: str, language: str = "en") -> bytes:
        """Convert text to speech"""
        try:
            # Generate speech
            tts = gTTS(text=text, lang=language, slow=False)
            
            # Save to bytes buffer
            audio_buffer = io.BytesIO()
            tts.write_to_fp(audio_buffer)
            
            # Get audio bytes
            audio_buffer.seek(0)
            audio_bytes = audio_buffer.read()
            
            return audio_bytes
        except Exception as e:
            print(f"Text-to-speech error: {e}")
            return b""
    
    def text_to_speech_base64(self, text: str, language: str = "en") -> str:
        """Convert text to speech and return base64 encoded audio"""
        audio_bytes = self.text_to_speech(text, language)
        return base64.b64encode(audio_bytes).decode('utf-8')

class VoiceWebSocketHandler:
    """WebSocket handler for real-time voice communication"""
    
    def __init__(self):
        self.active_connections: list[WebSocket] = []
        self.voice_assistant = VoiceAssistant()
    
    async def connect(self, websocket: WebSocket):
        """Accept WebSocket connection"""
        await websocket.accept()
        self.active_connections.append(websocket)
    
    def disconnect(self, websocket: WebSocket):
        """Disconnect WebSocket"""
        self.active_connections.remove(websocket)
    
    async def handle_audio(self, websocket: WebSocket, audio_data: bytes):
        """Handle incoming audio and send response"""
        try:
            # Convert speech to text
            text = self.voice_assistant.speech_to_text(audio_data)
            
            if text:
                # Send text response
                await websocket.send_json({
                    "type": "text",
                    "text": text
                })
                
                # Convert response to speech (simulated - in real app, this would come from LLM)
                response_text = f"I heard: {text}"
                audio_base64 = self.voice_assistant.text_to_speech_base64(response_text)
                
                # Send audio response
                await websocket.send_json({
                    "type": "audio",
                    "audio": audio_base64
                })
            
        except Exception as e:
            print(f"Audio handling error: {e}")
            await websocket.send_json({
                "type": "error",
                "message": str(e)
            })
    
    async def broadcast(self, message: str):
        """Broadcast message to all connected clients"""
        for connection in self.active_connections:
            try:
                await connection.send_json({
                    "type": "broadcast",
                    "message": message
                })
            except:
                pass

# Global voice handler
voice_handler = VoiceWebSocketHandler()

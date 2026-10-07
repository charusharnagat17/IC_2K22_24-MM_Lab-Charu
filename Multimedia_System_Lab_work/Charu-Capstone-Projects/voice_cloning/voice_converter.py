"""
Instant Voice Converter using ElevenLabs Speech-to-Speech API
-------------------------------------------------------------
Hold SPACEBAR to speak -> Release SPACEBAR to output converted voice.

Author: Antigravity Agent
"""

import io
import os
import sys
import time
import threading
import numpy as np
import sounddevice as sd
import soundfile as sf
from pynput import keyboard
from colorama import init, Fore, Style
from elevenlabs.client import ElevenLabs

# Initialize colorama
init(autoreset=True)

# Default ElevenLabs API Key
DEFAULT_API_KEY = "sk_d6aa2b45793f43340bf5323171553a96c6a596f5e020d222"
API_KEY = os.environ.get("ELEVENLABS_API_KEY", DEFAULT_API_KEY)

# Audio Settings
SAMPLE_RATE = 44100  # High quality audio capture
CHANNELS = 1

class VoiceChangerApp:
    def __init__(self, api_key: str):
        print(f"{Fore.CYAN}Initializing ElevenLabs Client...{Style.RESET_ALL}")
        self.client = ElevenLabs(api_key=api_key)
        self.voices = []
        self.selected_voice = None
        
        # Audio recording state
        self.is_recording = False
        self.is_processing = False
        self.is_space_down = False
        self.audio_frames = []
        self.stream = None
        self.lock = threading.Lock()
        
        # Fetch available voices
        self.load_voices()

    def load_voices(self):
        try:
            voices_res = self.client.voices.get_all()
            self.voices = voices_res.voices
            if self.voices:
                self.selected_voice = self.voices[0]  # Default to first voice
            print(f"{Fore.GREEN}✓ Successfully loaded {len(self.voices)} voices from ElevenLabs.{Style.RESET_ALL}")
        except Exception as e:
            print(f"{Fore.RED}✗ Failed to fetch voices from ElevenLabs: {e}{Style.RESET_ALL}")
            sys.exit(1)

    def display_menu(self):
        print("\n" + "=" * 65)
        print(f"{Fore.YELLOW}        ELEVENLABS INSTANT VOICE CONVERTER (PUSH-TO-TALK){Style.RESET_ALL}")
        print("=" * 65)
        print(f"Current Target Voice: {Fore.GREEN}{self.selected_voice.name}{Style.RESET_ALL} (ID: {self.selected_voice.voice_id})")
        print("\nControls:")
        print(f"  • {Fore.WHITE}{Style.BRIGHT}[HOLD SPACEBAR]{Style.RESET_ALL} : Record your original voice")
        print(f"  • {Fore.WHITE}{Style.BRIGHT}[RELEASE SPACEBAR]{Style.RESET_ALL} : Convert & play in target voice")
        print(f"  • {Fore.WHITE}{Style.BRIGHT}[V]{Style.RESET_ALL} : Change Target Voice")
        print(f"  • {Fore.WHITE}{Style.BRIGHT}[Q / ESC]{Style.RESET_ALL} : Quit Application")
        print("=" * 65 + "\n")
        print(f"{Fore.CYAN}Ready! Press and hold SPACEBAR to speak...{Style.RESET_ALL}\n")

    def select_voice_menu(self):
        print("\n--- Available Voices ---")
        for idx, v in enumerate(self.voices):
            category = f" ({v.category})" if hasattr(v, 'category') and v.category else ""
            print(f"  [{idx + 1}] {v.name}{category}")
        print("------------------------")
        
        try:
            choice = input(f"Select voice number (1-{len(self.voices)}): ").strip()
            num = int(choice)
            if 1 <= num <= len(self.voices):
                self.selected_voice = self.voices[num - 1]
                print(f"{Fore.GREEN}Selected target voice: {self.selected_voice.name}{Style.RESET_ALL}")
            else:
                print(f"{Fore.RED}Invalid selection.{Style.RESET_ALL}")
        except ValueError:
            print(f"{Fore.RED}Invalid input.{Style.RESET_ALL}")
            
        self.display_menu()

    def audio_callback(self, indata, frames, time_info, status):
        if status:
            print(f"{Fore.YELLOW}Audio status: {status}{Style.RESET_ALL}", file=sys.stderr)
        if self.is_recording:
            self.audio_frames.append(indata.copy())

    def start_recording(self):
        with self.lock:
            if self.is_recording or self.is_processing:
                return
            self.is_recording = True
            self.audio_frames = []
            
            print(f"\r{Fore.RED}● [RECORDING] Hold SPACEBAR and speak into your microphone...{Style.RESET_ALL}", end="", flush=True)
            
            try:
                self.stream = sd.InputStream(
                    samplerate=SAMPLE_RATE,
                    channels=CHANNELS,
                    dtype='float32',
                    callback=self.audio_callback
                )
                self.stream.start()
            except Exception as e:
                print(f"\n{Fore.RED}Failed to start audio stream: {e}{Style.RESET_ALL}")
                self.is_recording = False

    def stop_recording_and_process(self):
        with self.lock:
            if not self.is_recording:
                return
            self.is_recording = False
            
            if self.stream:
                self.stream.stop()
                self.stream.close()
                self.stream = None

            print(f"\n{Fore.YELLOW}⏳ [RELEASED] Processing voice conversion with ElevenLabs...{Style.RESET_ALL}")
            self.is_processing = True

        # Process conversion in background thread to keep UI responsive
        threading.Thread(target=self._process_and_play, daemon=True).start()

    def _process_and_play(self):
        try:
            if not self.audio_frames:
                print(f"{Fore.YELLOW}⚠ No audio recorded. Hold spacebar longer to record.{Style.RESET_ALL}\n")
                return

            audio_data = np.concatenate(self.audio_frames, axis=0)
            duration = len(audio_data) / SAMPLE_RATE
            
            if duration < 0.3:
                print(f"{Fore.YELLOW}⚠ Recording too short ({duration:.2f}s). Hold spacebar while speaking.{Style.RESET_ALL}\n")
                return

            print(f"Recorded {duration:.2f}s of audio. Converting to voice '{self.selected_voice.name}'...")

            # Convert numpy array to WAV BytesIO buffer
            buf = io.BytesIO()
            sf.write(buf, audio_data, SAMPLE_RATE, format='WAV', subtype='PCM_16')
            buf.seek(0)

            # Call ElevenLabs Speech-to-Speech API
            start_time = time.time()
            converted_audio_stream = self.client.speech_to_speech.convert(
                voice_id=self.selected_voice.voice_id,
                audio=buf,
                model_id="eleven_multilingual_sts_v2"
            )
            
            audio_bytes = b"".join(converted_audio_stream)
            elapsed = time.time() - start_time
            print(f"{Fore.GREEN}✓ Voice converted in {elapsed:.2f} seconds! Playing audio...{Style.RESET_ALL}")

            # Decode converted audio and play back
            out_data, out_sr = sf.read(io.BytesIO(audio_bytes))
            
            print(f"{Fore.MAGENTA}🔊 [PLAYING] Outputting converted voice...{Style.RESET_ALL}")
            sd.play(out_data, out_sr)
            sd.wait()
            print(f"{Fore.GREEN}✓ Playback complete.{Style.RESET_ALL}\n")

        except Exception as e:
            print(f"{Fore.RED}✗ Error during voice conversion: {e}{Style.RESET_ALL}\n")
        finally:
            with self.lock:
                self.is_processing = False
            print(f"{Fore.CYAN}Ready! Press and hold SPACEBAR to speak...{Style.RESET_ALL}")

    def on_press(self, key):
        try:
            if key == keyboard.Key.space:
                if not self.is_space_down:
                    self.is_space_down = True
                    self.start_recording()
            elif hasattr(key, 'char') and key.char:
                char = key.char.lower()
                if char == 'v' and not self.is_recording and not self.is_processing:
                    self.select_voice_menu()
                elif char == 'q':
                    print(f"\n{Fore.YELLOW}Exiting program... Goodbye!{Style.RESET_ALL}")
                    return False
        except Exception:
            pass

    def on_release(self, key):
        try:
            if key == keyboard.Key.space:
                if self.is_space_down:
                    self.is_space_down = False
                    self.stop_recording_and_process()
            elif key == keyboard.Key.esc:
                print(f"\n{Fore.YELLOW}Exiting program... Goodbye!{Style.RESET_ALL}")
                return False
        except Exception:
            pass

    def run(self):
        self.display_menu()
        
        # Start Keyboard Listener
        with keyboard.Listener(on_press=self.on_press, on_release=self.on_release) as listener:
            try:
                listener.join()
            except KeyboardInterrupt:
                print(f"\n{Fore.YELLOW}Program interrupted. Exiting...{Style.RESET_ALL}")

if __name__ == "__main__":
    app = VoiceChangerApp(api_key=API_KEY)
    app.run()

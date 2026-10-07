"""
Graphical User Interface (GUI) Voice Converter using ElevenLabs API
------------------------------------------------------------------
Hold Spacebar or the "Push to Talk" button to speak, release to hear converted voice.

Author: Antigravity Agent
"""

import io
import os
import sys
import time
import threading
import tkinter as tk
from tkinter import ttk, messagebox, filedialog
import numpy as np
import sounddevice as sd
import soundfile as sf
from elevenlabs.client import ElevenLabs
from elevenlabs.types import VoiceSettings

DEFAULT_API_KEY = "sk_d6aa2b45793f43340bf5323171553a96c6a596f5e020d222"
API_KEY = os.environ.get("ELEVENLABS_API_KEY", DEFAULT_API_KEY)

SAMPLE_RATE = 44100
CHANNELS = 1

class VoiceConverterGUI:
    def __init__(self, root):
        self.root = root
        self.root.title("ElevenLabs Instant Voice Converter (Spacebar Push-To-Talk)")
        self.root.geometry("680x750")
        self.root.configure(bg="#1e1e2e")
        self.root.resizable(True, True)

        # ElevenLabs Client
        self.client = ElevenLabs(api_key=API_KEY)
        self.voices = []
        self.voice_map = {}
        
        # Audio & State variables
        self.is_recording = False
        self.is_processing = False
        self.is_space_down = False
        self.audio_frames = []
        self.last_converted_bytes = None
        self.stream = None
        self.lock = threading.Lock()

        # Build UI
        self._setup_styles()
        self._create_widgets()
        
        # Bind keyboard events
        self.root.bind("<KeyPress-space>", self.on_key_press)
        self.root.bind("<KeyRelease-space>", self.on_key_release)
        
        # Load voices asynchronously
        threading.Thread(target=self.load_voices, daemon=True).start()

    def _setup_styles(self):
        self.style = ttk.Style()
        self.style.theme_use("clam")
        
        # Custom dark palette
        self.style.configure(".", background="#1e1e2e", foreground="#cdd6f4", font=("Segoe UI", 10))
        self.style.configure("TFrame", background="#1e1e2e")
        self.style.configure("TLabelframe", background="#1e1e2e", foreground="#89b4fa", font=("Segoe UI", 10, "bold"))
        self.style.configure("TLabelframe.Label", background="#1e1e2e", foreground="#89b4fa")
        self.style.configure("TLabel", background="#1e1e2e", foreground="#cdd6f4")
        self.style.configure("TButton", font=("Segoe UI", 10, "bold"), padding=6)
        self.style.configure("TCombobox", padding=5)

    def _create_widgets(self):
        # Header
        header_frame = ttk.Frame(self.root)
        header_frame.pack(fill="x", px=20, py=15)

        title_lbl = tk.Label(
            header_frame,
            text="🎙 ElevenLabs Voice Converter",
            font=("Segoe UI", 18, "bold"),
            bg="#1e1e2e",
            fg="#89b4fa"
        )
        title_lbl.pack(anchor="w")

        sub_lbl = tk.Label(
            header_frame,
            text="Hold SPACEBAR or click button to speak -> Release to hear converted voice",
            font=("Segoe UI", 10, "italic"),
            bg="#1e1e2e",
            fg="#a6adc8"
        )
        sub_lbl.pack(anchor="w", pady=(2, 0))

        # Status & Level Meter Frame
        status_frame = ttk.LabelFrame(self.root, text=" Live Status ", padding=15)
        status_frame.pack(fill="x", px=20, py=10)

        self.status_box = tk.Label(
            status_frame,
            text="INITIALIZING...",
            font=("Segoe UI", 12, "bold"),
            bg="#313244",
            fg="#f9e2af",
            height=2,
            relief="flat",
            bd=0
        )
        self.status_box.pack(fill="x", pady=5)

        # Audio Volume Level Bar
        meter_label = ttk.Label(status_frame, text="Microphone Level:")
        meter_label.pack(anchor="w", pady=(5, 2))
        
        self.meter_canvas = tk.Canvas(status_frame, height=14, bg="#313244", highlightthickness=0)
        self.meter_canvas.pack(fill="x", pady=2)
        self.meter_bar = self.meter_canvas.create_rectangle(0, 0, 0, 14, fill="#a6e3a1")

        # Voice Settings Frame
        voice_frame = ttk.LabelFrame(self.root, text=" Target Voice & Parameters ", padding=15)
        voice_frame.pack(fill="x", px=20, py=10)

        # Voice Dropdown
        lbl_v = ttk.Label(voice_frame, text="Target Voice:")
        lbl_v.grid(row=0, column=0, sticky="w", pady=5)

        self.voice_combo = ttk.Combobox(voice_frame, state="readonly", width=40)
        self.voice_combo.grid(row=0, column=1, sticky="ew", padx=10, pady=5)
        voice_frame.columnconfigure(1, weight=1)

        # Settings: Stability slider
        lbl_stab = ttk.Label(voice_frame, text="Stability:")
        lbl_stab.grid(row=1, column=0, sticky="w", pady=5)
        self.stab_scale = ttk.Scale(voice_frame, from_=0.0, to=1.0, value=0.5)
        self.stab_scale.grid(row=1, column=1, sticky="ew", padx=10, pady=5)

        # Push to Talk Big Button Frame
        action_frame = ttk.Frame(self.root)
        action_frame.pack(fill="x", px=20, py=15)

        self.ptt_button = tk.Button(
            action_frame,
            text="🎤  HOLD SPACEBAR TO SPEAK\n(or click and hold here)",
            font=("Segoe UI", 13, "bold"),
            bg="#89b4fa",
            fg="#11111b",
            activebackground="#74c7ec",
            activeforeground="#11111b",
            height=3,
            relief="flat",
            cursor="hand2"
        )
        self.ptt_button.pack(fill="x")

        # Mouse press & release bindings on PTT button
        self.ptt_button.bind("<ButtonPress-1>", self.on_btn_press)
        self.ptt_button.bind("<ButtonRelease-1>", self.on_btn_release)

        # Output & Save Bar
        playback_frame = ttk.Frame(self.root)
        playback_frame.pack(fill="x", px=20, py=5)

        self.replay_btn = tk.Button(
            playback_frame,
            text="▶ Replay Last Conversion",
            font=("Segoe UI", 10, "bold"),
            bg="#313244",
            fg="#cdd6f4",
            activebackground="#45475a",
            command=self.replay_audio,
            state="disabled",
            relief="flat",
            padx=10,
            pady=5
        )
        self.replay_btn.pack(side="left", padx=(0, 10))

        self.save_btn = tk.Button(
            playback_frame,
            text="💾 Save Output Audio (.wav)",
            font=("Segoe UI", 10, "bold"),
            bg="#313244",
            fg="#cdd6f4",
            activebackground="#45475a",
            command=self.save_audio,
            state="disabled",
            relief="flat",
            padx=10,
            pady=5
        )
        self.save_btn.pack(side="left")

        # Log Window Frame
        log_frame = ttk.LabelFrame(self.root, text=" Event Log ", padding=10)
        log_frame.pack(fill="both", expand=True, px=20, py=10)

        self.log_text = tk.Text(
            log_frame,
            height=8,
            bg="#11111b",
            fg="#a6adc8",
            insertbackground="white",
            font=("Consolas", 9),
            relief="flat",
            bd=0
        )
        self.log_text.pack(fill="both", expand=True)

    def log(self, message):
        t_str = time.strftime("[%H:%M:%S] ")
        self.log_text.insert("end", t_str + message + "\n")
        self.log_text.see("end")

    def update_status(self, text, bg_color, fg_color="#11111b"):
        self.status_box.config(text=text, bg=bg_color, fg=fg_color)

    def update_meter(self, level):
        # level is 0.0 to 1.0
        width = self.meter_canvas.winfo_width()
        bar_w = int(width * min(1.0, level * 5.0)) # Boost visually
        self.meter_canvas.coords(self.meter_bar, 0, 0, bar_w, 14)

    def load_voices(self):
        try:
            self.log("Connecting to ElevenLabs API...")
            res = self.client.voices.get_all()
            self.voices = res.voices
            
            names = []
            for v in self.voices:
                display_name = f"{v.name} ({v.voice_id})"
                self.voice_map[display_name] = v
                names.append(display_name)
            
            self.voice_combo['values'] = names
            if names:
                self.voice_combo.current(0)
            
            self.update_status("READY: Press and hold SPACEBAR to speak", "#a6e3a1", "#11111b")
            self.log(f"Successfully loaded {len(self.voices)} voices.")
        except Exception as e:
            self.update_status("ERROR LOADING VOICES", "#f38ba8", "#11111b")
            self.log(f"API Error: {e}")

    def audio_callback(self, indata, frames, time_info, status):
        if self.is_recording:
            self.audio_frames.append(indata.copy())
            volume_norm = np.linalg.norm(indata) / np.sqrt(len(indata))
            self.root.after(0, self.update_meter, volume_norm)

    def start_recording(self):
        with self.lock:
            if self.is_recording or self.is_processing:
                return
            self.is_recording = True
            self.audio_frames = []
            
            self.update_status("● RECORDING... Speak Now", "#f38ba8", "#11111b")
            self.ptt_button.config(bg="#f38ba8", text="● RECORDING AUDIO...")
            self.log("Recording started...")
            
            try:
                self.stream = sd.InputStream(
                    samplerate=SAMPLE_RATE,
                    channels=CHANNELS,
                    dtype='float32',
                    callback=self.audio_callback
                )
                self.stream.start()
            except Exception as e:
                self.log(f"Audio record error: {e}")
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
                
            self.update_meter(0)
            self.update_status("⏳ CONVERTING VOICE VIA ELEVENLABS...", "#f9e2af", "#11111b")
            self.ptt_button.config(bg="#89b4fa", text="🎤  HOLD SPACEBAR TO SPEAK")
            self.is_processing = True

        threading.Thread(target=self._process_and_play, daemon=True).start()

    def _process_and_play(self):
        try:
            if not self.audio_frames:
                self.log("No audio recorded.")
                return

            audio_data = np.concatenate(self.audio_frames, axis=0)
            duration = len(audio_data) / SAMPLE_RATE

            if duration < 0.2:
                self.log(f"Audio clip too short ({duration:.2f}s). Hold spacebar longer.")
                return

            v_display = self.voice_combo.get()
            selected_voice = self.voice_map.get(v_display)
            if not selected_voice:
                self.log("No target voice selected.")
                return

            self.log(f"Converting {duration:.2f}s audio to target voice '{selected_voice.name}'...")

            buf = io.BytesIO()
            sf.write(buf, audio_data, SAMPLE_RATE, format='WAV', subtype='PCM_16')
            buf.seek(0)

            stab_val = self.stab_scale.get()
            
            t0 = time.time()
            converted_stream = self.client.speech_to_speech.convert(
                voice_id=selected_voice.voice_id,
                audio=buf,
                model_id="eleven_multilingual_sts_v2"
            )

            self.last_converted_bytes = b"".join(converted_stream)
            elapsed = time.time() - t0

            self.log(f"Converted in {elapsed:.2f} seconds! Playing output audio...")
            self.update_status(f"🔊 PLAYING CONVERTED VOICE ({selected_voice.name})", "#89b4fa", "#11111b")
            
            # Enable replay & save buttons
            self.root.after(0, self.enable_output_buttons)

            # Play audio
            out_data, out_sr = sf.read(io.BytesIO(self.last_converted_bytes))
            sd.play(out_data, out_sr)
            sd.wait()

            self.log("Playback complete.")
        except Exception as e:
            self.log(f"Conversion Error: {e}")
            messagebox.showerror("ElevenLabs API Error", str(e))
        finally:
            with self.lock:
                self.is_processing = False
            self.update_status("READY: Press and hold SPACEBAR to speak", "#a6e3a1", "#11111b")

    def enable_output_buttons(self):
        self.replay_btn.config(state="normal", bg="#89b4fa", fg="#11111b")
        self.save_btn.config(state="normal", bg="#a6e3a1", fg="#11111b")

    def replay_audio(self):
        if self.last_converted_bytes:
            threading.Thread(target=self._play_bytes, args=(self.last_converted_bytes,), daemon=True).start()

    def _play_bytes(self, b):
        out_data, out_sr = sf.read(io.BytesIO(b))
        sd.play(out_data, out_sr)
        sd.wait()

    def save_audio(self):
        if not self.last_converted_bytes:
            return
        path = filedialog.asksaveasfilename(
            defaultextension=".wav",
            filetypes=[("WAV Audio", "*.wav"), ("All Files", "*.*")],
            title="Save Converted Voice Audio"
        )
        if path:
            with open(path, "wb") as f:
                f.write(self.last_converted_bytes)
            self.log(f"Saved audio file to {path}")
            messagebox.showinfo("Saved", f"Audio saved successfully to:\n{path}")

    # Key bindings
    def on_key_press(self, event):
        if not self.is_space_down:
            self.is_space_down = True
            self.start_recording()

    def on_key_release(self, event):
        if self.is_space_down:
            self.is_space_down = False
            self.stop_recording_and_process()

    # Button bindings
    def on_btn_press(self, event):
        if not self.is_space_down:
            self.is_space_down = True
            self.start_recording()

    def on_btn_release(self, event):
        if self.is_space_down:
            self.is_space_down = False
            self.stop_recording_and_process()

if __name__ == "__main__":
    root = tk.Tk()
    app = VoiceConverterGUI(root)
    root.mainloop()

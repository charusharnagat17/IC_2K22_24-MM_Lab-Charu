import io
import time
import numpy as np
import sounddevice as sd
import soundfile as sf
from elevenlabs.client import ElevenLabs

API_KEY = "sk_d6aa2b45793f43340bf5323171553a96c6a596f5e020d222"
client = ElevenLabs(api_key=API_KEY)

# Fetch voices
voices = client.voices.get_all().voices
target_voice = voices[0] # First voice
print(f"Target Voice: {target_voice.name} ({target_voice.voice_id})")

# Record 2 seconds of audio test
sample_rate = 16000
print("Recording 2 seconds of test speech... Speak now!")
recorded_audio = sd.rec(int(2 * sample_rate), samplerate=sample_rate, channels=1, dtype='float32')
sd.wait()
print("Recording finished.")

# Save to BytesIO WAV buffer
buf = io.BytesIO()
sf.write(buf, recorded_audio, sample_rate, format='WAV')
buf.seek(0)

print("Sending to ElevenLabs Speech-to-Speech API...")
audio_stream = client.speech_to_speech.convert(
    voice_id=target_voice.voice_id,
    audio=buf,
    model_id="eleven_multilingual_sts_v2"
)

converted_bytes = b"".join(audio_stream)
print(f"Received {len(converted_bytes)} bytes of converted audio.")

# Play converted audio
data, out_sr = sf.read(io.BytesIO(converted_bytes))
print("Playing converted audio output...")
sd.play(data, out_sr)
sd.wait()
print("Playback complete!")

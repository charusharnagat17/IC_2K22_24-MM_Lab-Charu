# 🎙️ ElevenLabs Instant Voice Converter (Push-To-Talk)

An instant voice conversion application built in Python using the **ElevenLabs Speech-to-Speech (STS) API**. Hold down the **SPACEBAR** to record your voice, and release the **SPACEBAR** to immediately hear your speech converted into a target voice.

---

## 🌟 Features

- **Push-To-Talk Control**:
  - **Press & Hold Spacebar**: Starts audio recording from your microphone instantly.
  - **Release Spacebar**: Stops recording, sends audio to ElevenLabs Speech-to-Speech API, and plays converted output.
- **Multiple Target Voices**: Dynamically loads all available voices from your ElevenLabs account (`Roger`, `Sarah`, `Charlie`, `George`, `Laura`, `Alice`, etc.).
- **Dual Interface Modes**:
  1. **GUI Mode (`voice_converter_gui.py`)**: Modern Tkinter application with live volume level meter, voice selector dropdown, PTT button, output audio replay & file saving.
  2. **CLI Mode (`voice_converter.py`)**: Colorized terminal application with global hotkeys.
- **High Audio Fidelity**: 44.1 kHz 16-bit audio recording with in-memory stream processing using `io.BytesIO()`.

---

## ⚙️ Prerequisites & Setup

### 1. Requirements
Ensure Python 3.9+ is installed on your system.

### 2. Install Dependencies
Run the following command in terminal or command prompt:

```bash
pip install -r requirements.txt
```

---

## 🚀 How to Run

### Option 1: Run Graphical User Interface (GUI)
```bash
python voice_converter_gui.py
```
- Select your target voice from the dropdown list.
- Press & hold **SPACEBAR** (or click & hold the blue **HOLD SPACEBAR TO SPEAK** button).
- Speak into your microphone.
- Release the **SPACEBAR** or button. The converted voice will play through your speakers automatically!
- Click **Replay Last Conversion** or **Save Output Audio (.wav)** to keep the file.

### Option 2: Run Command Line Interface (CLI)
```bash
python voice_converter.py
```
- Press & hold **SPACEBAR** to record.
- Release **SPACEBAR** to convert and listen.
- Press **`V`** to open voice selection menu.
- Press **`Q`** or **`ESC`** to quit.

---

## 🔑 ElevenLabs API Key

The application is pre-configured with your API key:
`sk_d6aa2b45793f43340bf5323171553a96c6a596f5e020d222`

Alternatively, you can set your API key as an environment variable:
```bash
set ELEVENLABS_API_KEY=your_api_key_here
```

---

## 📁 File Structure

- `voice_converter_gui.py`: Graphical user interface implementation (Tkinter).
- `voice_converter.py`: Command-line interface implementation (`pynput` + `colorama`).
- `test_conversion.py`: Quick diagnostic & API verification test script.
- `requirements.txt`: Python package dependencies.
- `README.md`: System documentation.

# 🧙‍♂️ The Dungeon Scribe

Turn your raw Craig bot recordings into polished D&D session notes with this all-in-one transcription and summarization tool. Powered by Whisper and OpenAI GPT, with a modern drag-and-drop interface.

---

## 📸 Features

- 🎙️ **Transcribe multitrack Craig bot recordings**
- 🧠 **Summarize D&D sessions using GPT**
- 👤 **Maps Discord usernames to Player/Character names**
- 💻 **Modern dark-themed GUI for Windows**
- 🗂️ **Stores results locally and on Unraid NAS**
- ⚙️ **Configurable via GUI settings window**
- 🔒 **Keeps API keys and file paths in config.json**

---

## 🧰 Requirements

- Python 3.10+
- NVIDIA GPU (recommended for Whisper speed)
- [ffmpeg](https://ffmpeg.org/) installed and in your PATH (used by Whisper)
- A Craig bot `.zip` file containing multitrack audio (1 per speaker)
- An OpenAI API key

---

## 🧪 Setup Instructions

### 1. Clone the Repository

```bash
git clone https://github.com/jkwitchel/the-dungeon-scribe.git
cd the-dungeon-scribe
```

### 2. Install Dependencies

```bash
pip install -r requirements.txt
```

> Make sure your environment has GPU access if you're using Whisper with CUDA.

### 3. (Optional) Add FFmpeg to Path

- Windows users: Download [FFmpeg](https://ffmpeg.org/download.html), extract it, and add the `bin` folder to your system `PATH`.

### 4. Configure the App

You can either:
- Run the app and click `Settings ⚙️` to set folders, API keys, models, and speaker mappings, or
- Manually edit the `config.json` file.

Example:

```json
{
  "local_transcript_dir": "E:/SessionTranscripts/Transcripts",
  "local_summary_dir": "E:/SessionTranscripts/Summaries",
  "unraid_path": "//TOWER/jwitchel/DND/Sessions",
  "openai_api_key": "sk-...",
  "openai_model": "gpt-4o-mini",
  "whisper_model": "medium",
  "verbose_logging": true,
  "speaker_map": {
    "discord username": {
      "player": "Jeremy",
      "character": "Gamemaster"
    }
  }
}
```

---

## 🖥️ Running the App

```bash
python dnd_transcription_gui.py
```

Then:
1. Browse for your Craig `.zip` file.
2. Click **Transcribe & Summarize**.
3. Output files will appear in your configured folders.

---

## 🔍 File Overview

| File | Description |
|------|-------------|
| `dnd_transcription_gui.py` | The main GUI program (Tkinter) |
| `transcribe_audacity_zip.py` | Extracts audio + transcribes using Whisper |
| `dnd_transcript_summarizer.py` | Summarizes transcript using OpenAI GPT |
| `config.json` | Stores local paths, model choices, speaker map |
| `transcriber.log` | Logs from GUI and script execution |

---

## 🧠 How It Works

1. Craig zip file contains individual tracks per Discord speaker.
2. `transcribe_audacity_zip.py`:
   - Extracts and transcribes each track using Whisper
   - Uses speaker map to replace Discord usernames
   - Outputs a timestamped transcript
3. `dnd_transcript_summarizer.py`:
   - Chunks long transcripts
   - Sends each chunk to OpenAI API with speaker context
   - Combines summaries into one cohesive session note

---

## 💾 Unraid Integration

The app can store transcripts and summaries on a network path like `\\TOWER\jwitchel\DND\Sessions`. Configure this in your `config.json` or GUI settings.

---

## 🛠️ Customization

- 🧾 **Chunk size** and **token limits** are set in `dnd_transcript_summarizer.py`
- 🔧 **Transcription model** (`base`, `medium`, `large`, etc.) is set in GUI/config
- 🗣️ Add speaker mappings in the GUI or `config.json`

---

## 🚧 Roadmap / To Do

- [ ] Add support for alternate transcription sources (not just Craig)
- [ ] Support outputting Markdown or HTML logs
- [ ] Add multi-language transcription support
- [ ] Allow batch processing of multiple .zip files

---

## 🧙 About the Creator

Made by Jeremy Witchel to simplify and preserve my epic D&D campaigns with friends.

---

## 📝 License

MIT License. Feel free to fork and build upon it!

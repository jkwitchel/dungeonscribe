# 🧙‍♂️ The Dungeon Scribe

**The Dungeon Scribe** is a local Windows GUI tool for transcribing and summarizing Dungeons & Dragons sessions recorded using the Craig Discord bot. It uses **Whisper** for speech-to-text and **GPT-4o-mini** for intelligent summarization, supporting both chunk-based and final overviews. The output is ideal for DM notes and Unraid-based backups.

---

## 🧩 Features

- 🎤 **Multitrack transcription** of Craig `.zip` files using OpenAI's Whisper
- ✍️ **Chunk-by-chunk GPT summarization** with detailed event breakdowns
- 📘 **Final summary** compiled from all chunk summaries
- 🖥️ **Modern GUI** with dark theme and resizable layout
- 🔧 **Editable player mapping** (Discord → Player → Character)
- 📂 **Local + Unraid folder saving** for easy backups
- 🐍 **Configurable Whisper and GPT models**
- ✅ Separate buttons to:
  - Run **only transcription**
  - Run **only summarization**
  - Run **both in sequence**
- 📜 Automatically names transcripts and summaries using today’s date
- 🪵 Optional **verbose logging**

---

## 🧰 Requirements

- Python 3.9+
- `torch`, `whisper`, `openai`, `pydub`, `tiktoken`, `tkinter`

Install requirements:

```bash
pip install torch openai pydub git+https://github.com/openai/whisper.git tiktoken
```

---

## 🚀 How It Works

### Step 1: Transcription
- Runs `transcribe_audacity_zip.py`
- Extracts Craig `.zip` multitrack audio
- Transcribes each track using Whisper
- Applies speaker mapping for cleaner output
- Outputs formatted `.txt` transcript

### Step 2: Chunk Summarization
- Runs `dnd_chunk_and_summarize.py`
- Splits transcript into ~3000-token chunks
- Each chunk is summarized by GPT-4o-mini
- Outputs per-chunk `.txt` files in a folder

### Step 3: Final Summary
- Runs `dnd_second_pass_summary.py`
- Combines chunk summaries into one final summary
- Outputs clean, cohesive session recap for the DM

---

## 🛠 Configuration

All settings are saved to `config.json` and editable via the GUI:

```json
{
  "local_transcript_dir": "E:/SessionTranscripts/Transcripts",
  "local_summary_dir": "E:/SessionTranscripts/Summaries",
  "unraid_path": "//TOWER/jwitchel/DND/Sessions",
  "openai_api_key": "...",
  "openai_model": "gpt-4o-mini",
  "whisper_model": "medium",
  "verbose_logging": true,
  "speaker_map": {
    "discord_name": {
      "player": "Player Name",
      "character": "Character Name"
    }
  }
}
```

---

## 🖼 GUI Features

- Drag & drop style interface built with `tkinter`
- Select `.zip` file exported from Craig
- Transcribe, summarize, or both
- Access settings to change:
  - API keys
  - Folder paths
  - Speaker mapping
  - Models used
- See output status + errors in real time

---

## 📁 Output

- **Transcript Location:** `local_transcript_dir`
- **Summary Location:** `local_summary_dir`
- Files are saved as:

```
2025-04-04 - transcript.txt
2025-04-04 - summary.txt
```

- Automatically sync with Unraid (manual backup assumed via path)

---

## 🧑‍💻 Development Notes

- Use your RTX 3090 GPU for Whisper via PyTorch CUDA
- GPT model selection is isolated from Whisper
- Logs are stored in `transcriber.log`, `chunk_summarizer.log`, and `second_pass_summary.log`

---

## 💡 Future Ideas

- Export to Obsidian format
- Rich formatting (Markdown/HTML)
- Auto-backup to Unraid after each session
- Searchable transcript archive

---

## 📣 Credits

Created by **Jeremy Witchel**  
Inspired by epic D&D moments and a desire to never forget them.

---

🧠 _“Because even the smallest tavern tale deserves to be remembered.”_

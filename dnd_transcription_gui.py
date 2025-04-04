"""
D&D Session Transcriber GUI - The Dungeon Scribe

This script provides a graphical interface for transcribing and summarizing Dungeons & Dragons 
sessions recorded with the Craig Discord bot. It uses Whisper for speech-to-text transcription and 
OpenAI's GPT for summarization.

Author: Jeremy Witchel
Project: The Dungeon Scribe
"""

import tkinter as tk
from tkinter import ttk, filedialog, messagebox
import os
import shutil
import json
import subprocess
import threading
from datetime import date
import logging
from logging.handlers import RotatingFileHandler

# --- Constants ---
CONFIG_FILE = "config.json"
LOG_FILE = "transcriber.log"

# --- Logging Setup ---
def setup_logging(verbose=False):
    logger = logging.getLogger("Transcriber")
    logger.setLevel(logging.DEBUG if verbose else logging.INFO)
    handler = RotatingFileHandler(LOG_FILE, maxBytes=1024*1024, backupCount=3)
    formatter = logging.Formatter('%(asctime)s [%(levelname)s] %(message)s')
    handler.setFormatter(formatter)
    logger.handlers = []
    logger.addHandler(handler)
    return logger

log = setup_logging(verbose=False)

# --- Config Management ---
def load_config():
    if not os.path.exists(CONFIG_FILE):
        print("⚠️ config.json not found!")
        return {}
    with open(CONFIG_FILE, 'r') as f:
        print("✅ Loaded config.json")
        return json.load(f)


def save_config(config):
    with open(CONFIG_FILE, 'w') as f:
        json.dump(config, f, indent=4)

# --- Script Runner ---
def run_script(script_path):
    subprocess.run(["python", script_path], check=True)

# --- Player Mapping Window ---
class PlayerMappingWindow:
    def __init__(self, parent, config):
        self.top = tk.Toplevel(parent)
        self.top.title("Player Mapping")
        self.top.configure(bg="#1e1e1e")

        style = ttk.Style(self.top)
        style.theme_use('default')
        style.configure("TLabel", background="#1e1e1e", foreground="#ffffff")
        style.configure("TEntry", fieldbackground="#2e2e2e", foreground="#ffffff")
        style.configure("TButton", background="#333333", foreground="#ffffff")

        self.config = config
        self.entries = []

        frame = ttk.Frame(self.top)
        frame.grid(padx=20, pady=20)

        ttk.Label(frame, text="Discord Username").grid(row=0, column=0, padx=5, pady=5)
        ttk.Label(frame, text="Player Name").grid(row=0, column=1, padx=5, pady=5)
        ttk.Label(frame, text="Character Name").grid(row=0, column=2, padx=5, pady=5)

        speaker_map = self.config.get("speaker_map", {})
        for i, (discord, mapping) in enumerate(speaker_map.items(), start=1):
            d = ttk.Entry(frame)
            d.insert(0, discord)
            d.grid(row=i, column=0, padx=5, pady=2)
            p = ttk.Entry(frame)
            p.insert(0, mapping.get("player", ""))
            p.grid(row=i, column=1, padx=5, pady=2)
            c = ttk.Entry(frame)
            c.insert(0, mapping.get("character", ""))
            c.grid(row=i, column=2, padx=5, pady=2)
            self.entries.append((d, p, c))

        ttk.Button(frame, text="Add Row", command=self.add_row).grid(row=len(speaker_map)+1, column=0, pady=10)
        ttk.Button(frame, text="Save Mapping", command=self.save).grid(row=len(speaker_map)+1, column=1, columnspan=2, pady=10)

    def add_row(self):
        row = len(self.entries) + 1
        d = ttk.Entry(self.top)
        p = ttk.Entry(self.top)
        c = ttk.Entry(self.top)
        d.grid(row=row, column=0, padx=5, pady=2)
        p.grid(row=row, column=1, padx=5, pady=2)
        c.grid(row=row, column=2, padx=5, pady=2)
        self.entries.append((d, p, c))

    def save(self):
        speaker_map = {}
        for d, p, c in self.entries:
            discord = d.get().strip()
            player = p.get().strip()
            character = c.get().strip()
            if discord:
                speaker_map[discord] = {"player": player, "character": character}
        self.config["speaker_map"] = speaker_map
        save_config(self.config)
        self.top.destroy()

# --- Settings Window ---
class SettingsWindow:
    def __init__(self, parent, config, on_save_callback):
        self.top = tk.Toplevel(parent)
        self.top.title("Settings")
        self.top.configure(bg="#1e1e1e")

        style = ttk.Style(self.top)
        style.theme_use('default')
        style.configure("TLabel", background="#1e1e1e", foreground="#ffffff")
        style.configure("TEntry", fieldbackground="#2e2e2e", foreground="#ffffff")
        style.configure("TButton", background="#333333", foreground="#ffffff")
        style.configure("TCheckbutton", background="#1e1e1e", foreground="#ffffff")

        self.config = config
        self.on_save_callback = on_save_callback
        self.entries = {}

        frame = ttk.Frame(self.top)
        frame.grid(padx=20, pady=20, sticky="nsew")
        frame.columnconfigure(1, weight=1)

        fields = [
            ("OpenAI API Key", "openai_api_key"),
            ("OpenAI GPT Model", "openai_model"),
            ("Whisper Model", "whisper_model"),
            ("Transcript Folder", "local_transcript_dir"),
            ("Summary Folder", "local_summary_dir"),
            ("Unraid Path", "unraid_path"),
        ]

        for i, (label, key) in enumerate(fields):
            ttk.Label(frame, text=label).grid(row=i, column=0, sticky="w", pady=5)
            entry = ttk.Entry(frame)
            entry.insert(0, self.config.get(key, ""))
            entry.grid(row=i, column=1, sticky="ew", pady=5)
            self.entries[key] = entry
            if "dir" in key or "path" in key:
                ttk.Button(frame, text="Browse", command=lambda k=key: self.browse_folder(k)).grid(row=i, column=2, padx=5)

        self.verbose_var = tk.BooleanVar(value=self.config.get("verbose_logging", False))
        ttk.Checkbutton(frame, text="Enable Verbose Logging", variable=self.verbose_var).grid(
            row=len(fields), column=0, columnspan=2, pady=10, sticky="w")

        ttk.Button(frame, text="Edit Player Mapping", command=self.open_player_mapping).grid(
            row=len(fields)+1, column=0, columnspan=2, pady=5)

        ttk.Button(frame, text="Save Settings", command=self.save).grid(
            row=len(fields)+2, column=0, columnspan=3, pady=10)

    def browse_folder(self, key):
        path = filedialog.askdirectory()
        if path:
            self.entries[key].delete(0, tk.END)
            self.entries[key].insert(0, path)

    def open_player_mapping(self):
        PlayerMappingWindow(self.top, self.config)

    def save(self):
        for key, entry in self.entries.items():
            self.config[key] = entry.get()
        self.config["verbose_logging"] = self.verbose_var.get()
        save_config(self.config)
        self.on_save_callback(self.config)
        self.top.destroy()

# --- App Class ---
class TranscriptionApp:
    def __init__(self, root):
        self.root = root
        self.root.title("D&D Session Transcriber")
        self.root.geometry("600x300")
        self.root.configure(bg="#1e1e1e")
        self.root.columnconfigure(0, weight=1)
        self.root.rowconfigure(0, weight=1)

        style = ttk.Style()
        style.theme_use('default')
        style.configure("TFrame", background="#1e1e1e")
        style.configure("TLabel", background="#1e1e1e", foreground="#ffffff")
        style.configure("TButton", background="#333333", foreground="#ffffff")
        style.configure("TEntry", fieldbackground="#2e2e2e", foreground="#ffffff")

        self.config = load_config()

        self.zip_path = tk.StringVar()
        self.status = tk.StringVar()

        self.create_widgets()

    def create_widgets(self):
        frame = ttk.Frame(self.root)
        frame.grid(sticky="nsew", padx=20, pady=20)
        frame.columnconfigure(1, weight=1)

        ttk.Label(frame, text="Craig .zip File:").grid(row=0, column=0, sticky="w", pady=5)
        entry = ttk.Entry(frame, textvariable=self.zip_path)
        entry.grid(row=0, column=1, sticky="ew", pady=5)
        ttk.Button(frame, text="Browse", command=self.browse_file).grid(row=0, column=2, sticky="ew", padx=5)

        # NEW: Individual operation buttons
        ttk.Button(frame, text="Run Transcription Only", command=lambda: threading.Thread(target=self.run_transcription).start()).grid(row=1, column=0, columnspan=3, pady=5)
        ttk.Button(frame, text="Run Chunk + Summarize", command=lambda: threading.Thread(target=self.run_chunk_summarize).start()).grid(row=2, column=0, columnspan=3, pady=5)
        ttk.Button(frame, text="Run Final Summary", command=lambda: threading.Thread(target=self.run_second_pass).start()).grid(row=3, column=0, columnspan=3, pady=5)
        ttk.Button(frame, text="Run All (Full Pipeline)", command=lambda: threading.Thread(target=self.run_all).start()).grid(row=4, column=0, columnspan=3, pady=5)

        ttk.Label(frame, textvariable=self.status, foreground="#80ff80").grid(row=4, column=0, columnspan=3, pady=5)
        ttk.Button(frame, text="Settings ⚙️", command=self.open_settings).grid(row=5, column=0, columnspan=3, pady=10)

    def browse_file(self):
        path = filedialog.askopenfilename(filetypes=[("Zip Files", "*.zip")])
        if path:
            self.zip_path.set(path)

    def run_all(self):
        threading.Thread(target=self.process).start()

    def run_transcription(self):
        try:
            zip_file = self.zip_path.get()
            if not zip_file.endswith(".zip"):
                raise ValueError("Select a valid Craig .zip file")

            self.status.set("🔁 Running transcription...")

            today_str = date.today().isoformat()
            transcript_path = os.path.join(self.config['local_transcript_dir'], f"{today_str} - transcript.txt")

            os.makedirs(self.config['local_transcript_dir'], exist_ok=True)

            os.environ['CRAIG_ZIP'] = zip_file
            os.environ['TRANSCRIPT_OUTPUT'] = transcript_path
            os.environ['WHISPER_MODEL'] = self.config['whisper_model']
            os.environ['OPENAI_API_KEY'] = self.config['openai_api_key']
            os.environ['OPENAI_MODEL'] = self.config['openai_model']

            run_script("transcribe_audacity_zip.py")

            self.status.set("✅ Transcription complete.")
        except Exception as e:
            log.exception("Transcription error")
            messagebox.showerror("Error", str(e))
            self.status.set("❌ Transcription failed")

    def run_chunk_summarize(self):
            try:
                self.status.set("🧠 Chunking + Summarizing transcript...")
                today = date.today().isoformat()
                transcript_path = os.path.join(self.config['local_transcript_dir'], f"{today} - transcript.txt")
                chunk_dir = os.path.join(self.config['local_summary_dir'], f"{today} - chunks")
                os.makedirs(chunk_dir, exist_ok=True)

                os.environ['SUMMARY_INPUT'] = transcript_path
                os.environ['SUMMARY_CHUNK_DIR'] = chunk_dir
                os.environ['OPENAI_API_KEY'] = self.config['openai_api_key']
                os.environ['OPENAI_MODEL'] = self.config['openai_model']

                run_script("dnd_chunk_and_summarize.py")
                self.status.set("✅ Chunk summarization complete.")
            except Exception as e:
                log.exception("Chunk summarization error")
                messagebox.showerror("Error", str(e))
                self.status.set("❌ Chunk summarization failed")

    def run_second_pass(self):
        try:
            self.status.set("🧠 Running final summary...")
            today = date.today().isoformat()
            chunk_dir = os.path.join(self.config['local_summary_dir'], f"{today} - chunks")
            summary_out = os.path.join(self.config['local_summary_dir'], f"{today} - summary.txt")

            os.environ['SUMMARY_CHUNK_DIR'] = chunk_dir
            os.environ['SUMMARY_OUTPUT'] = summary_out
            os.environ['OPENAI_API_KEY'] = self.config['openai_api_key']
            os.environ['OPENAI_MODEL'] = self.config['openai_model']

            run_script("dnd_second_pass_summary.py")
            self.status.set("✅ Final summary complete.")
        except Exception as e:
            log.exception("Final summary error")
            messagebox.showerror("Error", str(e))
            self.status.set("❌ Final summary failed")
            
    def run_all(self):
        self.run_transcription()
        self.run_chunk_summarize()
        self.run_second_pass()

    def open_settings(self):
        fresh_config = load_config()  # Reload from file
        SettingsWindow(self.root, fresh_config, self.update_config)

    def update_config(self, new_config):
        self.config = new_config
        setup_logging(verbose=self.config.get("verbose_logging", False))

# --- Run GUI ---
if __name__ == "__main__":
    root = tk.Tk()
    app = TranscriptionApp(root)
    root.mainloop()

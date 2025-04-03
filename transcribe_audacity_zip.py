"""
D&D Craig Zip Transcriber - The Dungeon Scribe

This script extracts multitrack audio from a Craig bot .zip file and transcribes each track
using OpenAI's Whisper model. Each Discord speaker's track is mapped to a player and character name
using a config file, and the result is a formatted transcript with timestamps.

Author: Jeremy Witchel
Project: The Dungeon Scribe
"""

import os
import zipfile
import tempfile
import json
from datetime import timedelta
from pathlib import Path

import torch
import whisper
from pydub import AudioSegment

# === Environment Configuration ===
# Paths and model settings are pulled from environment variables (set by the GUI script).
zip_path = os.environ.get('CRAIG_ZIP')
output_path = os.environ.get('TRANSCRIPT_OUTPUT')
whisper_model = os.environ.get('WHISPER_MODEL', 'base')

if not zip_path or not output_path:
    raise ValueError("Missing required environment variables CRAIG_ZIP or TRANSCRIPT_OUTPUT.")

# Load speaker mapping from config.json (used to map Discord names to players/characters).
CONFIG_FILE = "config.json"
speaker_map = {}
if os.path.exists(CONFIG_FILE):
    with open(CONFIG_FILE, 'r') as f:
        try:
            config = json.load(f)
            speaker_map = config.get("speaker_map", {})
        except json.JSONDecodeError:
            print("⚠️ Warning: Could not parse speaker_map from config.json")

# === Utility Functions ===
# Helper functions to extract audio, find files, format timestamps, and map speakers.
def extract_audio_from_zip(zip_path: str, extract_to: str):
    with zipfile.ZipFile(zip_path, 'r') as zip_ref:
        zip_ref.extractall(extract_to)

def find_audio_files(folder: str, extensions=(".wav", ".mp3", ".ogg", ".m4a")) -> list[str]:
    audio_files = []
    for root, _, files in os.walk(folder):
        for file in files:
            if file.lower().endswith(extensions):
                audio_files.append(os.path.join(root, file))
    return sorted(audio_files)

def format_timestamp(seconds: float) -> str:
    return str(timedelta(seconds=int(seconds))).zfill(8)

def get_mapped_speaker_name(discord_name: str) -> str:
    mapping = speaker_map.get(discord_name)
    if mapping:
        player = mapping.get("player", "")
        character = mapping.get("character", "")
        return f"{player} ({character})" if character else player
    return discord_name

def transcribe_audio_files(audio_files: list[str], model_name: str = "base") -> list[str]:
    device = "cuda" if torch.cuda.is_available() else "cpu"
    print(f"Using Whisper model '{model_name}' on {device.upper()}.")

    model = whisper.load_model(model_name, device=device)
    all_segments = []

    for file in audio_files:
        discord_user = Path(file).stem
        speaker = get_mapped_speaker_name(discord_user)
        print(f"🔊 Transcribing {discord_user} as {speaker}...")

        result = model.transcribe(
            file,
            condition_on_previous_text=False,
            compression_ratio_threshold=1.8
        )

        for seg in result["segments"]:
            all_segments.append({
                "start": seg["start"],
                "end": seg["end"],
                "speaker": speaker,
                "text": seg["text"].strip()
            })

    all_segments.sort(key=lambda s: s["start"])

    formatted = []
    for seg in all_segments:
        ts = f"[{format_timestamp(seg['start'])} --> {format_timestamp(seg['end'])}]"
        formatted.append(f"{ts} {seg['speaker']}: {seg['text']}")

    return formatted

def write_transcript(transcriptions, output_path):
    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    with open(output_path, 'w', encoding='utf-8') as f:
        for line in transcriptions:
            f.write(line + "\n")
    print(f"✅ Transcript written to: {output_path}")

# === Main Execution ===
# Transcribe all audio files found in the .zip archive and write to a transcript file.
def main():
    print(f"Transcribing {zip_path} to {output_path} using Whisper model: {whisper_model}")

    with tempfile.TemporaryDirectory() as tmpdir:
        extract_audio_from_zip(zip_path, tmpdir)
        audio_files = find_audio_files(tmpdir)

        if not audio_files:
            raise FileNotFoundError("No audio files found in the zip archive.")

        print(f"Found {len(audio_files)} audio file(s).")
        transcriptions = transcribe_audio_files(audio_files, model_name=whisper_model)
        write_transcript(transcriptions, output_path=output_path)

if __name__ == "__main__":
    main()

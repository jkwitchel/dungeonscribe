import re
import json
from pathlib import Path

# Load config
with open("config.json", "r", encoding="utf-8") as f:
    config = json.load(f)

transcript_dir = Path(config["local_transcript_dir"])
speaker_map = config.get("active_speaker_map", {})

# Get latest transcript file
transcripts = list(transcript_dir.glob("*.txt"))
if not transcripts:
    raise FileNotFoundError(f"No transcript files found in {transcript_dir}")
latest_file = max(transcripts, key=lambda f: f.stat().st_mtime)

# Read file
with latest_file.open("r", encoding="utf-8") as f:
    lines = f.readlines()

# Define filler words
filler_words = {"ok", "okay", "um", "uh", "like", "you know", "so", "well", "hmm", "ah", "er", "eh", "huh"}
filler_pattern = re.compile(r"\b(" + "|".join(re.escape(word) for word in filler_words) + r")\b", re.IGNORECASE)

def shorten_timestamp(ts: str) -> str:
    match = re.match(r"\[(\d+):(\d{2}):(\d{2})\s+-->", ts)
    if match:
        h, m, s = map(int, match.groups())
        total_minutes = h * 60 + m
        return f"[{total_minutes}:{s:02d}]"
    return ts

def normalize_speaker(raw_name: str) -> str:
    cleaned = re.sub(r"^\d+-", "", raw_name)
    cleaned = re.sub(r"_\d+$", "", cleaned)
    return speaker_map.get(cleaned, {}).get("character", raw_name)

def clean_message(text: str) -> str:
    text = filler_pattern.sub("", text)
    text = re.sub(r"\s{2,}", " ", text).strip()
    # Remove non-ASCII characters
    text = text.encode("ascii", "ignore").decode("ascii")
    # Remove stray control characters or unknowns
    text = re.sub(r"[^\x20-\x7E]+", "", text)
    return text

processed_lines = []
for line in lines:
    match = re.match(r"(\[.*?\]) (\S+): (.*)", line)
    if not match:
        continue

    timestamp, raw_speaker, message = match.groups()
    timestamp = shorten_timestamp(timestamp)
    character_name = normalize_speaker(raw_speaker)
    cleaned_message = clean_message(message)

    # Skip lines that are empty after cleaning
    if not cleaned_message.strip():
        continue

    processed_lines.append(f"{timestamp} {character_name}: {cleaned_message}")

# Write to file
output_path = transcript_dir / "processed_transcript.txt"
with output_path.open("w", encoding="utf-8") as f:
    f.write("\n".join(processed_lines))

print(f"✅ Preprocessing complete. Saved to {output_path}")

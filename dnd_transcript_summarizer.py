"""
D&D Transcript Summarizer - The Dungeon Scribe

This script summarizes a transcribed D&D session using OpenAI's GPT model.
It loads a full transcript, splits it into manageable chunks (based on token limits),
and generates summary text for each chunk. It includes speaker mapping to provide
character context to the language model.

Author: Jeremy Witchel
Project: The Dungeon Scribe
"""

import os
import json
from pathlib import Path
from openai import OpenAI
import tiktoken

# === Load from environment variables (set by GUI script) ===
# These environment variables are passed in from the GUI before execution.
# - SUMMARY_INPUT: Path to the transcript file
# - SUMMARY_OUTPUT: Path to the output summary file
# - OPENAI_API_KEY: Your OpenAI API key
# - OPENAI_MODEL: The GPT model to use for summarization
input_path = os.environ.get('SUMMARY_INPUT')
output_path = os.environ.get('SUMMARY_OUTPUT')
openai_key = os.environ.get('OPENAI_API_KEY')
openai_model = os.environ.get('OPENAI_MODEL')

if not all([input_path, output_path, openai_key, openai_model]):
    raise ValueError("Missing required environment variables. Please check the GUI configuration.")

# === Load speaker map from config.json ===
# Maps Discord usernames to player and character names.
speaker_map = {}
CONFIG_FILE = "config.json"
if os.path.exists(CONFIG_FILE):
    with open(CONFIG_FILE, 'r') as f:
        try:
            config = json.load(f)
            speaker_map = config.get("speaker_map", {})
        except json.JSONDecodeError:
            print("⚠️ Warning: Could not parse speaker_map from config.json")

# === OpenAI Setup ===
os.environ["OPENAI_API_KEY"] = openai_key
client = OpenAI()

# === Tokenization Config ===
# We split the transcript into chunks small enough for the GPT model to handle.
# TOKEN_LIMIT is the model limit; CHUNK_SIZE is a safe lower bound for processing.
TOKEN_LIMIT = 8192
CHUNK_SIZE = 3000

encoding = tiktoken.encoding_for_model(openai_model)

# Count tokens in a string using the tiktoken encoder
def count_tokens(text: str) -> int:
    return len(encoding.encode(text))

# Splits the transcript into word chunks without exceeding the max token limit
def chunk_text(text: str, max_tokens: int = CHUNK_SIZE) -> list[str]:
    words = text.split()
    chunks = []
    current_chunk = []

    for word in words:
        current_chunk.append(word)
        if count_tokens(" ".join(current_chunk)) > max_tokens:
            current_chunk.pop()
            chunks.append(" ".join(current_chunk))
            current_chunk = [word]

    if current_chunk:
        chunks.append(" ".join(current_chunk))

    return chunks

# Formats speaker mapping for inclusion in the prompt
def format_speaker_map(mapping: dict) -> str:
    if not mapping:
        return ""
    lines = ["Here is the speaker mapping (Discord → Player → Character):"]
    for discord, info in mapping.items():
        player = info.get("player", "Unknown")
        character = info.get("character", "Unknown")
        lines.append(f"- {discord} = {player} ({character})")
    return "\n".join(lines)

# Sends a transcript chunk to the OpenAI GPT API and returns a summary
def summarize_chunk(chunk: str) -> str:
    mapping_note = format_speaker_map(speaker_map)

    messages = [
        {
            "role": "system",
            "content": "You are a helpful assistant who summarizes Dungeons & Dragons session transcripts."
        },
        {
            "role": "user",
            "content": f"""{mapping_note}

Here is a portion of a D&D session. Write a clear and detailed summary including major events, character actions, NPCs, quests, discoveries, and emotional or dramatic moments. Treat this as session notes for the DM.

Transcript:
{chunk}"""
        }
    ]

    response = client.chat.completions.create(
        model=openai_model,
        messages=messages,
        temperature=0.5
    )

    return response.choices[0].message.content.strip()

# === Main Function ===
# Load transcript, split into chunks, summarize, and save output
def main():
    print(f"Summarizing {input_path} into {output_path} using {openai_model}")

    with open(input_path, "r", encoding="utf-8") as f:
        full_transcript = f.read()

    chunks = chunk_text(full_transcript)
    print(f"Transcript split into {len(chunks)} chunk(s).")

    summaries = []
    for i, chunk in enumerate(chunks):
        print(f"Summarizing chunk {i + 1}/{len(chunks)}...")
        summary = summarize_chunk(chunk)
        summaries.append(f"--- Summary of Chunk {i + 1} ---\n{summary}\n")

    full_summary = "\n".join(summaries)

    with open(output_path, "w", encoding="utf-8") as f:
        f.write(full_summary)

    print(f"✅ Summary saved to: {output_path}")

if __name__ == "__main__":
    main()
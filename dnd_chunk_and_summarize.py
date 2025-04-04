"""
Step 1: Chunk + Summarize (No Final Summary Yet)
With logging of API input and output per chunk.
"""

import os
import json
from pathlib import Path
from openai import OpenAI
import tiktoken
import logging

# === Logging Setup ===
logging.basicConfig(
    filename="chunk_summarizer.log",
    level=logging.DEBUG,
    format='%(asctime)s [%(levelname)s] %(message)s'
)
logger = logging.getLogger("ChunkSummarizer")

# === Load from environment variables ===
input_path = os.environ.get('SUMMARY_INPUT')
summary_dir = os.environ.get('SUMMARY_CHUNK_DIR')
openai_key = os.environ.get('OPENAI_API_KEY')
openai_model = os.environ.get('OPENAI_MODEL')

if not all([input_path, summary_dir, openai_key, openai_model]):
    raise ValueError("Missing required environment variables. Check configuration.")

# === Load speaker map from config.json ===
speaker_map = {}
CONFIG_FILE = "config.json"
if os.path.exists(CONFIG_FILE):
    with open(CONFIG_FILE, 'r') as f:
        try:
            config = json.load(f)
            speaker_map = config.get("speaker_map", {})
        except json.JSONDecodeError:
            print("⚠️ Warning: Could not parse speaker_map from config.json")

# === Constants ===
CHUNK_SIZE = 3000
FINAL_SUMMARY_TOKEN_BUDGET = 30000
client = OpenAI()
encoding = tiktoken.encoding_for_model(openai_model)

def count_tokens(text: str) -> int:
    return len(encoding.encode(text))

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

def format_speaker_map(mapping: dict) -> str:
    if not mapping:
        return ""
    lines = ["Here is the speaker mapping (Discord → Player → Character):"]
    for discord, info in mapping.items():
        player = info.get("player", "Unknown")
        character = info.get("character", "Unknown")
        lines.append(f"- {discord} = {player} ({character})")
    return "\n".join(lines)

def summarize_chunk(chunk: str, index: int, token_budget: int) -> str:
    mapping_note = format_speaker_map(speaker_map)

    base_prompt = f"""{mapping_note}

You are a note-taking assistant for a Dungeons & Dragons campaign. 
Summarize the following transcript chunk for the Dungeon Master.

🎯 Focus on:
- Characters mentioned (PCs, NPCs) and their actions
- Locations, factions, or named places
- Quest progression, plot twists, and discoveries
- Emotional or dramatic beats that affect the story

📦 Skip or condense:
- Dice mechanics or rule talk
- Long combat turn-by-turn narration unless it's plot-relevant
- Unimportant small talk or jokes

📄 Format:
- Use clear, structured paragraphs or bullets
- Prioritize story continuity over line-by-line coverage

Transcript:
{chunk}"""

    def call_openai(prompt: str) -> str:
        response = client.chat.completions.create(
            model=openai_model,
            messages=[
                {"role": "system", "content": "You are a helpful assistant who summarizes Dungeons & Dragons session transcripts."},
                {"role": "user", "content": prompt}
            ],
            temperature=0.5
        )
        return response.choices[0].message.content.strip()

    logger.debug(f"=== Chunk {index} Prompt ===\n{base_prompt}\n")
    summary = call_openai(base_prompt)
    summary_tokens = count_tokens(summary)

    if summary_tokens > token_budget:
        logger.warning(f"⚠️ Chunk {index} summary exceeds token budget ({summary_tokens} > {token_budget}). Requesting condensed version.")

        condensed_prompt = f"""{mapping_note}

This summary is too long. Please rewrite it more concisely to fit within a strict token budget.

🪶 Keep only the most essential characters, locations, and plot beats.

Transcript:
{chunk}"""

        summary = call_openai(condensed_prompt)
        summary_tokens = count_tokens(summary)

        # Final fallback: trim it
        if summary_tokens > token_budget:
            logger.warning(f"⚠️ Chunk {index} fallback summary still exceeds token budget. Trimming to fit.")
            words = summary.split()
            trimmed_summary = []
            for word in words:
                trimmed_summary.append(word)
                if count_tokens(" ".join(trimmed_summary)) >= token_budget:
                    break
            summary = " ".join(trimmed_summary)

    logger.debug(f"=== Chunk {index} Final Summary ({summary_tokens} tokens) ===\n{summary}\n")
    return summary

def main():
    print(f"Chunking and summarizing {input_path} into {summary_dir} using {openai_model}")

    with open(input_path, "r", encoding="utf-8") as f:
        full_transcript = f.read()

    chunks = chunk_text(full_transcript)
    total_chunks = len(chunks)
    max_tokens_per_summary = FINAL_SUMMARY_TOKEN_BUDGET // total_chunks

    os.makedirs(summary_dir, exist_ok=True)

    total_tokens = 0
    for i, chunk in enumerate(chunks):
        logger.info(f"Summarizing chunk {i+1}/{total_chunks}")
        summary = summarize_chunk(chunk, i + 1, max_tokens_per_summary)

        with open(Path(summary_dir) / f"chunk_{i+1:02d}.txt", "w", encoding="utf-8") as f:
            f.write(summary)

        chunk_tokens = count_tokens(summary)
        total_tokens += chunk_tokens

    logger.info(f"✅ Chunk summaries saved to: {summary_dir}")
    logger.info(f"🔢 Total summary tokens: {total_tokens}")
    print(f"✅ Chunk summaries saved to: {summary_dir}")
    print(f"🔢 Total summary tokens: {total_tokens}")

if __name__ == "__main__":
    main()

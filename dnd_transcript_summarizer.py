# dnd_whole_transcript_summary.py

import os
import json
from pathlib import Path
from openai import OpenAI
import tiktoken
import logging

# === Logging Setup ===
logging.basicConfig(
    filename="whole_summary.log",
    level=logging.DEBUG,
    format='%(asctime)s [%(levelname)s] %(message)s'
)
logger = logging.getLogger("WholeTranscriptSummary")

# === Load Config ===
CONFIG_FILE = "config.json"
with open(CONFIG_FILE, "r") as f:
    config = json.load(f)

transcript_dir = Path(config["local_transcript_dir"])
summary_dir = Path(config["local_summary_dir"])
transcript_file = sorted(transcript_dir.glob("*transcript.txt"))[-1]  # Use latest transcript
summary_file = summary_dir / transcript_file.name.replace("transcript", "summary")

openai_key = config["openai_api_key"]
openai_model = "gpt-4o-mini"
speaker_map = config.get("speaker_map", {})

# === OpenAI Setup ===
os.environ["OPENAI_API_KEY"] = openai_key
client = OpenAI()
encoding = tiktoken.encoding_for_model(openai_model)

def count_tokens(text: str) -> int:
    return len(encoding.encode(text))

def format_speaker_map(mapping: dict) -> str:
    if not mapping:
        return ""
    lines = ["Here is the speaker mapping (Discord → Player → Character):"]
    for discord, info in mapping.items():
        player = info.get("player", "Unknown")
        character = info.get("character", "Unknown")
        lines.append(f"- {discord} = {player} ({character})")
    return "\n".join(lines)

def summarize_full_transcript(transcript: str) -> str:
    speaker_note = format_speaker_map(speaker_map)
    prompt = f"""
You are a professional campaign assistant trained to analyze transcripts from high-powered, narrative-rich Pathfinder 2e campaigns. 

You are generating exhaustive notes for the Dungeon Master. Prioritize clarity, evocative prose, and organization. Extract story beats, foreshadowing, unresolved threads, and social dynamics. Include anything the DM could use later for callbacks, emotional payoff, or plot advancement. If anything is ambiguous, highlight it for future clarification or elaboration.

Use the following structure exactly:

---

**🔮 Session Summary (3–5 Paragraphs)**  
Write a vivid, story-driven recap of the session as if telling the tale to another Dungeon Master. Capture tone, pacing, key decisions, emotional beats, and world events. Mention all main player characters by name, summarizing their personal arcs and contributions. Ensure there is a clear beginning, middle, and end to the session (if applicable).

---

**🎭 Key Character Actions and Roleplaying Moments**  
List 5–15 notable PC actions, grouped by character name. Highlight dramatic, clever, emotional, or funny moments. Use bold formatting for character names. Describe what they did and how it shaped the narrative or other PCs/NPCs.

---

**👥 Important NPCs and Encounters**  
List each significant NPC or monster encountered. Include:
- Name and role
- Personality traits or memorable dialogue
- Description of their relationship to the PCs (if any)
- Encounter outcome and lingering consequences

---

**📜 Major Plot Events and Developments**  
List 5–10 bullet points describing the session's most important story beats. Include:
- Quests started, advanced, or completed
- Mysteries uncovered
- Social, political, or academic conflicts
- Discoveries or revelations
- Consequences of player actions

---

**💔 Emotional or Dramatic Beats**  
In prose, recount emotionally charged or intense moments: bonding, conflict, sacrifice, vulnerability, or betrayal. Make it immersive, like you're writing a novel. Mention which characters were involved and what made the scene powerful.

---

**🧩 Unresolved Threads or Potential Hooks**  
List 5–8 questions or narrative threads the DM could explore later. Include:
- Ominous foreshadowing
- Strange or suspicious NPC behavior
- Items, visions, or events that remain unexplained
- Relationship drama or inner conflict
- Long-term consequences set in motion

---

**🎙️ Post Script: Funny Lines and Off-Topic Moments**  
In a casual tone, jot down any hilarious quotes, memes, off-topic discussions, or technical shenanigans that happened during the session. Capture the table’s personality and energy for future nostalgia.

---

{speaker_note}

Transcript:
{transcript}
"""

    messages = [
        {"role": "system", "content": "You are a professional D&D campaign assistant creating detailed session summaries from full transcripts."},
        {"role": "user", "content": prompt}
    ]

    logger.debug(f"=== Prompt Sent ===\n{prompt}\n")

    response = client.chat.completions.create(
        model=openai_model,
        messages=messages,
        temperature=0.3  # Lowered for better structure
    )

    result = response.choices[0].message.content.strip()
    logger.debug(f"=== Summary Returned ===\n{result}\n")
    return result

def main():
    print(f"📖 Reading transcript from: {transcript_file}")
    with open(transcript_file, "r", encoding="utf-8") as f:
        transcript = f.read()

    token_count = count_tokens(transcript)
    print(f"🔢 Token count: {token_count}")

    if token_count > 128000:
        raise RuntimeError("🚫 Transcript too large for gpt-4-0125-preview (128k token limit).")

    print(f"🧠 Summarizing session with {openai_model}...")
    summary = summarize_full_transcript(transcript)

    summary_dir.mkdir(parents=True, exist_ok=True)
    with open(summary_file, "w", encoding="utf-8") as f:
        f.write(summary)

    print(f"✅ Summary saved to: {summary_file}")
    logger.info(f"✅ Summary saved to: {summary_file}")

if __name__ == "__main__":
    main()

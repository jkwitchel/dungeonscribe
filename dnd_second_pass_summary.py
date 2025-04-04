"""
Step 2: Final Summary of Summaries
With logging of combined input and model response.
"""

import os
import json
from pathlib import Path
from openai import OpenAI
import tiktoken
import logging

# === Logging Setup ===
logging.basicConfig(
    filename="second_pass_summary.log",
    level=logging.DEBUG,
    format='%(asctime)s [%(levelname)s] %(message)s'
)
logger = logging.getLogger("SecondPass")

# === Load from environment variables ===
#summary_dir = os.environ.get('SUMMARY_CHUNK_DIR')
summary_dir = r'E:\SessionTranscripts\Summaries\2025-04-04 - chunks'
output_path = os.environ.get('SUMMARY_OUTPUT')
openai_key = os.environ.get('OPENAI_API_KEY')

## BYPASS ENV VAR FOR TESTING
openai_model = "gpt-4o"
#openai_model = os.environ.get('OPENAI_MODEL')

if not all([summary_dir, output_path, openai_key, openai_model]):
    raise ValueError("Missing required environment variables. Check configuration.")

# === OpenAI Setup ===
os.environ["OPENAI_API_KEY"] = openai_key
client = OpenAI()
encoding = tiktoken.encoding_for_model(openai_model)

def count_tokens(text: str) -> int:
    return len(encoding.encode(text))

def combine_summaries(folder: str) -> str:
    parts = []
    for file in sorted(Path(folder).glob("chunk_*.txt")):
        with open(file, "r", encoding="utf-8") as f:
            content = f.read().strip()
            parts.append(content)
    combined = "\n\n".join(parts)
    logger.debug(f"=== Combined Summary Text ===\n{combined}\n")
    logger.info(f"🔢 Total tokens in combined summary: {count_tokens(combined)}")
    return combined

def summarize_all(text: str) -> str:
    prompt = f"""
    You are summarizing a Dungeons & Dragons session for the Dungeon Master.

    Below are detailed chunk summaries from the session. Each chunk may include structured notes like: Characters, Locations, Quests, Dramatic Beats, and Conclusions.

    Please use this information to write a full and detailed session recap, organized in the following format:

    ---

    **Session Summary**  
    Begin with a 3–5 paragraph cinematic narrative that recounts the session events as a cohesive story. Focus on the major events, twists, character decisions, and turning points. This should read like a DM's recap or campaign journal entry.

    ---

    **Player Focus Summary**  
    Summarize what each player character did or focused on this session. Use the character names and highlight their motivations, challenges, and contributions to the party's progress.

    ---

    **Locations Visited**  
    List all named or noteworthy locations that the party visited or interacted with during the session. Include brief context for each (e.g., what happened there).

    ---

    **NPCs Encountered**  
    List all named NPCs mentioned in the session. Describe their role, relationship to the players, and any significant actions or dialogue.

    ---

    **Quests & Discoveries**  
    Note all quest updates, new leads, completed objectives, or important discoveries made during the session.

    ---

    **Dramatic & Emotional Moments**  
    Summarize the emotional highs and lows of the session. Highlight any roleplay-heavy scenes, character conflicts, unexpected consequences, or powerful thematic moments.

    ---

    Keep the tone clear and cinematic. Help the DM remember key beats and prep for follow-ups. Ensure the summary connects events to character arcs and campaign threads.

    Chunk Summaries:
    {text}
    """


    messages = [
        {"role": "system", "content": "You are a helpful assistant creating a high-level session summary from detailed summaries of a Dungeons & Dragons game."},
        {"role": "user", "content": prompt}
    ]
    logger.debug(f"=== Final Summary Prompt ===\n{prompt}\n")
    response = client.chat.completions.create(
        model=openai_model,
        messages=messages,
        temperature=0.5
    )
    summary = response.choices[0].message.content.strip()
    logger.debug(f"=== Final Summary Response ===\n{summary}\n")
    return summary

def main():
    print(f"Combining summaries from {summary_dir} into final summary at {output_path}")
    full_text = combine_summaries(summary_dir)
    final_summary = summarize_all(full_text)
    with open(output_path, "w", encoding="utf-8") as f:
        f.write(final_summary)
    print(f"✅ Final summary written to: {output_path}")
    logger.info(f"✅ Final summary written to: {output_path}")

if __name__ == "__main__":
    main()
import asyncio
import os
from edge_tts import Communicate
from pydub import AudioSegment

# --- CONFIGURATION ---
GERMAN_VOICE = "de-DE-KillianNeural"
ENGLISH_VOICE = "en-US-ChristopherNeural"

GERMAN_PAUSE_MS = 2500   # 2.5 second pause after German (Active Recall window)
ENGLISH_PAUSE_MS = 1500  # 1.5 second pause after English before next sentence

INPUT_FILE = "sentences.txt"
OUTPUT_MP3 = "german_podcast.mp3"


async def generate_tts(text: str, voice: str, filename: str):
    """Generates an MP3 audio file from text using edge-tts with retries."""
    for attempt in range(3):
        try:
            communicate = Communicate(text, voice)
            await communicate.save(filename)
            return True
        except Exception as e:
            if attempt == 2:
                print(f"Failed to generate audio for: '{text}' | Error: {e}")
                return False
            await asyncio.sleep(1)
    return False


async def main():
    if not os.path.exists(INPUT_FILE):
        print(f"Error: Please make sure '{INPUT_FILE}' exists in this folder!")
        return

    with open(INPUT_FILE, "r", encoding="utf-8") as f:
        lines = f.readlines()

    final_audio = AudioSegment.silent(duration=1000)
    german_pause = AudioSegment.silent(duration=GERMAN_PAUSE_MS)
    english_pause = AudioSegment.silent(duration=ENGLISH_PAUSE_MS)

    print("Generating podcast audio (this may take a minute)...")

    valid_sentences = 0

    for index, line in enumerate(lines):
        line = line.strip()
        
        # Skip empty lines or category headers
        if not line or line.startswith("===") or " - " not in line:
            continue

        german_text, english_text = line.split(" - ", 1)

        temp_de = f"temp_de_{index}.mp3"
        temp_en = f"temp_en_{index}.mp3"

        # Generate audio files via edge-tts
        success_de = await generate_tts(german_text, GERMAN_VOICE, temp_de)
        await asyncio.sleep(0.4) # Small delay to prevent server blocking
        
        success_en = await generate_tts(english_text, ENGLISH_VOICE, temp_en)
        await asyncio.sleep(0.4) # Small delay to prevent server blocking

        if not success_de or not success_en:
            continue

        # Load MP3 segments using pydub
        de_segment = AudioSegment.from_mp3(temp_de)
        en_segment = AudioSegment.from_mp3(temp_en)

        # Append to final audio: German -> 2.5s Pause -> English -> 1.5s Pause
        final_audio += de_segment + german_pause + en_segment + english_pause

        # Cleanup temporary files
        if os.path.exists(temp_de):
            os.remove(temp_de)
        if os.path.exists(temp_en):
            os.remove(temp_en)

        valid_sentences += 1
        print(f"[{valid_sentences}] Processed: {german_text}")

    # Export the final combined podcast MP3 file
    final_audio.export(OUTPUT_MP3, format="mp3")
    print(f"\nSuccess! Full podcast saved as '{OUTPUT_MP3}'")


if __name__ == "__main__":
    asyncio.run(main())
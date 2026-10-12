"""What this does: reads ElevenLabs' transcripts of a chapter's page recordings (one recording per
page, made from the narration script) and writes one tidy file with the time of every spoken word
on every page.

Delivery cues in square brackets ([urgent] and so on) come back from ElevenLabs as "words" lasting a
few hundredths of a second; they are not spoken, so they are kept apart under "cues". Names written
in phonetic symbols in the script (so the voice says them right) are turned back into plain
spelling, using the script's "phonetic_names" list (for example {"/məˈteɪi/": "Mattei"}).

A delivery cue can be several words long ("[in a warm, steady New Zealand accent]"); everything from
the word that opens the bracket to the word that closes it is the cue.

Use: python3 -I extract_word_times.py TRANSCRIPTS NARRATION_SCRIPT.json OUTPUT.json RECORDING_FOLDER
TRANSCRIPTS is either ElevenLabs' status reply (a .json file holding "transcripts") or a folder of
pageN-words.json files (ElevenLabs' word-time downloads). RECORDING_FOLDER is where pageN.mp3
lives (page1.mp3, page2.mp3 ...); the paths written into OUTPUT are the paths you give here, so
run the next step (assemble_chapter_narration.py) from the same folder.
Example: python3 -I narration-tools/extract_word_times.py examples/austerity-chapter-1/transcripts
         examples/austerity-chapter-1/narration-script.json word-times.json examples/austerity-chapter-1/recordings

After a long delivery cue, ElevenLabs can place the first spoken word up to 0.3 s after the voice
actually starts. So the first word's start is checked against the recording: if her voice begins
earlier, the first word is moved back to where her voice begins (the change is printed).
"""

import json
import os
import subprocess
import sys

import numpy

FIRST_WORD_TOLERANCE = 0.03   # seconds; smaller differences are left alone

PHONETIC_TO_PLAIN = {}  # filled from the narration script's "phonetic_names"


def plain_word(raw_text):
    for phonetic, plain in PHONETIC_TO_PLAIN.items():
        raw_text = raw_text.replace(phonetic, plain)
    return raw_text


def voice_start_seconds(recording_path):
    """Where the voice really begins: the first 10 ms stretch within 35 dB of the loudest one."""
    raw = subprocess.run(["ffmpeg", "-v", "error", "-i", recording_path, "-ac", "1", "-ar", "48000", "-f", "f32le", "-"],
                         check=True, capture_output=True).stdout
    samples = numpy.frombuffer(raw, dtype=numpy.float32)
    window = 480
    count = len(samples) // window
    loudness = 20 * numpy.log10(numpy.sqrt((samples[:count * window].reshape(count, window) ** 2).mean(axis=1)) + 1e-9)
    return float(numpy.argmax(loudness > loudness.max() - 35)) * 0.01


def main():
    if len(sys.argv) < 5:
        raise SystemExit("Use: extract_word_times.py TRANSCRIPTS NARRATION_SCRIPT.json OUTPUT.json RECORDING_FOLDER")
    transcripts_path, narration_script_path, output_path, recording_folder = sys.argv[1:5]
    with open(narration_script_path, encoding="utf-8") as handle:
        narration_script = json.load(handle)
    PHONETIC_TO_PLAIN.update(narration_script.get("phonetic_names", {}))
    script_pages = narration_script["pages"]
    if os.path.isdir(transcripts_path):
        transcripts = []
        for page in script_pages:
            with open(os.path.join(transcripts_path, f"page{page['page']}-words.json"), encoding="utf-8") as handle:
                transcripts.append({"text": page["text"], "words": json.load(handle)["words"]})
    else:
        with open(transcripts_path, encoding="utf-8") as handle:
            transcripts = json.load(handle)["transcripts"]
    if len(transcripts) != len(script_pages):
        raise SystemExit(f"{len(transcripts)} transcripts but {len(script_pages)} script pages")

    pages_out = []
    for script_page, transcript in zip(script_pages, transcripts):
        # The transcript of a recording made from text gives back the text itself; check it is this page.
        if transcript["text"].strip() != script_page["text"].strip():
            raise SystemExit(f"page {script_page['page']}: transcript text does not match the script")
        spoken_words = []
        cues = []
        inside_cue = False
        for entry in transcript["words"]:
            if entry.get("type") != "word":
                continue
            text = entry["text"]
            record = {"text": plain_word(text), "start": round(entry["start"], 3), "end": round(entry["end"], 3)}
            if text.startswith("["):
                inside_cue = True
            if inside_cue:
                cues.append(record)
                if text.endswith("]"):
                    inside_cue = False
            else:
                spoken_words.append(record)
        recording_path = f"{recording_folder}/page{script_page['page']}.mp3"
        if os.path.exists(recording_path):
            voice_start = voice_start_seconds(recording_path)
            first = spoken_words[0]
            if first["start"] - voice_start > FIRST_WORD_TOLERANCE:
                print(f"page {script_page['page']:>2}: first word '{first['text']}' moved from {first['start']:.3f} s "
                      f"to {voice_start:.3f} s, where the voice begins")
                first["start"] = round(voice_start, 3)
        pages_out.append({
            "page": script_page["page"],
            "name": script_page["name"],
            "recording": recording_path,
            "generation_id": transcript.get("generation_id"),
            "spoken_duration_secs": transcript.get("spoken_duration_secs"),
            "cues": cues,
            "words": spoken_words,
        })

    output = {
        "note": "What this file is: the time (in seconds from the start of each page's recording) at "
                "which the narrator starts and ends every word. Made by narration-tools/extract_word_times.py "
                "from ElevenLabs' transcripts of the recordings. Delivery cues are listed apart; they are not spoken.",
        "pages": pages_out,
    }
    with open(output_path, "w", encoding="utf-8") as handle:
        json.dump(output, handle, ensure_ascii=False, indent=1)

    for page in pages_out:
        longest_cue = max((cue["end"] - cue["start"] for cue in page["cues"]), default=0)
        print(f"page {page['page']:>2}: {len(page['words'])} spoken words, {len(page['cues'])} cues "
              f"(longest cue {longest_cue:.3f} s), last word ends {page['words'][-1]['end']:.2f} s")


if __name__ == "__main__":
    main()

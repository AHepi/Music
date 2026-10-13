"""What this does: lays a chapter's page recordings end to end on one chapter timeline, with a planned
pause between pages, and writes two things:

  1. the narration track (a WAV file at 48,000 samples a second), each page turned to the same
     loudness (-16 LUFS) by a plain volume change, so no page sounds louder than the next;
  2. the chapter timeline (JSON): where each page's recording starts and where every word falls,
     in seconds from the start of the chapter. The paper film reads it, so pictures land on words.

The pause between pages is measured from the end of one page's last word to the start of the next
page's first word: 1.4 seconds unless you give your own with --pauses (one number per gap, in
order: after page 1, after page 2, ...). Chapter 1 of the austerity explainer used
--pauses 1.7,1.4,1.1,1.5,1.5,1.3,1.5,1.4,1.6 (longer where the page turn has more to do).

Use: python3 -I assemble_chapter_narration.py WORD_TIMES.json OUT_NARRATION.wav OUT_TIMELINE.json [--pauses a,b,c,...]
(run from the folder the recording paths in WORD_TIMES.json start from, usually the kit folder)
"""

import json
import math
import subprocess
import sys

import numpy

SAMPLE_RATE = 48000
FRAMES_PER_SECOND = 30
VOICE_LOUDNESS = -16.0
FIRST_WORD_AT = 1.08          # seconds of music before Malina's first word
TAIL_AFTER_LAST_WORD = 4.0    # seconds after her last word: the last mark lands, the music fades
# pause (seconds) between the last word of page N and the first word of page N + 1, unless --pauses is given
DEFAULT_PAUSE = 1.4


def decode_to_samples(path):
    """Decode an audio file to mono float samples at SAMPLE_RATE."""
    raw = subprocess.run(
        ["ffmpeg", "-hide_banner", "-loglevel", "error", "-i", path, "-ac", "1", "-ar", str(SAMPLE_RATE), "-f", "f32le", "-"],
        check=True, capture_output=True).stdout
    return numpy.frombuffer(raw, dtype=numpy.float32).copy()


def measured_loudness(path):
    report = subprocess.run(["ffmpeg", "-hide_banner", "-nostats", "-i", path, "-af", "ebur128", "-f", "null", "-"],
                            capture_output=True, text=True).stderr
    lines = [line for line in report.splitlines() if line.strip().startswith("I:")]
    return float(lines[-1].split()[1])


def main():
    arguments = sys.argv[1:]
    pauses_given = None
    if "--pauses" in arguments:
        at = arguments.index("--pauses")
        pauses_given = [float(value) for value in arguments[at + 1].split(",")]
        arguments = arguments[:at] + arguments[at + 2:]
    word_times_path, narration_out, timeline_out = arguments[:3]
    with open(word_times_path, encoding="utf-8") as handle:
        pages = json.load(handle)["pages"]
    if pauses_given is not None and len(pauses_given) != len(pages) - 1:
        raise SystemExit(f"--pauses needs {len(pages) - 1} numbers (one per gap between pages), got {len(pauses_given)}")
    PAUSES_AFTER_PAGE = {page["page"]: (pauses_given[i] if pauses_given else DEFAULT_PAUSE) for i, page in enumerate(pages[:-1])}

    # place each page: its first word comes PAUSES_AFTER_PAGE after the previous page's last word
    placements = []
    previous_last_word_end = None
    for page in pages:
        first_word_in_file = page["words"][0]["start"]
        last_word_end_in_file = page["words"][-1]["end"]
        if previous_last_word_end is None:
            first_word_at = FIRST_WORD_AT
        else:
            first_word_at = previous_last_word_end + PAUSES_AFTER_PAGE[page["page"] - 1]
        recording_starts_at = first_word_at - first_word_in_file
        placements.append({
            "page": page["page"], "name": page["name"], "recording": page["recording"],
            "recording_starts_at": round(recording_starts_at, 3),
            "first_word_at": round(first_word_at, 3),
            "last_word_end_at": round(recording_starts_at + last_word_end_in_file, 3),
            "words": [{"text": w["text"], "start": round(recording_starts_at + w["start"], 3),
                       "end": round(recording_starts_at + w["end"], 3)} for w in page["words"]],
        })
        previous_last_word_end = recording_starts_at + last_word_end_in_file

    chapter_seconds = previous_last_word_end + TAIL_AFTER_LAST_WORD
    chapter_frames = math.ceil(chapter_seconds * FRAMES_PER_SECOND)
    chapter_seconds = chapter_frames / FRAMES_PER_SECOND

    # build the narration track
    track = numpy.zeros(int(round(chapter_seconds * SAMPLE_RATE)) + SAMPLE_RATE, dtype=numpy.float64)
    for placement in placements:
        samples = decode_to_samples(placement["recording"])
        gain_db = VOICE_LOUDNESS - measured_loudness(placement["recording"])
        placement["gain_db"] = round(gain_db, 2)
        start_sample = int(round(placement["recording_starts_at"] * SAMPLE_RATE))
        end_sample = start_sample + len(samples)
        if start_sample < 0 or end_sample > len(track):
            raise SystemExit(f"page {placement['page']} does not fit on the timeline")
        if numpy.any(track[start_sample:end_sample] != 0):
            raise SystemExit(f"page {placement['page']} overlaps the page before it")
        track[start_sample:end_sample] += samples * (10 ** (gain_db / 20))
    track = track[: int(round(chapter_seconds * SAMPLE_RATE))]
    # Saved as floating-point samples, which may go a little past full scale without damage; the
    # final mix sets the overall level and its limiter keeps the delivered file under clipping.
    peak = float(numpy.max(numpy.abs(track)))
    pcm = track.astype("<f4").tobytes()
    subprocess.run(["ffmpeg", "-hide_banner", "-loglevel", "error", "-y", "-f", "f32le", "-ar", str(SAMPLE_RATE), "-ac", "1",
                    "-i", "-", "-c:a", "pcm_f32le", narration_out], input=pcm, check=True)

    timeline = {
        "note": "What this file is: a chapter's timeline. Every time is in seconds from the start of the "
                "chapter. Made by narration-tools/assemble_chapter_narration.py from the word times file.",
        "frames_per_second": FRAMES_PER_SECOND,
        "chapter_seconds": chapter_seconds,
        "chapter_frames": chapter_frames,
        "first_word_at": FIRST_WORD_AT,
        "pauses_after_page": PAUSES_AFTER_PAGE,
        "tail_after_last_word": TAIL_AFTER_LAST_WORD,
        "voice_loudness_lufs": VOICE_LOUDNESS,
        "narration_peak": round(peak, 3),
        "pages": placements,
    }
    with open(timeline_out, "w", encoding="utf-8") as handle:
        json.dump(timeline, handle, ensure_ascii=False, indent=1)

    print(f"chapter: {chapter_seconds:.2f} s = {chapter_frames} frames; narration peak {peak:.3f}")
    for placement in placements:
        print(f"page {placement['page']:>2}: recording at {placement['recording_starts_at']:7.3f} s, "
              f"words {placement['first_word_at']:7.3f} to {placement['last_word_end_at']:7.3f} s, gain {placement['gain_db']:+.2f} dB")


if __name__ == "__main__":
    main()

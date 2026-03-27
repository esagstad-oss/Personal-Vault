"""
YouTube Video Transcriber & Summarizer
Uses youtube-transcript-api to fetch captions (no download needed).

Usage:
    python transcribe_youtube.py <youtube_url_or_video_id>

Requirements:
    pip install youtube-transcript-api
"""

import sys
import re
import textwrap


def extract_video_id(url_or_id: str) -> str:
    """Extract video ID from a YouTube URL or return as-is if already an ID."""
    patterns = [
        r"(?:v=)([A-Za-z0-9_-]{11})",
        r"(?:youtu\.be/)([A-Za-z0-9_-]{11})",
        r"(?:embed/)([A-Za-z0-9_-]{11})",
    ]
    for pattern in patterns:
        match = re.search(pattern, url_or_id)
        if match:
            return match.group(1)
    # Assume it's already a video ID
    return url_or_id.strip()


def fetch_transcript(video_id: str) -> list[dict]:
    """Fetch transcript entries for a YouTube video."""
    try:
        from youtube_transcript_api import YouTubeTranscriptApi
        from youtube_transcript_api._errors import NoTranscriptFound, TranscriptsDisabled
    except ImportError:
        print("ERROR: youtube-transcript-api is not installed.")
        print("Run: pip install youtube-transcript-api")
        sys.exit(1)

    api = YouTubeTranscriptApi()
    try:
        # Try English first, then fall back to any available language
        transcript_list = api.list(video_id)
        try:
            transcript = transcript_list.find_transcript(["en"])
        except NoTranscriptFound:
            transcript = next(iter(transcript_list))
            print(f"No English transcript found. Using: {transcript.language} ({transcript.language_code})")
        fetched = transcript.fetch()
        return [{'start': s.start, 'duration': s.duration, 'text': s.text} for s in fetched]
    except TranscriptsDisabled:
        print(f"ERROR: Transcripts are disabled for video '{video_id}'.")
        sys.exit(1)


def format_transcript(entries: list[dict]) -> str:
    """Format transcript entries into readable text with timestamps."""
    lines = []
    for entry in entries:
        start = entry["start"]
        minutes = int(start // 60)
        seconds = int(start % 60)
        timestamp = f"[{minutes:02d}:{seconds:02d}]"
        text = entry["text"].replace("\n", " ").strip()
        lines.append(f"{timestamp} {text}")
    return "\n".join(lines)


def build_plain_text(entries: list[dict]) -> str:
    """Build a clean plain-text transcript (no timestamps)."""
    words = " ".join(e["text"].replace("\n", " ").strip() for e in entries)
    return "\n".join(textwrap.wrap(words, width=100))


def main():
    if len(sys.argv) < 2:
        print("Usage: python transcribe_youtube.py <youtube_url_or_video_id>")
        sys.exit(1)

    input_arg = sys.argv[1]
    video_id = extract_video_id(input_arg)
    print(f"Video ID: {video_id}")
    print(f"Fetching transcript...\n")

    entries = fetch_transcript(video_id)
    total_duration = entries[-1]["start"] + entries[-1].get("duration", 0)
    minutes = int(total_duration // 60)
    seconds = int(total_duration % 60)

    print(f"=== TRANSCRIPT ({len(entries)} segments, ~{minutes}m {seconds}s) ===\n")
    timestamped = format_transcript(entries)
    print(timestamped)

    print("\n=== PLAIN TEXT ===\n")
    plain = build_plain_text(entries)
    print(plain)

    # Save output
    output_file = f"transcript_{video_id}.txt"
    with open(output_file, "w", encoding="utf-8") as f:
        f.write(f"Video ID: {video_id}\n")
        f.write(f"URL: https://www.youtube.com/watch?v={video_id}\n")
        f.write(f"Duration: ~{minutes}m {seconds}s\n\n")
        f.write("=== TIMESTAMPED TRANSCRIPT ===\n\n")
        f.write(timestamped)
        f.write("\n\n=== PLAIN TEXT ===\n\n")
        f.write(plain)

    print(f"\nSaved to: {output_file}")


if __name__ == "__main__":
    main()

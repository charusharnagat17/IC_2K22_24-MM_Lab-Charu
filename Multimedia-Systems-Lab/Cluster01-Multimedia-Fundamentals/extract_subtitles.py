"""
Subtitle Extractor
------------------
This script checks if a given media file (video/audio container) contains
embedded subtitle/text streams, extracts existing subtitle tracks (WITHOUT generating
speech-to-text subtitles), and saves them into standard .srt subtitle files.

Usage:
    python extract_subtitles.py <input_media_file> [output_srt_file]
"""

import sys
import os
import subprocess
from pymediainfo import MediaInfo

# Ensure UTF-8 output encoding for terminal printing
if hasattr(sys.stdout, 'reconfigure'):
    try:
        sys.stdout.reconfigure(encoding='utf-8')
    except Exception:
        pass


def find_ffmpeg():
    """Finds available ffmpeg executable on the system or inside imageio_ffmpeg."""
    try:
        import imageio_ffmpeg
        exe = imageio_ffmpeg.get_ffmpeg_exe()
        if exe and os.path.exists(exe):
            return exe
    except ImportError:
        pass

    # Fallback to system PATH
    try:
        res = subprocess.run(["ffmpeg", "-version"], stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
        if res.returncode == 0:
            return "ffmpeg"
    except Exception:
        pass

    return None


def get_subtitle_tracks(file_path):
    """
    Inspects media file using MediaInfo and returns a list of subtitle track info dictionaries.
    """
    try:
        media_info = MediaInfo.parse(file_path)
    except Exception as e:
        print(f"Error parsing file with MediaInfo: {e}")
        return []

    sub_tracks = []
    text_count = 0
    for track in media_info.tracks:
        if track.track_type in ['Text', 'Subtitle']:
            data = track.to_data()
            sub_tracks.append({
                'index': text_count,
                'format': data.get('format', 'Unknown'),
                'codec_id': data.get('codec_id', 'Unknown'),
                'language': data.get('language', 'Unknown'),
                'title': data.get('title', data.get('handler_name', 'Subtitle Track'))
            })
            text_count += 1

    return sub_tracks


def extract_subtitles(input_path, output_srt_path=None):
    """
    Checks for available subtitle streams and extracts them into .srt file(s).
    """
    if not os.path.exists(input_path):
        print(f"[ERROR] Input file '{input_path}' does not exist.")
        return False

    abs_input = os.path.abspath(input_path)
    print("=" * 80)
    print(f" SUBTITLE EXTRACTION ")
    print("=" * 80)
    print(f"Input File: {abs_input}")

    # Step 1: Detect embedded subtitle tracks using MediaInfo
    sub_tracks = get_subtitle_tracks(input_path)

    if not sub_tracks:
        print("\n[INFO] No embedded subtitle/text streams found in this file.")
        print("[NOTE] As per requirements, subtitle generation (speech-to-text) is disabled.")
        print("       No .srt file was created.")
        print("=" * 80)
        return False

    print(f"\n[+] Found {len(sub_tracks)} subtitle stream(s):")
    for st in sub_tracks:
        print(f"    - Track #{st['index']}: Format={st['format']}, Language={st['language']}, Title={st['title']}")

    # Step 2: Locate FFmpeg executable for stream extraction
    ffmpeg_exe = find_ffmpeg()
    if not ffmpeg_exe:
        print("\n[ERROR] FFmpeg executable could not be found to extract subtitle stream.")
        print("        Please ensure 'imageio_ffmpeg' is installed or 'ffmpeg' is on system PATH.")
        return False

    # Determine default output path if not specified
    base_name = os.path.splitext(abs_input)[0]

    extracted_files = []
    for st in sub_tracks:
        idx = st['index']
        if output_srt_path:
            if len(sub_tracks) == 1:
                target_srt = output_srt_path
            else:
                base_out, ext = os.path.splitext(output_srt_path)
                target_srt = f"{base_out}_track{idx+1}{ext if ext else '.srt'}"
        else:
            if len(sub_tracks) == 1:
                target_srt = f"{base_name}_subtitles.srt"
            else:
                target_srt = f"{base_name}_subtitles_track{idx+1}.srt"

        print(f"\n[+] Extracting Subtitle Track #{idx} to: {target_srt}")

        # Construct FFmpeg command to extract subtitle track to SRT format
        cmd = [
            ffmpeg_exe,
            "-y",  # overwrite output without asking
            "-i", abs_input,
            "-map", f"0:s:{idx}",
            target_srt
        ]

        try:
            res = subprocess.run(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
            if res.returncode == 0 and os.path.exists(target_srt) and os.path.getsize(target_srt) > 0:
                print(f"[SUCCESS] Saved subtitle file: {target_srt} ({os.path.getsize(target_srt)} bytes)")
                extracted_files.append(target_srt)
            else:
                print(f"[ERROR] Failed to extract track #{idx}. FFmpeg Error:\n{res.stderr}")
        except Exception as e:
            print(f"[ERROR] Subprocess execution error: {e}")

    print("\n" + "=" * 80)
    if extracted_files:
        print(f" Extracted {len(extracted_files)} subtitle file(s) successfully.")
    else:
        print(" Subtitle extraction failed.")
    print("=" * 80)
    return bool(extracted_files)


def main():
    if len(sys.argv) > 1:
        input_file = sys.argv[1]
        output_srt = sys.argv[2] if len(sys.argv) > 2 else None
    else:
        # Prompt user or use default dataset files for demonstration
        default_file = os.path.join("..", "datasets", "voiceover_with_subtitles.mp4")
        if not os.path.exists(default_file):
            default_file = os.path.join("..", "datasets", "voiceover.mp4")

        print("No input file provided via command line.")
        user_input = input(f"Enter path to media file (press Enter for default '{default_file}'): ").strip()
        input_file = user_input if user_input else default_file
        output_srt = None

    input_file = input_file.strip('"').strip("'")
    extract_subtitles(input_file, output_srt)


if __name__ == "__main__":
    main()

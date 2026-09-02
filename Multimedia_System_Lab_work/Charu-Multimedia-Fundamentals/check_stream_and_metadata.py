# This is Charu's Code
"""
Media Stream Checker & Metadata Extractor
-----------------------------------------
This script checks if a given multimedia file contains video stream(s),
audio stream(s), or subtitle/text stream(s), and prints all extracted
metadata about the file to the terminal.

Usage:
    python check_stream_and_metadata.py <path_to_media_file>
"""

import sys
import os
from pymediainfo import MediaInfo

# Ensure UTF-8 output encoding for terminal printing
if hasattr(sys.stdout, 'reconfigure'):
    try:
        sys.stdout.reconfigure(encoding='utf-8')
    except Exception:
        pass


def format_bytes(size_bytes):
    """Format bytes to human readable string (KB, MB, GB)."""
    try:
        size = float(size_bytes)
    except (ValueError, TypeError):
        return "Unknown"
    
    for unit in ['B', 'KB', 'MB', 'GB', 'TB']:
        if size < 1024.0:
            return f"{size:.2f} {unit}"
        size /= 1024.0
    return f"{size:.2f} PB"


def format_duration(ms):
    """Format duration in milliseconds to HH:MM:SS.mmm format."""
    try:
        ms = float(ms)
    except (ValueError, TypeError):
        return "Unknown"
    
    seconds = ms / 1000.0
    hrs = int(seconds // 3600)
    mins = int((seconds % 3600) // 60)
    secs = seconds % 60
    if hrs > 0:
        return f"{hrs:02d}:{mins:02d}:{secs:06.3f}"
    else:
        return f"{mins:02d}:{secs:06.3f}"


def inspect_media_file(file_path):
    """Parses media file and prints stream classification and all extracted metadata."""
    if not os.path.exists(file_path):
        print(f"Error: File '{file_path}' does not exist.")
        return

    print("=" * 80)
    print(f" ANALYZING MEDIA FILE: {os.path.abspath(file_path)}")
    print("=" * 80)

    try:
        media_info = MediaInfo.parse(file_path)
    except Exception as e:
        print(f"Error parsing media file with MediaInfo: {e}")
        return

    tracks = media_info.tracks
    if not tracks:
        print("No tracks or metadata found in file.")
        return

    # Categorize tracks
    video_tracks = [t for t in tracks if t.track_type == 'Video']
    audio_tracks = [t for t in tracks if t.track_type == 'Audio']
    text_tracks = [t for t in tracks if t.track_type in ['Text', 'Subtitle']]
    general_tracks = [t for t in tracks if t.track_type == 'General']
    other_tracks = [t for t in tracks if t.track_type not in ['Video', 'Audio', 'Text', 'Subtitle', 'General']]

    # Determine overall stream type classification
    print("\n" + " STREAM CLASSIFICATION SUMMARY ".center(80, "-"))
    has_video = len(video_tracks) > 0
    has_audio = len(audio_tracks) > 0
    has_subtitles = len(text_tracks) > 0

    if has_video and has_audio:
        stream_type_desc = "VIDEO & AUDIO STREAM (Container contains both Video and Audio)"
    elif has_video:
        stream_type_desc = "VIDEO STREAM ONLY (No audio track found)"
    elif has_audio:
        stream_type_desc = "AUDIO STREAM ONLY (No video track found)"
    elif has_subtitles:
        stream_type_desc = "SUBTITLE / TEXT STREAM ONLY"
    else:
        stream_type_desc = "OTHER / UNKNOWN MEDIA STREAM"

    print(f"[+] Media Classification: {stream_type_desc}")
    print(f"[+] Video Stream Count  : {len(video_tracks)}")
    print(f"[+] Audio Stream Count  : {len(audio_tracks)}")
    print(f"[+] Subtitle Stream Count: {len(text_tracks)}")
    print(f"[+] Other Track Count   : {len(other_tracks)}")

    # Print Formatted Key Details
    print("\n" + " DETAILED TRACK OVERVIEW ".center(80, "-"))
    for idx, track in enumerate(tracks, start=1):
        print(f"\n--- Track #{idx} [{track.track_type}] ---")
        data = track.to_data()

        # Display highlights based on track type
        if track.track_type == 'General':
            print(f"  * Format              : {data.get('format', 'N/A')}")
            print(f"  * File Size           : {format_bytes(data.get('file_size'))}")
            print(f"  * Duration            : {format_duration(data.get('duration'))}")
            print(f"  * Overall Bit Rate    : {data.get('overall_bit_rate', 'N/A')} bps")
            print(f"  * Codec ID            : {data.get('codec_id', 'N/A')}")

        elif track.track_type == 'Video':
            print(f"  * Format / Codec      : {data.get('format', 'N/A')} ({data.get('codec_id', 'N/A')})")
            print(f"  * Resolution          : {data.get('width', 'N/A')} x {data.get('height', 'N/A')} pixels")
            print(f"  * Aspect Ratio        : {data.get('display_aspect_ratio', 'N/A')}")
            print(f"  * Frame Rate (FPS)    : {data.get('frame_rate', 'N/A')} fps")
            print(f"  * Bit Rate            : {data.get('bit_rate', 'N/A')} bps")
            print(f"  * Duration            : {format_duration(data.get('duration'))}")
            print(f"  * Color Space         : {data.get('color_space', 'N/A')} ({data.get('chroma_subsampling', 'N/A')})")
            print(f"  * Bit Depth           : {data.get('bit_depth', 'N/A')} bits")

        elif track.track_type == 'Audio':
            print(f"  * Format / Codec      : {data.get('format', 'N/A')} ({data.get('codec_id', 'N/A')})")
            print(f"  * Channels            : {data.get('channel_s', 'N/A')} channel(s) ({data.get('channel_positions', 'N/A')})")
            print(f"  * Sampling Rate       : {data.get('sampling_rate', 'N/A')} Hz")
            print(f"  * Bit Rate            : {data.get('bit_rate', 'N/A')} bps ({data.get('bit_rate_mode', 'N/A')})")
            print(f"  * Duration            : {format_duration(data.get('duration'))}")
            print(f"  * Language            : {data.get('language', 'N/A')}")

        elif track.track_type in ['Text', 'Subtitle']:
            print(f"  * Subtitle Format     : {data.get('format', 'N/A')} ({data.get('codec_id', 'N/A')})")
            print(f"  * Language            : {data.get('language', 'N/A')}")
            print(f"  * Title / Handler     : {data.get('title', data.get('handler_name', 'N/A'))}")

        else:
            print(f"  * Format              : {data.get('format', 'N/A')}")

    # Print ALL Extracted Raw Metadata Fields
    print("\n" + " ALL EXTRACTED METADATA (RAW KEY-VALUE ATTRIBUTES) ".center(80, "="))
    for idx, track in enumerate(tracks, start=1):
        print(f"\n[ Track #{idx}: {track.track_type} ]")
        data = track.to_data()
        # Sort keys for consistent display
        for key in sorted(data.keys()):
            val = data[key]
            if val is not None and str(val).strip() != "":
                print(f"  {key:<35}: {val}")

    print("\n" + "=" * 80)
    print(" Metadata extraction complete.")
    print("=" * 80)


def main():
    if len(sys.argv) > 1:
        file_path = sys.argv[1]
    else:
        # Default dataset file for demonstration if none passed
        default_file = os.path.join("..", "datasets", "voiceover.mp4")
        if not os.path.exists(default_file):
            default_file = os.path.join("..", "datasets", "Afternoon_Window.mp3")
            
        print("No input file provided via command line.")
        user_input = input(f"Enter path to media file (press Enter for default '{default_file}'): ").strip()
        file_path = user_input if user_input else default_file

    # Strip quotes if user dragged and dropped file into terminal
    file_path = file_path.strip('"').strip("'")
    inspect_media_file(file_path)


if __name__ == "__main__":
    main()
# This is Charu's Code

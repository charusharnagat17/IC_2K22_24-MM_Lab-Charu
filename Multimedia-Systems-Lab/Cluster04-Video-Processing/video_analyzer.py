"""
Video Metadata Analyzer
-----------------------
Extracts and displays comprehensive video, audio, container, and stream metadata
from video files in a formatted report.

Usage:
    python video_analyzer.py [path_to_video_file]
"""

import sys
import os
import cv2
from pymediainfo import MediaInfo

# Ensure UTF-8 output encoding for terminal compatibility
if hasattr(sys.stdout, 'reconfigure'):
    try:
        sys.stdout.reconfigure(encoding='utf-8')
    except Exception:
        pass


def format_file_size(size_bytes):
    """Format file size in bytes to a human-readable string (KB, MB, GB)."""
    try:
        size = float(size_bytes)
    except (ValueError, TypeError):
        return "N/A"

    if size < 1024:
        return f"{size_bytes} bytes"
    elif size < 1024 * 1024:
        return f"{size / 1024:.2f} KB ({int(size):,} bytes)"
    elif size < 1024 * 1024 * 1024:
        return f"{size / (1024 * 1024):.2f} MB ({int(size):,} bytes)"
    else:
        return f"{size / (1024 * 1024 * 1024):.2f} GB ({int(size):,} bytes)"


def format_duration(ms):
    """Format duration in milliseconds to HH:MM:SS.mmm (and total seconds)."""
    try:
        ms = float(ms)
    except (ValueError, TypeError):
        return "N/A"

    total_seconds = ms / 1000.0
    hrs = int(total_seconds // 3600)
    mins = int((total_seconds % 3600) // 60)
    secs = total_seconds % 60

    if hrs > 0:
        time_str = f"{hrs:02d}:{mins:02d}:{secs:06.3f}"
    else:
        time_str = f"{mins:02d}:{secs:06.3f}"

    return f"{time_str} ({total_seconds:.2f} s)"


def format_bitrate(bps):
    """Format bitrate in bits per second to kbps/Mbps."""
    try:
        bps_val = float(bps)
    except (ValueError, TypeError):
        return "N/A"

    if bps_val >= 1_000_000:
        return f"{bps_val / 1_000_000:.2f} Mbps ({int(bps_val / 1000):,} kbps)"
    elif bps_val >= 1000:
        return f"{int(bps_val / 1000):,} kbps"
    else:
        return f"{int(bps_val)} bps"


def format_framerate(fps):
    """Format frame rate to FPS string."""
    try:
        fps_val = float(fps)
        return f"{fps_val:.3f} FPS" if fps_val % 1 != 0 else f"{fps_val:.1f} FPS"
    except (ValueError, TypeError):
        return "N/A"


def format_sampling_rate(hz):
    """Format sampling rate in Hz to kHz string."""
    try:
        hz_val = float(hz)
        if hz_val >= 1000:
            return f"{int(hz_val)} Hz ({hz_val / 1000:.1f} kHz)"
        return f"{int(hz_val)} Hz"
    except (ValueError, TypeError):
        return "N/A"


def analyze_video(video_path):
    """Parses video metadata and prints formatted report."""
    if not os.path.exists(video_path):
        print(f"Error: File '{video_path}' does not exist.")
        return

    file_name = os.path.basename(video_path)
    file_size = format_file_size(os.path.getsize(video_path))

    # Initialize metadata variables
    container = "N/A"
    duration = "N/A"

    # Video details
    resolution = "N/A"
    frame_rate = "N/A"
    video_bitrate = "N/A"
    video_codec = "N/A"

    # Audio details
    audio_codec = "N/A"
    channels = "N/A"
    sampling_rate = "N/A"
    audio_bitrate = "N/A"

    # Extra metadata tags
    extra_metadata = {}

    has_pymediainfo = False
    try:
        media_info = MediaInfo.parse(video_path)
        has_pymediainfo = True

        tracks = media_info.tracks
        general_track = next((t for t in tracks if t.track_type == 'General'), None)
        video_track = next((t for t in tracks if t.track_type == 'Video'), None)
        audio_track = next((t for t in tracks if t.track_type == 'Audio'), None)

        if general_track:
            container = general_track.format or general_track.commercial_name or "N/A"
            if general_track.duration:
                duration = format_duration(general_track.duration)
            if general_track.writing_application:
                extra_metadata['Writing Application'] = general_track.writing_application
            if general_track.file_creation_date__local:
                extra_metadata['File Created'] = general_track.file_creation_date__local

        if video_track:
            if video_track.width and video_track.height:
                resolution = f"{video_track.width} x {video_track.height}"
            if video_track.frame_rate:
                frame_rate = format_framerate(video_track.frame_rate)
            if video_track.bit_rate:
                video_bitrate = format_bitrate(video_track.bit_rate)
            elif general_track and general_track.overall_bit_rate:
                video_bitrate = format_bitrate(general_track.overall_bit_rate)
            
            video_codec = video_track.format or video_track.codec_id or "N/A"
            if video_track.format_profile:
                video_codec += f" ({video_track.format_profile})"

            if video_track.color_space:
                cs = video_track.color_space
                if video_track.chroma_subsampling:
                    cs += f" ({video_track.chroma_subsampling})"
                extra_metadata['Color Space'] = cs
            if video_track.bit_depth:
                extra_metadata['Bit Depth'] = f"{video_track.bit_depth} bits"
            if video_track.scan_type:
                extra_metadata['Scan Type'] = video_track.scan_type
            if video_track.display_aspect_ratio:
                extra_metadata['Aspect Ratio'] = video_track.display_aspect_ratio
            if video_track.writing_library:
                extra_metadata['Writing Library'] = video_track.writing_library

        if audio_track:
            audio_codec = audio_track.format or audio_track.codec_id or "N/A"
            if audio_track.format_additionalfeatures:
                audio_codec += f" ({audio_track.format_additionalfeatures})"
            
            if audio_track.channel_s:
                channels_val = audio_track.channel_s
                pos = f" ({audio_track.channel_positions})" if audio_track.channel_positions else ""
                channels = f"{channels_val}{pos}"
            
            if audio_track.sampling_rate:
                sampling_rate = format_sampling_rate(audio_track.sampling_rate)
            if audio_track.bit_rate:
                audio_bitrate = format_bitrate(audio_track.bit_rate)
            if audio_track.language:
                extra_metadata['Audio Language'] = audio_track.language

        # Collect text/subtitle tracks info
        text_tracks = [t for t in tracks if t.track_type in ['Text', 'Subtitle']]
        if text_tracks:
            sub_formats = [t.format for t in text_tracks if t.format]
            extra_metadata['Subtitle Tracks'] = f"{len(text_tracks)} ({', '.join(sub_formats)})"

    except Exception:
        has_pymediainfo = False

    # OpenCV Fallback for Video metadata if MediaInfo didn't capture or wasn't available
    cap = cv2.VideoCapture(video_path)
    if cap.isOpened():
        width = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
        height = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
        fps = cap.get(cv2.CAP_PROP_FPS)
        frame_count = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))

        if resolution == "N/A" and width > 0 and height > 0:
            resolution = f"{width} x {height}"
        if frame_rate == "N/A" and fps > 0:
            frame_rate = format_framerate(fps)
        if duration == "N/A" and fps > 0 and frame_count > 0:
            dur_sec = frame_count / fps
            duration = format_duration(dur_sec * 1000)

        # Codec FourCC fallback
        if video_codec == "N/A":
            fourcc_int = int(cap.get(cv2.CAP_PROP_FOURCC))
            fourcc = "".join([chr((fourcc_int >> 8 * i) & 0xFF) for i in range(4)]).strip()
            if fourcc:
                video_codec = fourcc

        extra_metadata['Total Frames'] = f"{frame_count:,}"
        cap.release()

    # Print Formatted Output Report
    print("================================")
    print("VIDEO METADATA REPORT")
    print("================================")
    print()
    print(f"{'File Name':<16}: {file_name}")
    print(f"{'File Size':<16}: {file_size}")
    print(f"{'Container':<16}: {container}")
    print(f"{'Duration':<16}: {duration}")
    print()
    print("VIDEO")
    print("--------------------------------")
    print(f"{'Resolution':<16}: {resolution}")
    print(f"{'Frame Rate':<16}: {frame_rate}")
    print(f"{'Bit Rate':<16}: {video_bitrate}")
    print(f"{'Codec':<16}: {video_codec}")
    print()
    print("AUDIO")
    print("--------------------------------")
    print(f"{'Codec':<16}: {audio_codec}")
    print(f"{'Channels':<16}: {channels}")
    print(f"{'Sampling Rate':<16}: {sampling_rate}")
    print(f"{'Bit Rate':<16}: {audio_bitrate}")
    print()
    print("METADATA")
    print("--------------------------------")
    if extra_metadata:
        for key, value in extra_metadata.items():
            print(f"{key:<16}: {value}")
    else:
        print("No additional metadata found.")


def main():
    if len(sys.argv) > 1:
        video_path = sys.argv[1]
    else:
        # Default fallback to dataset video file
        default_path = os.path.abspath(
            os.path.join(os.path.dirname(__file__), "..", "datasets", "voiceover.mp4")
        )
        if os.path.exists(default_path):
            video_path = default_path
        else:
            print("Usage: python video_analyzer.py <path_to_video_file>")
            sys.exit(1)

    # Strip surrounding quotes if dragged into terminal
    video_path = video_path.strip('"').strip("'")
    analyze_video(video_path)


if __name__ == "__main__":
    main()

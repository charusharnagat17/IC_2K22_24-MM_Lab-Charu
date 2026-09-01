"""
Audio Analyzer Module
---------------------
Extracts audio metadata including duration, codec, channels, sampling rate,
bitrate, and ID3/audio tags using pymediainfo.
"""

import os
from pymediainfo import MediaInfo
from file_utils import get_file_info


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
    """Format bitrate in bits per second to kbps string."""
    try:
        bps_val = float(bps)
        if bps_val >= 1000:
            return f"{int(bps_val / 1000):,} kbps"
        return f"{int(bps_val)} bps"
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


def analyze_audio(audio_path):
    """
    Analyzes an audio file and returns a structured dictionary of metadata.
    """
    file_info = get_file_info(audio_path)
    if not file_info["file_exists"]:
        return {
            "status": "error",
            "message": f"File '{audio_path}' does not exist.",
            "file_info": file_info
        }

    duration = "N/A"
    codec = "N/A"
    channels = "N/A"
    sampling_rate = "N/A"
    bit_rate = "N/A"
    bit_rate_mode = "N/A"
    container = "N/A"

    tags = {}

    try:
        media_info = MediaInfo.parse(audio_path)
        tracks = media_info.tracks

        general_track = next((t for t in tracks if t.track_type == 'General'), None)
        audio_track = next((t for t in tracks if t.track_type == 'Audio'), None)

        if general_track:
            container = general_track.format or general_track.commercial_name or "N/A"
            if general_track.duration and duration == "N/A":
                duration = format_duration(general_track.duration)
            if general_track.title:
                tags['Title'] = general_track.title
            if general_track.performer or general_track.artist:
                tags['Artist'] = general_track.performer or general_track.artist
            if general_track.album:
                tags['Album'] = general_track.album
            if general_track.genre:
                tags['Genre'] = general_track.genre
            if general_track.recorded_date:
                tags['Release Date'] = general_track.recorded_date

        if audio_track:
            codec = audio_track.format or audio_track.codec_id or "N/A"
            if audio_track.format_additionalfeatures:
                codec += f" ({audio_track.format_additionalfeatures})"

            if audio_track.duration:
                duration = format_duration(audio_track.duration)

            if audio_track.channel_s:
                ch_count = audio_track.channel_s
                pos = f" ({audio_track.channel_positions})" if audio_track.channel_positions else ""
                channels = f"{ch_count}{pos}"

            if audio_track.sampling_rate:
                sampling_rate = format_sampling_rate(audio_track.sampling_rate)

            if audio_track.bit_rate:
                bit_rate = format_bitrate(audio_track.bit_rate)

            if audio_track.bit_rate_mode:
                bit_rate_mode = audio_track.bit_rate_mode

            if audio_track.title and 'Title' not in tags:
                tags['Title'] = audio_track.title
            if audio_track.performer and 'Artist' not in tags:
                tags['Artist'] = audio_track.performer

    except Exception as e:
        tags['Error'] = f"Failed to parse audio metadata: {str(e)}"

    report_data = {
        "status": "success",
        "file_name": file_info["file_name"],
        "file_size": file_info["file_size_formatted"],
        "container": container,
        "duration": duration,
        "codec": codec,
        "channels": channels,
        "sampling_rate": sampling_rate,
        "bit_rate": bit_rate,
        "bit_rate_mode": bit_rate_mode,
        "tags": tags
    }

    return report_data

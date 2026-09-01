"""
Report Generator Module
-----------------------
Responsible for:
- Formatting and printing terminal metadata reports for Image, Audio, Video, and Unknown files.
- Exporting structured consolidated JSON reports to reports/report.json.
"""

import os
import json
from datetime import datetime


def print_image_report(data):
    """Prints terminal report for Image metadata."""
    print("================================")
    print("IMAGE METADATA REPORT")
    print("================================")
    print()
    print(f"{'File Name':<16}: {data.get('file_name', 'N/A')}")
    print(f"{'File Size':<16}: {data.get('file_size', 'N/A')}")
    print(f"{'File Format':<16}: {data.get('file_format', 'N/A')}")
    print(f"{'Width':<16}: {data.get('width', 0)} px")
    print(f"{'Height':<16}: {data.get('height', 0)} px")
    print(f"{'Resolution':<16}: {data.get('resolution', 'N/A')}")
    print(f"{'Color Mode':<16}: {data.get('color_mode', 'N/A')}")
    print()
    print("EXIF Metadata")
    print("--------------------------------")
    exif_sum = data.get('exif_summary', {})
    if exif_sum and any(v != 'N/A' for v in exif_sum.values()):
        print(f"{'Camera':<16}: {exif_sum.get('camera', 'N/A')}")
        print(f"{'Date Taken':<16}: {exif_sum.get('date_taken', 'N/A')}")
        print(f"{'Orientation':<16}: {exif_sum.get('orientation', 'N/A')}")
    else:
        print("No EXIF metadata found.")


def print_audio_report(data):
    """Prints terminal report for Audio metadata."""
    print("================================")
    print("AUDIO METADATA REPORT")
    print("================================")
    print()
    print(f"{'File Name':<16}: {data.get('file_name', 'N/A')}")
    print(f"{'File Size':<16}: {data.get('file_size', 'N/A')}")
    print(f"{'Container':<16}: {data.get('container', 'N/A')}")
    print(f"{'Duration':<16}: {data.get('duration', 'N/A')}")
    print()
    print("AUDIO")
    print("--------------------------------")
    print(f"{'Codec':<16}: {data.get('codec', 'N/A')}")
    print(f"{'Channels':<16}: {data.get('channels', 'N/A')}")
    print(f"{'Sampling Rate':<16}: {data.get('sampling_rate', 'N/A')}")
    print(f"{'Bit Rate':<16}: {data.get('bit_rate', 'N/A')}")
    print(f"{'Bit Rate Mode':<16}: {data.get('bit_rate_mode', 'N/A')}")
    print()
    print("METADATA")
    print("--------------------------------")
    tags = data.get('tags', {})
    if tags:
        for k, v in tags.items():
            print(f"{k:<16}: {v}")
    else:
        print("No additional metadata found.")


def print_video_report(data):
    """Prints terminal report for Video metadata."""
    video = data.get('video', {})
    audio = data.get('audio', {})
    meta = data.get('metadata', {})

    print("================================")
    print("VIDEO METADATA REPORT")
    print("================================")
    print()
    print(f"{'File Name':<16}: {data.get('file_name', 'N/A')}")
    print(f"{'File Size':<16}: {data.get('file_size', 'N/A')}")
    print(f"{'Container':<16}: {data.get('container', 'N/A')}")
    print(f"{'Duration':<16}: {data.get('duration', 'N/A')}")
    print()
    print("VIDEO")
    print("--------------------------------")
    print(f"{'Resolution':<16}: {video.get('resolution', 'N/A')}")
    print(f"{'Frame Rate':<16}: {video.get('frame_rate', 'N/A')}")
    print(f"{'Bit Rate':<16}: {video.get('bit_rate', 'N/A')}")
    print(f"{'Codec':<16}: {video.get('codec', 'N/A')}")
    print()
    print("AUDIO")
    print("--------------------------------")
    print(f"{'Codec':<16}: {audio.get('codec', 'N/A')}")
    print(f"{'Channels':<16}: {audio.get('channels', 'N/A')}")
    print(f"{'Sampling Rate':<16}: {audio.get('sampling_rate', 'N/A')}")
    print(f"{'Bit Rate':<16}: {audio.get('bit_rate', 'N/A')}")
    print()
    print("METADATA")
    print("--------------------------------")
    if meta:
        for k, v in meta.items():
            print(f"{k:<16}: {v}")
    else:
        print("No additional metadata found.")


def generate_console_report(media_type, data):
    """Dispatches the appropriate console report printer based on media type."""
    if data.get('status') != 'success':
        print(f"Error analyzing file: {data.get('message', 'Unknown error')}")
        return

    if media_type == 'IMAGE':
        print_image_report(data)
    elif media_type == 'AUDIO':
        print_audio_report(data)
    elif media_type == 'VIDEO':
        print_video_report(data)
    else:
        print("================================")
        print("UNSUPPORTED FILE REPORT")
        print("================================")
        print(f"File Name : {data.get('file_name', 'N/A')}")
        print(f"File Size : {data.get('file_size', 'N/A')}")
        print("Status    : Media type could not be identified or is unsupported.")


def save_json_report(media_type, data, output_path=None):
    """
    Saves the extracted metadata payload into a structured JSON report.
    Defaults to reports/report.json.
    """
    if output_path is None:
        base_dir = os.path.dirname(os.path.abspath(__file__))
        reports_dir = os.path.join(base_dir, "reports")
        os.makedirs(reports_dir, exist_ok=True)
        output_path = os.path.join(reports_dir, "report.json")

    payload = {
        "analysis_timestamp": datetime.now().isoformat(),
        "media_type": media_type,
        "report_data": data
    }

    try:
        os.makedirs(os.path.dirname(os.path.abspath(output_path)), exist_ok=True)
        with open(output_path, 'w', encoding='utf-8') as f:
            json.dump(payload, f, indent=4)
        print(f"\n[+] Consolidated report saved to: {os.path.abspath(output_path)}")
        return output_path
    except Exception as e:
        print(f"[-] Failed to save JSON report: {e}")
        return None

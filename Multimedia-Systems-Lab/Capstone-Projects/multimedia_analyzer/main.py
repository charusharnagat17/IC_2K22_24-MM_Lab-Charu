"""
Consolidated Multimedia Analyzer - Main Application
---------------------------------------------------
Accepts Image, Audio, or Video input files, identifies the file type automatically,
dispatches to the corresponding analyzer, prints formatted console reports,
and exports JSON reports to reports/report.json.

Usage:
    python main.py [path_to_media_file]
"""

import sys
import os

# Import project modules
from file_utils import file_exists, identify_file_type, get_file_info
from image_analyzer import analyze_image
from audio_analyzer import analyze_audio
from video_analyzer import analyze_video
from report_generator import generate_console_report, save_json_report

# Ensure UTF-8 output encoding for terminal printing
if hasattr(sys.stdout, 'reconfigure'):
    try:
        sys.stdout.reconfigure(encoding='utf-8')
    except Exception:
        pass


def run_analyzer(target_file):
    """
    Validates target file, detects media type, extracts metadata,
    displays console report, and saves JSON report.
    """
    target_file = target_file.strip('"').strip("'")

    if not file_exists(target_file):
        print(f"Error: File '{target_file}' does not exist or is not a valid file.")
        return False

    file_info = get_file_info(target_file)
    media_type = file_info["media_type"]

    print(f"\n[+] Analyzing file : {file_info['file_name']}")
    print(f"[+] Identified Type: {media_type}\n")

    if media_type == 'IMAGE':
        report_data = analyze_image(target_file)
    elif media_type == 'AUDIO':
        report_data = analyze_audio(target_file)
    elif media_type == 'VIDEO':
        report_data = analyze_video(target_file)
    else:
        report_data = {
            "status": "error",
            "message": f"Unsupported media type for file '{file_info['file_name']}'",
            "file_info": file_info
        }

    # Generate Console Report
    generate_console_report(media_type, report_data)

    # Save JSON Report
    save_json_report(media_type, report_data)
    return True


def prompt_user_for_sample(base_dir):
    """
    Prompts the user to select from available sample files when no command-line argument is passed.
    """
    samples_dir = os.path.join(base_dir, "samples")
    print("=" * 60)
    print(" CONSOLIDATED MULTIMEDIA ANALYZER")
    print("=" * 60)
    print("No input file provided via command line.")

    available_samples = []
    if os.path.exists(samples_dir):
        available_samples = [
            os.path.join("samples", f)
            for f in os.listdir(samples_dir)
            if os.path.isfile(os.path.join(samples_dir, f))
        ]

    if available_samples:
        print("\nAvailable Sample Files:")
        for idx, sample in enumerate(available_samples, 1):
            print(f"  [{idx}] {sample}")
        print("\nOptions:")
        print("  - Enter the number of a sample file above")
        print("  - Type/paste a custom file path")
        print("  - Press Enter to analyze default sample (samples/video.mp4)")

        user_input = input("\nSelect sample or enter path: ").strip()

        if not user_input:
            default_sample = os.path.join(samples_dir, "video.mp4")
            if os.path.exists(default_sample):
                return default_sample
            return os.path.join(samples_dir, available_samples[0]) if available_samples else ""
        elif user_input.isdigit() and 1 <= int(user_input) <= len(available_samples):
            return os.path.join(base_dir, available_samples[int(user_input) - 1])
        else:
            return user_input
    else:
        user_input = input("Enter path to Image, Audio, or Video file: ").strip()
        return user_input


def main():
    base_dir = os.path.dirname(os.path.abspath(__file__))

    if len(sys.argv) > 1:
        target_file = sys.argv[1]
    else:
        target_file = prompt_user_for_sample(base_dir)

    if not target_file:
        print("Error: No file path provided.")
        sys.exit(1)

    run_analyzer(target_file)


if __name__ == "__main__":
    main()

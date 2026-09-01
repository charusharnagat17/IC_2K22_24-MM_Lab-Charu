"""
Image Analyzer Module
---------------------
Extracts metadata from image files using PIL (Pillow) and OpenCV.
Extracts dimensions, resolution (DPI), format, color mode, and EXIF tags.
"""

import os
import cv2
from PIL import Image, ExifTags
from file_utils import get_file_info


def analyze_image(image_path):
    """
    Analyzes an image file and returns a structured dictionary of metadata.
    """
    file_info = get_file_info(image_path)
    if not file_info["file_exists"]:
        return {
            "status": "error",
            "message": f"File '{image_path}' does not exist.",
            "file_info": file_info
        }

    # Primary analysis using PIL
    width = 0
    height = 0
    file_format = "Unknown"
    color_mode = "Unknown"
    resolution = "N/A"
    exif_data = {}

    try:
        with Image.open(image_path) as pil_img:
            width, height = pil_img.size
            file_format = pil_img.format if pil_img.format else "Unknown"
            color_mode = pil_img.mode
            dpi = pil_img.info.get('dpi')
            if dpi:
                resolution = f"{round(dpi[0])} x {round(dpi[1])} DPI"

            exif = pil_img.getexif()
            if exif:
                for tag_id, val in exif.items():
                    tag = ExifTags.TAGS.get(tag_id, tag_id)
                    exif_data[str(tag)] = str(val)
                for ifd_id in ExifTags.IFD:
                    try:
                        ifd = exif.get_ifd(ifd_id)
                        if ifd:
                            for tag_id, val in ifd.items():
                                tag = ExifTags.TAGS.get(
                                    tag_id,
                                    ExifTags.GPSTAGS.get(tag_id, tag_id)
                                )
                                exif_data[str(tag)] = str(val)
                    except Exception:
                        pass
    except Exception as e:
        # Fallback to OpenCV if PIL fails
        img = cv2.imread(image_path)
        if img is not None:
            height, width = img.shape[:2]
            color_mode = f"BGR ({img.shape[2]} channels)" if len(img.shape) > 2 else "Grayscale"
            file_format = file_info["extension"].replace('.', '').upper()

    # Formatted Camera & Date info from EXIF if available
    camera = "N/A"
    date_taken = "N/A"
    orientation = "N/A"

    if exif_data:
        make = exif_data.get('Make', '').strip()
        model = exif_data.get('Model', '').strip()
        if make and model:
            camera = model if model.startswith(make) else f"{make} {model}"
        else:
            camera = make or model or "N/A"

        date_taken = (
            exif_data.get('DateTimeOriginal') or
            exif_data.get('DateTimeDigitized') or
            exif_data.get('DateTime') or
            "N/A"
        )
        orientation = exif_data.get('Orientation', 'N/A')

    report_data = {
        "status": "success",
        "file_name": file_info["file_name"],
        "file_size": file_info["file_size_formatted"],
        "file_format": file_format,
        "width": width,
        "height": height,
        "resolution": resolution,
        "color_mode": color_mode,
        "exif_summary": {
            "camera": camera,
            "date_taken": date_taken,
            "orientation": orientation
        },
        "exif_raw": exif_data
    }

    return report_data

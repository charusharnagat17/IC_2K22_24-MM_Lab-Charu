# Robust Text Extractor Model in Python

An end-to-end Python text extraction model designed to extract text from **any image file format**, handling **blurry or clear images**, and correctly classifying images **with or without text**.

---

## Key Features

1. **Format Agnostic (Any Extension)**:
   - Supports `.png`, `.jpg`, `.jpeg`, `.webp`, `.bmp`, `.tiff`, `.gif`, `.ico`, `.ppm`, etc.
   - Accepts image file paths, `PIL.Image` objects, `numpy.ndarray` (OpenCV BGR/Grayscale/RGBA), or raw `bytes`.

2. **Blur Detection & Image Enhancement**:
   - Computes Laplacian Variance to score image clarity and detect blur.
   - Applies adaptive preprocessing (Unsharp Masking sharpening, CLAHE histogram equalization, and adaptive binarization) on blurry or low-contrast images.
   - Multi-pass OCR evaluation selects the candidate image that yields the highest detection confidence.

3. **Handles Images With or Without Text**:
   - Noise filtering removes low-confidence predictions.
   - Returns clear `has_text: True/False` indicator, confidence scores, bounding boxes, and metadata.

---

## Installation & Dependencies

Make sure the required Python dependencies are installed:

```bash
python -m pip install easyocr opencv-python pillow numpy torch torchvision
```

---

## Python API Usage

### Basic Usage

```python
from text_extractor import TextExtractorModel

# Initialize model
model = TextExtractorModel(languages=['en'], min_confidence=0.25)

# Extract text from any image file
result = model.extract_text("sample.png")

print(f"Has Text   : {result['has_text']}")
print(f"Confidence : {result['confidence'] * 100:.1f}%")
print(f"Extracted  : \n{result['text']}")
```

### Result Schema

```json
{
  "has_text": true,
  "text": "Extracted text line 1\nExtracted text line 2",
  "confidence": 0.9425,
  "detections": [
    {
      "text": "Extracted text line 1",
      "confidence": 0.9425,
      "bbox": [[30, 50], [250, 50], [250, 80], [30, 80]]
    }
  ],
  "quality_info": {
    "is_blurry": false,
    "blur_score": 342.5,
    "preprocessing_used": "original"
  },
  "image_info": {
    "format": "PNG",
    "width": 400,
    "height": 150,
    "channels": 3,
    "mode": "RGB"
  }
}
```

---

## Command Line Interface (CLI)

### Single Image Processing

```bash
python text_extractor.py --image path/to/image.jpg
```

### Directory Batch Processing

```bash
python text_extractor.py --dir path/to/image_folder --output results.json
```

---

## Running Unit Tests

To run the automated test suite verifying format support, blur handling, and no-text classification:

```bash
python test_text_extractor.py
```

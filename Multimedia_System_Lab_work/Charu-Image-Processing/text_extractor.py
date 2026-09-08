#this is charu's code
import os
import sys
import json
import argparse
from pathlib import Path
from typing import Union, List, Dict, Any, Optional, Tuple

import cv2
import numpy as np
from PIL import Image, ImageOps


class TextExtractorModel:
    """
    Robust OCR Model for extracting text from any image format.
    
    Handles:
    - Any image extension (JPG, PNG, WEBP, BMP, TIFF, GIF, etc.)
    - Clear and blurry images (automatic blur detection + adaptive preprocessing)
    - Images with or without text (noise filtering and confidence thresholding)
    """

    def __init__(
        self,
        languages: List[str] = ['en'],
        gpu: bool = False,
        min_confidence: float = 0.25,
        blur_threshold: float = 100.0,
        reader = None
    ):
        """
        Initialize the Text Extractor Model.

        :param languages: List of language codes for OCR (default: ['en'])
        :param gpu: Whether to use CUDA GPU acceleration if available
        :param min_confidence: Minimum confidence score threshold (0.0 to 1.0) for valid text
        :param blur_threshold: Laplacian variance threshold below which image is considered blurry
        :param reader: Optional pre-instantiated EasyOCR Reader object
        """
        self.languages = languages
        self.gpu = gpu
        self.min_confidence = min_confidence
        self.blur_threshold = blur_threshold

        if reader is not None:
            self.reader = reader
        else:
            try:
                import easyocr
                # Suppress verbose output during initialization
                self.reader = easyocr.Reader(languages, gpu=gpu, verbose=False)
            except Exception as e:
                raise RuntimeError(
                    f"Failed to initialize EasyOCR engine. Make sure easyocr is installed. Error: {e}"
                )

    @staticmethod
    def load_image(image_input: Union[str, Path, Image.Image, np.ndarray, bytes]) -> Tuple[np.ndarray, Dict[str, Any]]:
        """
        Load any image input format and return a standard BGR numpy array and metadata.
        
        Supports file paths with any extension, PIL Images, raw byte arrays, and OpenCV numpy arrays.
        """
        metadata = {
            "format": "UNKNOWN",
            "width": 0,
            "height": 0,
            "channels": 3,
            "mode": "RGB"
        }

        if isinstance(image_input, (str, Path)):
            path_str = str(image_input)
            if not os.path.exists(path_str):
                raise FileNotFoundError(f"Image file not found at: '{path_str}'")

            # Use PIL for robust format support (WEBP, TIFF, GIF, BMP, etc.)
            with Image.open(path_str) as pil_img:
                metadata["format"] = pil_img.format or Path(path_str).suffix.replace('.', '').upper()
                metadata["mode"] = pil_img.mode
                # Handle orientation EXIF tags automatically
                pil_img = ImageOps.exif_transpose(pil_img)
                # Convert to RGB mode
                pil_rgb = pil_img.convert('RGB')
                metadata["width"], metadata["height"] = pil_rgb.size
                # Convert PIL (RGB) to OpenCV (BGR)
                img_np = cv2.cvtColor(np.array(pil_rgb), cv2.COLOR_RGB2BGR)

        elif isinstance(image_input, Image.Image):
            pil_img = ImageOps.exif_transpose(image_input)
            metadata["format"] = image_input.format or "PIL"
            metadata["mode"] = image_input.mode
            pil_rgb = pil_img.convert('RGB')
            metadata["width"], metadata["height"] = pil_rgb.size
            img_np = cv2.cvtColor(np.array(pil_rgb), cv2.COLOR_RGB2BGR)

        elif isinstance(image_input, bytes):
            nparr = np.frombuffer(image_input, np.uint8)
            img_np = cv2.imdecode(nparr, cv2.IMREAD_COLOR)
            if img_np is None:
                raise ValueError("Failed to decode image from raw bytes.")
            h, w = img_np.shape[:2]
            metadata["width"] = w
            metadata["height"] = h
            metadata["format"] = "BYTES"

        elif isinstance(image_input, np.ndarray):
            img_np = image_input.copy()
            if len(img_np.shape) == 2:  # Grayscale
                img_np = cv2.cvtColor(img_np, cv2.COLOR_GRAY2BGR)
            elif img_np.shape[2] == 4:  # RGBA
                img_np = cv2.cvtColor(img_np, cv2.COLOR_RGBA2BGR)
            h, w = img_np.shape[:2]
            metadata["width"] = w
            metadata["height"] = h
            metadata["format"] = "NUMPY"

        else:
            raise TypeError(f"Unsupported image input type: {type(image_input)}")

        return img_np, metadata

    def detect_blur(self, img_bgr: np.ndarray) -> Tuple[bool, float]:
        """
        Calculate Laplacian Variance score to determine if image is blurry.
        
        Returns:
            (is_blurry, blur_score)
        """
        gray = cv2.cvtColor(img_bgr, cv2.COLOR_BGR2GRAY)
        blur_score = float(cv2.Laplacian(gray, cv2.CV_64F).var())
        is_blurry = blur_score < self.blur_threshold
        return is_blurry, blur_score

    @staticmethod
    def enhance_image(img_bgr: np.ndarray) -> Dict[str, np.ndarray]:
        """
        Generate preprocessed image variants optimized for OCR on blurry or low-contrast text.
        """
        variants = {}

        # 1. Sharpening Kernel (Unsharp Masking)
        kernel = np.array([[0, -1, 0],
                           [-1, 5, -1],
                           [0, -1, 0]], dtype=np.float32)
        sharpened = cv2.filter2D(img_bgr, -1, kernel)
        variants["sharpened"] = sharpened

        # 2. CLAHE (Contrast Limited Adaptive Histogram Equalization)
        lab = cv2.cvtColor(img_bgr, cv2.COLOR_BGR2LAB)
        l, a, b = cv2.split(lab)
        clahe = cv2.createCLAHE(clipLimit=2.0, tileGridSize=(8, 8))
        cl = clahe.apply(l)
        limg = cv2.merge((cl, a, b))
        clahe_bgr = cv2.cvtColor(limg, cv2.COLOR_LAB2BGR)
        variants["clahe"] = clahe_bgr

        # 3. Adaptive Thresholding / Binarization for heavy blur
        gray = cv2.cvtColor(img_bgr, cv2.COLOR_BGR2GRAY)
        blurred = cv2.GaussianBlur(gray, (3, 3), 0)
        adaptive_thresh = cv2.adaptiveThreshold(
            blurred, 255, cv2.ADAPTIVE_THRESH_GAUSSIAN_C, cv2.THRESH_BINARY, 11, 2
        )
        variants["adaptive_thresh"] = cv2.cvtColor(adaptive_thresh, cv2.COLOR_GRAY2BGR)

        return variants

    def extract_text(
        self,
        image_input: Union[str, Path, Image.Image, np.ndarray, bytes],
        detail: int = 1
    ) -> Dict[str, Any]:
        """
        Extract text from an image.

        :param image_input: File path, PIL Image, NumPy array, or bytes
        :param detail: 1 for detailed bounding box detections, 0 for text string only
        :return: Dictionary containing extracted text, has_text boolean, confidence, quality metrics, and metadata
        """
        # Load image & metadata
        img_bgr, metadata = self.load_image(image_input)

        # Assess blur / quality
        is_blurry, blur_score = self.detect_blur(img_bgr)

        # Prepare candidates for OCR (Original image + enhanced variants if blurry)
        candidates = [("original", img_bgr)]
        if is_blurry:
            enhanced_dict = self.enhance_image(img_bgr)
            for name, img_var in enhanced_dict.items():
                candidates.append((name, img_var))

        best_result = None
        best_avg_confidence = -1.0
        best_candidate_name = "original"
        best_valid_detections = []

        # Multi-pass OCR evaluation
        for candidate_name, candidate_img in candidates:
            # Perform EasyOCR inference
            raw_ocr = self.reader.readtext(candidate_img, detail=1)

            valid_detections = []
            confidences = []

            for bbox, text, conf in raw_ocr:
                clean_text = text.strip()
                # Filter out empty string or low-confidence noise
                if len(clean_text) > 0 and conf >= self.min_confidence:
                    # Convert numpy coordinates to plain lists for JSON serialization
                    bbox_list = [[int(pt[0]), int(pt[1])] for pt in bbox]
                    valid_detections.append({
                        "text": clean_text,
                        "confidence": round(float(conf), 4),
                        "bbox": bbox_list
                    })
                    confidences.append(conf)

            avg_conf = float(np.mean(confidences)) if confidences else 0.0

            # Select candidate with highest average confidence & number of valid detections
            score = avg_conf + (0.05 * len(valid_detections))
            if score > best_avg_confidence:
                best_avg_confidence = score
                best_candidate_name = candidate_name
                best_valid_detections = valid_detections
                best_result = (valid_detections, avg_conf)

        # Final decision on whether text exists
        has_text = len(best_valid_detections) > 0

        # Construct full text string
        extracted_text_lines = [det["text"] for det in best_valid_detections]
        full_text = "\n".join(extracted_text_lines)

        overall_confidence = round(
            float(np.mean([d["confidence"] for d in best_valid_detections])), 4
        ) if has_text else 0.0

        output = {
            "has_text": has_text,
            "text": full_text,
            "confidence": overall_confidence,
            "detections": best_valid_detections if detail == 1 else [],
            "quality_info": {
                "is_blurry": is_blurry,
                "blur_score": round(blur_score, 2),
                "preprocessing_used": best_candidate_name
            },
            "image_info": metadata
        }

        return output


def main():
    parser = argparse.ArgumentParser(description="Extract text from any image format (clear, blurry, with or without text).")
    parser.add_argument("--image", "-i", type=str, help="Path to input image file.")
    parser.add_argument("--dir", "-d", type=str, help="Path to directory containing images.")
    parser.add_argument("--output", "-o", type=str, help="Path to save output JSON file.")
    parser.add_argument("--gpu", action="store_true", help="Enable GPU acceleration if available.")
    parser.add_argument("--min-conf", type=float, default=0.25, help="Minimum confidence threshold (default: 0.25).")

    args = parser.parse_args()

    if not args.image and not args.dir:
        parser.print_help()
        sys.exit(1)

    print("Initializing Text Extraction Model...")
    model = TextExtractorModel(languages=['en'], gpu=args.gpu, min_confidence=args.min_conf)

    results = []

    if args.image:
        print(f"Processing image: {args.image}")
        res = model.extract_text(args.image)
        results.append({"file": args.image, "result": res})
        print("\n--- EXTRACTION RESULT ---")
        print(f"Has Text   : {res['has_text']}")
        print(f"Confidence : {res['confidence'] * 100:.1f}%")
        print(f"Is Blurry  : {res['quality_info']['is_blurry']} (Score: {res['quality_info']['blur_score']})")
        print(f"Preprocess : {res['quality_info']['preprocessing_used']}")
        print("Text Content:")
        print(res['text'] if res['has_text'] else "[No text detected]")
        print("-------------------------\n")

    if args.dir:
        image_dir = Path(args.dir)
        valid_exts = {'.jpg', '.jpeg', '.png', '.webp', '.bmp', '.tiff', '.tif', '.gif', '.ppm', '.pnm'}
        files = [p for p in image_dir.rglob('*') if p.suffix.lower() in valid_exts]
        print(f"Found {len(files)} image files in directory: {image_dir}")

        for p in files:
            try:
                res = model.extract_text(p)
                results.append({"file": str(p), "result": res})
                status = f"TEXT ({res['confidence']*100:.0f}%)" if res['has_text'] else "NO TEXT"
                print(f"[{status}] {p.name}")
            except Exception as e:
                print(f"[ERROR] {p.name}: {e}")

    if args.output:
        with open(args.output, 'w', encoding='utf-8') as f:
            json.dump(results, f, indent=2)
        print(f"Results saved to: {args.output}")


if __name__ == "__main__":
    main()
#this is charu's code
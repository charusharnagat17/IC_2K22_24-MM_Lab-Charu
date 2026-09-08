import os
import unittest
import numpy as np
import cv2
from PIL import Image, ImageDraw, ImageFont
from text_extractor import TextExtractorModel

TEST_DIR = os.path.join(os.path.dirname(__file__), "test_images")


def create_sample_images():
    """Helper to generate sample test images with different formats, blur levels, and text presence."""
    os.makedirs(TEST_DIR, exist_ok=True)
    generated_files = {}

    # Font setup
    font = ImageFont.load_default()

    # 1. Clear image WITH text (PNG)
    img_clear = Image.new("RGB", (400, 150), color=(255, 255, 255))
    draw = ImageDraw.Draw(img_clear)
    draw.text((30, 50), "Hello World OCR Test", fill=(0, 0, 0), font=font)
    clear_png = os.path.join(TEST_DIR, "clear_with_text.png")
    img_clear.save(clear_png)
    generated_files["clear_png"] = clear_png

    # 2. Different extensions WITH text (JPG, WEBP, BMP, GIF)
    clear_jpg = os.path.join(TEST_DIR, "clear_with_text.jpg")
    img_clear.save(clear_jpg)
    generated_files["clear_jpg"] = clear_jpg

    clear_webp = os.path.join(TEST_DIR, "clear_with_text.webp")
    img_clear.save(clear_webp)
    generated_files["clear_webp"] = clear_webp

    clear_bmp = os.path.join(TEST_DIR, "clear_with_text.bmp")
    img_clear.save(clear_bmp)
    generated_files["clear_bmp"] = clear_bmp

    clear_gif = os.path.join(TEST_DIR, "clear_with_text.gif")
    img_clear.save(clear_gif)
    generated_files["clear_gif"] = clear_gif

    # 3. Heavy Blurry image WITH text (JPG)
    # Convert PIL to CV2 array, apply Gaussian blur, then save
    img_cv2 = cv2.cvtColor(np.array(img_clear), cv2.COLOR_RGB2BGR)
    blurred_cv2 = cv2.GaussianBlur(img_cv2, (15, 15), 5.0)
    blurry_jpg = os.path.join(TEST_DIR, "blurry_with_text.jpg")
    cv2.imwrite(blurry_jpg, blurred_cv2)
    generated_files["blurry_jpg"] = blurry_jpg

    # 4. Image WITHOUT text (PNG, JPG)
    # A simple smooth color gradient without any text
    no_text_img = np.zeros((200, 200, 3), dtype=np.uint8)
    for i in range(200):
        no_text_img[i, :, :] = [i % 256, (i * 2) % 256, (i * 3) % 256]
    
    no_text_png = os.path.join(TEST_DIR, "no_text_gradient.png")
    cv2.imwrite(no_text_png, no_text_img)
    generated_files["no_text_png"] = no_text_png

    no_text_jpg = os.path.join(TEST_DIR, "no_text_solid.jpg")
    solid_img = np.full((200, 200, 3), (200, 200, 200), dtype=np.uint8)
    cv2.imwrite(no_text_jpg, solid_img)
    generated_files["no_text_jpg"] = no_text_jpg

    return generated_files


class TestTextExtractorModel(unittest.TestCase):

    @classmethod
    def setUpClass(cls):
        print("\n--- Initializing Test Suite & Model ---")
        cls.test_files = create_sample_images()
        # Shared model instance to prevent reloading model weights repeatedly
        cls.model = TextExtractorModel(languages=['en'], gpu=False, min_confidence=0.20)

    def test_01_clear_image_extraction(self):
        """Test text extraction on clear images across different file formats."""
        for key in ["clear_png", "clear_jpg", "clear_webp", "clear_bmp"]:
            file_path = self.test_files[key]
            result = self.model.extract_text(file_path)
            
            self.assertTrue(result["has_text"], f"Failed to detect text in {key}")
            self.assertGreater(result["confidence"], 0.3)
            self.assertIn("HELLO", result["text"].upper())
            self.assertFalse(result["quality_info"]["is_blurry"])

    def test_02_blurry_image_extraction(self):
        """Test blur detection and enhanced processing on blurry images."""
        file_path = self.test_files["blurry_jpg"]
        result = self.model.extract_text(file_path)
        
        # Verify blur detection correctly identified the image as blurry
        self.assertTrue(result["quality_info"]["is_blurry"], "Failed to identify image as blurry")
        self.assertLess(result["quality_info"]["blur_score"], 100.0)

    def test_03_no_text_image(self):
        """Test images that contain no text."""
        for key in ["no_text_png", "no_text_jpg"]:
            file_path = self.test_files[key]
            result = self.model.extract_text(file_path)
            
            self.assertFalse(result["has_text"], f"Should not detect text in no-text image {key}")
            self.assertEqual(result["text"], "")
            self.assertEqual(result["confidence"], 0.0)

    def test_04_numpy_and_pil_input_support(self):
        """Test passing direct PIL Image and NumPy array to extract_text."""
        file_path = self.test_files["clear_png"]
        
        # Test PIL Image input
        with Image.open(file_path) as pil_img:
            res_pil = self.model.extract_text(pil_img)
            self.assertTrue(res_pil["has_text"])

        # Test NumPy Array input
        cv2_img = cv2.imread(file_path)
        res_np = self.model.extract_text(cv2_img)
        self.assertTrue(res_np["has_text"])


if __name__ == "__main__":
    unittest.main()

# -*- coding: utf-8 -*-
r"""
Image Enhancer & Deblurring Tool
--------------------------------
A single, self-contained Python program that takes a blurry image as input 
and produces a sharp, clear output image using advanced deconvolution, 
guided edge-preserving sharpening, multi-scale detail enhancement, and contrast correction.

Author: Charu (Capstone Project)
Path: D:\IC2K2224-MS-Charu\Multimedia_System_Lab_work\Charu-Capstone-Projects\image_enhancer\image_enhancer.py
"""

import os
import sys
import argparse
import time
import numpy as np
import cv2
from skimage import restoration, color, img_as_float, img_as_ubyte
from scipy.ndimage import convolve


def measure_sharpness(image_np):
    """
    Measures sharpness of an image using the Variance of Laplacian (Blur Metric).
    Higher value indicates a sharper, clearer image.
    """
    if len(image_np.shape) == 3:
        gray = cv2.cvtColor(image_np, cv2.COLOR_BGR2GRAY)
    else:
        gray = image_np
    return cv2.Laplacian(gray, cv2.CV_64F).var()


def generate_psf(psf_type="gaussian", size=7, angle=45):
    """
    Generates a Point Spread Function (PSF) kernel representing image blur.
    
    Types:
        - 'gaussian': Defocus / atmospheric blur
        - 'motion': Linear motion blur
        - 'defocus': Circular aperture defocus blur
    """
    if size % 2 == 0:
        size += 1  # ensure odd kernel size
    
    psf = np.zeros((size, size), dtype=np.float32)
    center = size // 2
    
    if psf_type == "gaussian":
        sigma = max(size / 3.0, 0.8)
        for x in range(size):
            for y in range(size):
                dx = x - center
                dy = y - center
                psf[x, y] = np.exp(-(dx**2 + dy**2) / (2 * sigma**2))
    
    elif psf_type == "motion":
        # Linear motion blur at specific angle
        radian = np.deg2rad(angle)
        dx = np.cos(radian)
        dy = np.sin(radian)
        for i in range(-center, center + 1):
            x = int(round(center + i * dy))
            y = int(round(center + i * dx))
            if 0 <= x < size and 0 <= y < size:
                psf[x, y] = 1.0
                
    elif psf_type == "defocus":
        # Disk/circular kernel
        radius = size / 2.0
        for x in range(size):
            for y in range(size):
                if (x - center)**2 + (y - center)**2 <= radius**2:
                    psf[x, y] = 1.0
                    
    else:
        # Fallback to Gaussian
        sigma = 1.5
        for x in range(size):
            for y in range(size):
                psf[x, y] = np.exp(-((x - center)**2 + (y - center)**2) / (2 * sigma**2))

    # Normalize PSF kernel so energy is preserved
    psf_sum = np.sum(psf)
    if psf_sum > 0:
        psf /= psf_sum
    else:
        psf[center, center] = 1.0

    return psf


def lucy_richardson_deblur(img_float, psf, num_iter=30):
    """
    Applies Richardson-Lucy Deconvolution channel by channel.
    Input must be float image scaled [0, 1].
    """
    deblurred = np.zeros_like(img_float)
    if img_float.ndim == 3:
        for c in range(img_float.shape[2]):
            deblurred[:, :, c] = restoration.richardson_lucy(
                img_float[:, :, c], psf, num_iter=num_iter, clip=False
            )
    else:
        deblurred = restoration.richardson_lucy(
            img_float, psf, num_iter=num_iter, clip=False
        )
    return np.clip(deblurred, 0.0, 1.0)


def wiener_deblur(img_float, psf, balance=100.0):
    """
    Applies Wiener Deconvolution in the frequency domain.
    """
    deblurred = np.zeros_like(img_float)
    if img_float.ndim == 3:
        for c in range(img_float.shape[2]):
            deblurred[:, :, c] = restoration.wiener(
                img_float[:, :, c], psf, balance=balance, clip=False
            )
    else:
        deblurred = restoration.wiener(img_float, psf, balance=balance, clip=False)
    return np.clip(deblurred, 0.0, 1.0)


def guided_unsharp_mask(img_bgr, strength=1.5, radius=3, noise_thresh=5.0):
    """
    Applies Bilateral / Edge-Preserving Unsharp Masking to enhance fine details 
    without amplifying noise or creating ugly halos.
    """
    img_float = img_bgr.astype(np.float32)
    
    # Smooth image with Bilateral Filter (preserves edges while removing blur softness)
    blurred = cv2.bilateralFilter(img_bgr, d=radius*2+1, sigmaColor=75, sigmaSpace=75).astype(np.float32)
    
    # Calculate detail mask (high frequencies)
    details = img_float - blurred
    
    # Suppress low-amplitude noise in high frequencies
    abs_details = np.abs(details)
    mask = abs_details > noise_thresh
    details_filtered = np.where(mask, details, 0.0)
    
    # Boost details
    enhanced = img_float + strength * details_filtered
    return np.clip(enhanced, 0, 255).astype(np.uint8)


def apply_clahe_contrast(img_bgr, clip_limit=1.8, tile_grid_size=(8, 8)):
    """
    Applies CLAHE (Contrast Limited Adaptive Histogram Equalization) 
    in LAB color space to increase visual clarity without distorting colors.
    """
    lab = cv2.cvtColor(img_bgr, cv2.COLOR_BGR2LAB)
    l, a, b = cv2.split(lab)
    
    clahe = cv2.createCLAHE(clipLimit=clip_limit, tileGridSize=tile_grid_size)
    cl = clahe.apply(l)
    
    limg = cv2.merge((cl, a, b))
    enhanced_bgr = cv2.cvtColor(limg, cv2.COLOR_LAB2BGR)
    return enhanced_bgr


def enhance_image(
    image_bgr, 
    mode="auto", 
    strength=1.5, 
    psf_type="gaussian", 
    psf_size=7, 
    num_iter=25, 
    enable_clahe=True, 
    denoise_strength=0.3
):
    """
    Main image enhancement & deblurring pipeline.
    
    Pipeline Steps:
    1. Pre-denoising (optional lightweight bilateral filtering to isolate blur from sensor noise).
    2. Deconvolution (Richardson-Lucy or Wiener) to reconstruct latent sharp structure.
    3. Multi-scale edge-preserving unsharp masking to boost high-frequency crispness.
    4. Adaptive CLAHE contrast enhancement for vivid depth and clarity.
    """
    # 1. Soft Denoising if requested
    if denoise_strength > 0:
        denoised = cv2.fastNlMeansDenoisingColored(
            image_bgr, None, h=int(3 * denoise_strength), hColor=int(3 * denoise_strength),
            templateWindowSize=7, searchWindowSize=21
        )
    else:
        denoised = image_bgr.copy()

    # Convert to float [0, 1] for deconvolution
    img_float = img_as_float(cv2.cvtColor(denoised, cv2.COLOR_BGR2RGB))
    psf = generate_psf(psf_type=psf_type, size=psf_size)

    # 2. Deconvolution step
    if mode in ["lucy_richardson", "auto"]:
        deblurred_float = lucy_richardson_deblur(img_float, psf, num_iter=num_iter)
    elif mode == "wiener":
        deblurred_float = wiener_deblur(img_float, psf, balance=100.0)
    else:
        deblurred_float = img_float

    # Convert back to uint8 BGR
    deblurred_ubyte = img_as_ubyte(deblurred_float)
    deblurred_bgr = cv2.cvtColor(deblurred_ubyte, cv2.COLOR_RGB2BGR)

    # 3. High-Frequency Detail Boosting (Guided Unsharp Masking)
    sharpened_bgr = guided_unsharp_mask(deblurred_bgr, strength=strength, radius=3)

    # 4. Adaptive Contrast Enhancement (CLAHE)
    if enable_clahe:
        final_output = apply_clahe_contrast(sharpened_bgr, clip_limit=1.5)
    else:
        final_output = sharpened_bgr

    return final_output


def create_demo_image():
    """
    Creates a synthetic sharp test image with grid lines, geometrical patterns, 
    and crisp text, then applies blur to create a test input image.
    """
    h, w = 500, 700
    img = np.zeros((h, w, 3), dtype=np.uint8)
    
    # Fill background gradient
    for y in range(h):
        for x in range(w):
            img[y, x] = [int(180 + 70 * (x / w)), int(120 + 80 * (y / h)), int(200 - 50 * (x / w))]
            
    # Draw geometric patterns
    cv2.circle(img, (200, 250), 100, (255, 255, 255), 4)
    cv2.rectangle(img, (400, 150), (600, 350), (0, 255, 255), 3)
    cv2.line(img, (50, 450), (650, 50), (255, 0, 128), 3)
    
    # Fine grid lines (hard to see when blurred)
    for x in range(0, w, 25):
        cv2.line(img, (x, 0), (x, h), (80, 80, 80), 1)
    for y in range(0, h, 25):
        cv2.line(img, (0, y), (w, y), (80, 80, 80), 1)
        
    # Add sharp text
    cv2.putText(img, "DEBLUR & ENHANCE TEST", (50, 80), cv2.FONT_HERSHEY_SIMPLEX, 1.2, (255, 255, 255), 3)
    cv2.putText(img, "Capstone Project - Image Restoration", (50, 120), cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 255, 0), 2)
    cv2.putText(img, "Fine Detail Test 1234567890", (50, 420), cv2.FONT_HERSHEY_SIMPLEX, 0.7, (255, 255, 0), 2)
    
    # Apply Gaussian + Motion Blur to synthesize blur input
    psf_motion = generate_psf("motion", size=11, angle=30)
    img_float = img_as_float(cv2.cvtColor(img, cv2.COLOR_BGR2RGB))
    blurred_rgb = np.zeros_like(img_float)
    for c in range(3):
        blurred_rgb[:, :, c] = convolve(img_float[:, :, c], psf_motion, mode='reflect')
        
    blurred_ubyte = img_as_ubyte(np.clip(blurred_rgb, 0, 1))
    blurred_bgr = cv2.cvtColor(blurred_ubyte, cv2.COLOR_RGB2BGR)
    
    # Add slight Gaussian blur overlay
    blurred_bgr = cv2.GaussianBlur(blurred_bgr, (5, 5), 1.5)
    
    return img, blurred_bgr


def main():
    parser = argparse.ArgumentParser(
        description="Image Enhancer: Takes a blurry image input and converts it into a crisp, clear image output.",
        formatter_class=argparse.ArgumentDefaultsHelpFormatter
    )
    parser.add_argument("-i", "--input", type=str, default=None, help="Path to input blurry image (or folder)")
    parser.add_argument("-o", "--output", type=str, default=None, help="Path to save output clear image")
    parser.add_argument("-m", "--mode", type=str, default="auto", choices=["auto", "lucy_richardson", "wiener", "unsharp_only"], help="Enhancement mode")
    parser.add_argument("-s", "--strength", type=float, default=1.8, help="Detail sharpening strength factor")
    parser.add_argument("--psf_type", type=str, default="gaussian", choices=["gaussian", "motion", "defocus"], help="Type of blur kernel to counteract")
    parser.add_argument("--psf_size", type=int, default=7, help="Estimated blur kernel size (odd integer)")
    parser.add_argument("--iterations", type=int, default=25, help="Number of deconvolution iterations")
    parser.add_argument("--no_clahe", action="store_true", help="Disable adaptive contrast enhancement")
    parser.add_argument("--denoise", type=float, default=0.2, help="Noise reduction level before deblurring (0.0 to 1.0)")
    parser.add_argument("--demo", action="store_true", help="Run self-test demo with synthetic blurry image")

    args = parser.parse_args()

    print("==================================================================")
    print("                     IMAGE ENHANCER & DEBLURRER                   ")
    print("==================================================================")

    # Prompt user in terminal if input path is not supplied via arguments
    if not args.demo and args.input is None:
        try:
            print("\n[*] Interactive Mode: Please provide input path.")
            user_in = input("-> Enter path to blurry image (or image directory): ").strip().strip('"').strip("'")
            if not user_in:
                print("[*] Empty input. Switching to Demo Mode...")
                args.demo = True
            else:
                args.input = user_in
                if args.output is None:
                    user_out = input("-> Enter output path (or press ENTER to auto-save in same directory): ").strip().strip('"').strip("'")
                    if user_out:
                        args.output = user_out
        except (EOFError, KeyboardInterrupt):
            print("\n[!] Input cancelled. Exiting.")
            sys.exit(0)

    # Demo Mode run if --demo flag used or empty interactive input
    if args.demo:
        print("\n[*] Running Demo Mode with synthetic blurry image...")
        sharp_original, blurry_input = create_demo_image()
        
        demo_input_path = "demo_blurry.png"
        demo_output_path = "demo_clear_output.png"
        
        cv2.imwrite(demo_input_path, blurry_input)
        print(f"[+] Demo blurry input created: {os.path.abspath(demo_input_path)}")
        
        blur_score_in = measure_sharpness(blurry_input)
        print(f"    - Initial Image Sharpness (Blur Metric): {blur_score_in:.2f}")
        
        t0 = time.time()
        clear_output = enhance_image(
            blurry_input,
            mode=args.mode,
            strength=args.strength,
            psf_type=args.psf_type,
            psf_size=args.psf_size,
            num_iter=args.iterations,
            enable_clahe=not args.no_clahe,
            denoise_strength=args.denoise
        )
        elapsed = time.time() - t0
        
        cv2.imwrite(demo_output_path, clear_output)
        blur_score_out = measure_sharpness(clear_output)
        
        print(f"[+] Enhanced output saved: {os.path.abspath(demo_output_path)}")
        print(f"    - Final Image Sharpness (Blur Metric): {blur_score_out:.2f}")
        print(f"    - Sharpness Gain Factor: {blur_score_out / max(blur_score_in, 1e-5):.2f}x")
        print(f"    - Processing Time: {elapsed:.2f} seconds")
        print("==================================================================")
        print("Usage Tip: Run 'python image_enhancer.py' to enter image path interactively,")
        print("       or run 'python image_enhancer.py -i <blurry_img> -o <clear_img>'")
        print("==================================================================")
        return

    # Process User Provided File or Directory
    input_path = os.path.abspath(args.input)
    if not os.path.exists(input_path):
        print(f"[!] Error: Input path does not exist: {input_path}")
        sys.exit(1)

    # Determine files to process
    if os.path.isfile(input_path):
        files_to_process = [input_path]
        is_directory = False
    else:
        valid_exts = (".png", ".jpg", ".jpeg", ".bmp", ".webp", ".tif", ".tiff")
        files_to_process = [
            os.path.join(input_path, f) for f in os.listdir(input_path) 
            if f.lower().endswith(valid_exts)
        ]
        is_directory = True

    if not files_to_process:
        print(f"[!] No valid image files found in {input_path}")
        sys.exit(1)

    print(f"[*] Found {len(files_to_process)} image(s) to enhance.")

    for idx, img_file in enumerate(files_to_process, 1):
        print(f"\n[{idx}/{len(files_to_process)}] Processing: {os.path.basename(img_file)}...")
        
        img_bgr = cv2.imread(img_file)
        if img_bgr is None:
            print(f"    [!] Failed to read image: {img_file}")
            continue
            
        blur_score_in = measure_sharpness(img_bgr)
        print(f"    - Input Sharpness (Laplacian Var): {blur_score_in:.2f}")
        
        t0 = time.time()
        clear_output = enhance_image(
            img_bgr,
            mode=args.mode,
            strength=args.strength,
            psf_type=args.psf_type,
            psf_size=args.psf_size,
            num_iter=args.iterations,
            enable_clahe=not args.no_clahe,
            denoise_strength=args.denoise
        )
        elapsed = time.time() - t0
        
        blur_score_out = measure_sharpness(clear_output)
        
        # Determine output path
        if args.output:
            if is_directory:
                os.makedirs(args.output, exist_ok=True)
                save_path = os.path.join(args.output, os.path.basename(img_file))
            else:
                save_path = os.path.abspath(args.output)
                os.makedirs(os.path.dirname(save_path), exist_ok=True)
        else:
            base, ext = os.path.splitext(img_file)
            save_path = f"{base}_clear{ext}"
            
        cv2.imwrite(save_path, clear_output)
        print(f"    [+] Saved clear image to: {save_path}")
        print(f"    - Output Sharpness (Laplacian Var): {blur_score_out:.2f}")
        print(f"    - Improvement: {blur_score_out / max(blur_score_in, 1e-5):.2f}x sharper")
        print(f"    - Time Taken: {elapsed:.2f}s")

    print("\n==================================================================")
    print("                     ENHANCEMENT COMPLETE                         ")
    print("==================================================================")

if __name__ == "__main__":
    main()

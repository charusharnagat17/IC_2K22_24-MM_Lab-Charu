# Image Enhancer & Deblurring Program

A Python program that transforms blurry images into sharp, clear outputs using deconvolution (Richardson-Lucy & Wiener), guided edge-preserving sharpening, noise reduction, and adaptive CLAHE contrast enhancement.

## File Location
`D:\IC2K2224-MS-Charu\Multimedia_System_Lab_work\Charu-Capstone-Projects\image_enhancer\image_enhancer.py`

## Quick Start

### 1. Run Demo Mode (Self-Test with Synthetic Blurry Image)
```bash
python image_enhancer.py --demo
```

### 2. Process a Blurry Image
```bash
python image_enhancer.py -i input_blurry.jpg -o output_clear.jpg
```

### 3. Process an Entire Folder of Blurry Images
```bash
python image_enhancer.py -i ./blurry_images/ -o ./clear_images/
```

## Advanced Options

| Parameter | Default | Description |
|---|---|---|
| `-i`, `--input` | `None` | Path to input image file or folder |
| `-o`, `--output` | `None` | Path to save output image or folder |
| `-m`, `--mode` | `auto` | Enhancement mode (`auto`, `lucy_richardson`, `wiener`, `unsharp_only`) |
| `-s`, `--strength` | `1.8` | Detail sharpening strength multiplier |
| `--psf_type` | `gaussian` | Type of blur kernel to counteract (`gaussian`, `motion`, `defocus`) |
| `--psf_size` | `7` | Estimated blur kernel size (odd integer) |
| `--iterations` | `25` | Number of deconvolution iterations for Richardson-Lucy |
| `--denoise` | `0.2` | Pre-denoising level (0.0 to 1.0) |
| `--no_clahe` | `False` | Disable adaptive contrast enhancement |
| `--demo` | `False` | Run demo mode with synthetic blurry image |

## Key Features
- **Deconvolution Restoration**: Reconstructs high-frequency spatial information lost to motion blur or defocus blur.
- **Guided Edge-Preserving Sharpening**: Boosts fine edge details without introducing ringing or halo artifacts.
- **Adaptive CLAHE**: Enhances local contrast in LAB color space to increase visual clarity.
- **Sharpness Metric**: Computes variance of Laplacian score to quantify image clarity improvement.

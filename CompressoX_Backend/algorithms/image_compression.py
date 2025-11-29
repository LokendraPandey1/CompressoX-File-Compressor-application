from PIL import Image
import os
import traceback
import logging
import numpy as np
import math

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Standard JPEG Quantization Tables
LUMINANCE_QUANTIZATION_TABLE = np.array([
    [16, 11, 10, 16, 24, 40, 51, 61],
    [12, 12, 14, 19, 26, 58, 60, 55],
    [14, 13, 16, 24, 40, 57, 69, 56],
    [14, 17, 22, 29, 51, 87, 80, 62],
    [18, 22, 37, 56, 68, 109, 103, 77],
    [24, 35, 55, 64, 81, 104, 113, 92],
    [49, 64, 78, 87, 103, 121, 120, 101],
    [72, 92, 95, 98, 112, 100, 103, 99]
])

CHROMINANCE_QUANTIZATION_TABLE = np.array([
    [17, 18, 24, 47, 99, 99, 99, 99],
    [18, 21, 26, 66, 99, 99, 99, 99],
    [24, 26, 56, 99, 99, 99, 99, 99],
    [47, 66, 99, 99, 99, 99, 99, 99],
    [99, 99, 99, 99, 99, 99, 99, 99],
    [99, 99, 99, 99, 99, 99, 99, 99],
    [99, 99, 99, 99, 99, 99, 99, 99],
    [99, 99, 99, 99, 99, 99, 99, 99]
])

def apply_dct_2d(block):
    """Apply 2D Discrete Cosine Transform manually"""
    # This is a simplified O(N^4) implementation for educational purposes
    # In production, FFT-based O(N^2 log N) would be used
    N = 8
    dct_block = np.zeros((N, N))
    
    for u in range(N):
        for v in range(N):
            sum_val = 0.0
            cu = 1.0 / math.sqrt(2) if u == 0 else 1.0
            cv = 1.0 / math.sqrt(2) if v == 0 else 1.0
            
            for x in range(N):
                for y in range(N):
                    sum_val += block[x, y] * \
                              math.cos((2 * x + 1) * u * math.pi / 16) * \
                              math.cos((2 * y + 1) * v * math.pi / 16)
            
            dct_block[u, v] = 0.25 * cu * cv * sum_val
            
    return dct_block

def apply_idct_2d(dct_block):
    """Apply 2D Inverse Discrete Cosine Transform manually"""
    N = 8
    block = np.zeros((N, N))
    
    for x in range(N):
        for y in range(N):
            sum_val = 0.0
            
            for u in range(N):
                for v in range(N):
                    cu = 1.0 / math.sqrt(2) if u == 0 else 1.0
                    cv = 1.0 / math.sqrt(2) if v == 0 else 1.0
                    
                    sum_val += cu * cv * dct_block[u, v] * \
                              math.cos((2 * x + 1) * u * math.pi / 16) * \
                              math.cos((2 * y + 1) * v * math.pi / 16)
            
            block[x, y] = 0.25 * sum_val
            
    return block

def process_channel(channel, quant_table, quality):
    """Process a single image channel with DCT and Quantization"""
    h, w = channel.shape
    processed = np.zeros_like(channel, dtype=float)
    
    # Scale quantization table based on quality
    scale = 50 / quality if quality < 50 else (100 - quality) / 50
    scaled_quant = np.floor((quant_table * scale) + 0.5)
    scaled_quant[scaled_quant < 1] = 1
    scaled_quant[scaled_quant > 255] = 255
    
    # Process 8x8 blocks
    for i in range(0, h, 8):
        for j in range(0, w, 8):
            # Extract block
            block = channel[i:min(i+8, h), j:min(j+8, w)]
            
            # Pad if necessary
            curr_h, curr_w = block.shape
            if curr_h < 8 or curr_w < 8:
                padded = np.zeros((8, 8))
                padded[:curr_h, :curr_w] = block
                block = padded
            
            # Center values around 0
            block = block - 128
            
            # Apply DCT
            dct_block = apply_dct_2d(block)
            
            # Apply Quantization
            quantized = np.round(dct_block / scaled_quant)
            
            # De-Quantization (Simulating the loss)
            dequantized = quantized * scaled_quant
            
            # Apply Inverse DCT
            idct_block = apply_idct_2d(dequantized)
            
            # Un-center values
            idct_block = idct_block + 128
            
            # Store result
            processed[i:min(i+8, h), j:min(j+8, w)] = idct_block[:curr_h, :curr_w]
            
    return np.clip(processed, 0, 255).astype(np.uint8)

def compress_image_manual(img, quality):
    """Compress image using manual DCT implementation"""
    # Convert to YCbCr
    img_ycbcr = img.convert('YCbCr')
    y, cb, cr = img_ycbcr.split()
    
    # Convert to numpy arrays
    y_arr = np.array(y)
    cb_arr = np.array(cb)
    cr_arr = np.array(cr)
    
    # Process channels
    # Y uses Luminance table, Cb/Cr use Chrominance table
    y_processed = process_channel(y_arr, LUMINANCE_QUANTIZATION_TABLE, quality)
    cb_processed = process_channel(cb_arr, CHROMINANCE_QUANTIZATION_TABLE, quality)
    cr_processed = process_channel(cr_arr, CHROMINANCE_QUANTIZATION_TABLE, quality)
    
    # Reconstruct image
    processed_img = Image.merge('YCbCr', (
        Image.fromarray(y_processed),
        Image.fromarray(cb_processed),
        Image.fromarray(cr_processed)
    ))
    
    return processed_img.convert('RGB')

def compress_image(input_path, output_path, is_lossy=True, quality=50, force_algorithm=None):
    """Compress an image using PIL with optional lossy or lossless method"""
    try:
        with Image.open(input_path) as img:
            original_size = os.path.getsize(input_path)

            # Handle transparency for PNGs
            if img.format == 'PNG' and img.mode in ('RGBA', 'LA') and not is_lossy:
                # Keep RGBA/LA for lossless PNG
                pass
            elif img.mode != 'RGB' and is_lossy:
                # Convert to RGB for JPEG (lossy)
                if img.mode == 'RGBA':
                    # Create white background for transparent images converting to JPEG
                    background = Image.new('RGB', img.size, (255, 255, 255))
                    background.paste(img, mask=img.split()[3])
                    img = background
                else:
                    img = img.convert('RGB')

            if is_lossy:
                # Apply Manual DCT Compression
                logger.info(f"Applying manual DCT compression with quality {quality}")
                compressed_img = compress_image_manual(img, quality)
                
                # Save the processed image
                # We save as JPEG to finalize the compression (Huffman coding is handled by PIL save)
                compressed_img.save(output_path, 'JPEG', quality=quality, optimize=True)
                
                algorithm = 'Custom DCT & Quantization'
                description = f'Manual 8x8 Block DCT + Quantization (Quality: {quality})'
            else:
                # Use PNG for lossless compression
                img.save(output_path, 'PNG', optimize=True, compress_level=9)
                algorithm = 'PNG DEFLATE Compression'
                description = 'Uses DEFLATE algorithm with maximum compression level (9)'

            compressed_size = os.path.getsize(output_path)

            ratio = original_size / compressed_size if compressed_size > 0 else 1

            return {
                'success': True,
                'original_size': original_size,
                'compressed_size': compressed_size,
                'ratio': ratio,
                'algorithm': algorithm,
                'description': description
            }

    except Exception as e:
        logger.error(f"Error compressing image: {str(e)}")
        logger.error(traceback.format_exc())
        return {
            'success': False,
            'error': str(e)
        }

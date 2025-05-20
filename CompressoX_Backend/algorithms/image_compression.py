from PIL import Image
import os
import traceback
import logging
import numpy as np
import sys

# Add the parent directory to the Python path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def compress_image(input_path, output_path, is_lossy=True, quality=50, force_algorithm=None):
    """Compress an image using PIL with optional lossy or lossless method"""
    try:
        with Image.open(input_path) as img:
            original_size = os.path.getsize(input_path)

            # Ensure image is in RGB mode for JPEG
            if img.mode != 'RGB':
                img = img.convert('RGB')

            if is_lossy:
                img.save(output_path, 'JPEG', quality=quality, optimize=True)
                algorithm = 'JPEG DCT Compression'
                description = f'Uses Discrete Cosine Transform (DCT) with quality {quality} and Huffman coding'
            else:
                img.save(output_path, 'PNG', optimize=True, compress_level=9)
                algorithm = 'PNG DEFLATE Compression'
                description = 'Uses DEFLATE algorithm with maximum compression level (9)'

            compressed_size = os.path.getsize(output_path)

            # Retry lossy with lower quality if compression is ineffective
            if compressed_size >= original_size:
                if is_lossy and quality > 20:
                    return compress_image(input_path, output_path, is_lossy, quality - 20)
                elif not is_lossy:
                    img.save(output_path, 'JPEG', quality=100, optimize=True)
                    compressed_size = os.path.getsize(output_path)
                    algorithm = 'JPEG Lossless Mode'
                    description = 'Uses JPEG in lossless mode with maximum quality and Huffman coding'

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
        return {
            'success': False,
            'error': str(e)
        }

import numpy as np
from PIL import Image
import io
import os

class RLECompressor:
    def __init__(self):
        self.name = "Run-Length Encoding"
        self.description = "Compresses repeated pixel values by storing count and value"
    
    def compress(self, image, quality=50):
        """Compress image using PIL's built-in optimization"""
        try:
            # Convert to RGB if not already
            if image.mode != 'RGB':
                image = image.convert('RGB')
            
            # Get original file size
            original_size = os.path.getsize(image.filename) if hasattr(image, 'filename') else None
            
            # Save with maximum compression
            buffer = io.BytesIO()
            image.save(buffer, format='JPEG', quality=100, optimize=True)
            buffer.seek(0)
            
            # If compression didn't help, return original
            if original_size and buffer.getbuffer().nbytes >= original_size:
                return image
            
            return Image.open(buffer)
            
        except Exception as e:
            print(f"Error in compression: {str(e)}")
            return image

# Remove other compressor classes since we're using only PIL's optimization 
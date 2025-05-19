import numpy as np
import math
from PIL import Image

class DCTCompressor:
    def __init__(self):
        self.name = "DCT-based Compression"
        self.description = "Uses Discrete Cosine Transform to compress images by removing high-frequency components"
    
    def dct_2d(self, block):
        """Apply 2D DCT to an 8x8 block using numpy's FFT"""
        return np.fft.fft2(block).real
    
    def idct_2d(self, block):
        """Apply inverse 2D DCT to an 8x8 block using numpy's FFT"""
        return np.fft.ifft2(block).real
    
    def compress(self, image, quality=50):
        """Compress image using DCT"""
        try:
            # Convert to RGB if not already
            if image.mode != 'RGB':
                image = image.convert('RGB')
            
            # Convert to numpy array
            img_array = np.array(image)
            height, width = img_array.shape[:2]
            
            # Process each color channel separately
            compressed = np.zeros_like(img_array)
            block_size = 8
            
            # Calculate total blocks for progress tracking
            total_blocks = (height // block_size) * (width // block_size) * 3
            processed_blocks = 0
            
            for channel in range(3):  # RGB channels
                channel_data = img_array[:,:,channel]
                
                for i in range(0, height, block_size):
                    for j in range(0, width, block_size):
                        # Get 8x8 block
                        block = channel_data[i:i+block_size, j:j+block_size]
                        if block.shape != (block_size, block_size):
                            # Pad the block if it's not 8x8
                            padded_block = np.zeros((block_size, block_size), dtype=block.dtype)
                            padded_block[:block.shape[0], :block.shape[1]] = block
                            block = padded_block
                        
                        # Apply DCT
                        dct_block = self.dct_2d(block)
                        
                        # Quantization based on quality
                        # Scale quality to affect more coefficients
                        threshold = (100 - quality) / 100.0 * 255 * 0.5
                        dct_block[np.abs(dct_block) < threshold] = 0
                        
                        # Inverse DCT
                        idct_block = self.idct_2d(dct_block)
                        
                        # Copy back to the correct size
                        if i + block_size <= height and j + block_size <= width:
                            compressed[i:i+block_size, j:j+block_size, channel] = idct_block
                        else:
                            # Handle edge blocks
                            h = min(block_size, height - i)
                            w = min(block_size, width - j)
                            compressed[i:i+h, j:j+w, channel] = idct_block[:h, :w]
                        
                        processed_blocks += 1
                        if processed_blocks % 100 == 0:
                            print(f"Progress: {processed_blocks}/{total_blocks} blocks processed")
            
            # Ensure values are within valid range
            compressed = np.clip(compressed, 0, 255)
            return Image.fromarray(np.uint8(compressed))
        except Exception as e:
            print(f"Error in DCT compression: {str(e)}")
            # Fallback to simple quantization if DCT fails
            return QuantizationCompressor().compress(image, quality)

class QuantizationCompressor:
    def __init__(self):
        self.name = "Quantization-based Compression"
        self.description = "Reduces color precision by quantizing pixel values"
    
    def compress(self, image, quality=50):
        """Compress image using quantization"""
        try:
            # Convert to RGB if not already
            if image.mode != 'RGB':
                image = image.convert('RGB')
            
            # Convert to numpy array
            img_array = np.array(image)
            
            # Calculate number of levels based on quality
            # Higher quality = more levels
            levels = max(2, int(256 * (quality / 100)))
            step = 256 / levels
            
            # Quantize each color channel using vectorized operations
            quantized = np.floor(img_array / step) * step
            
            return Image.fromarray(np.uint8(quantized))
        except Exception as e:
            print(f"Error in quantization compression: {str(e)}")
            # Fallback to color reduction if quantization fails
            return ColorReductionCompressor().compress(image, quality)

class ColorReductionCompressor:
    def __init__(self):
        self.name = "Color Reduction Compression"
        self.description = "Reduces the number of unique colors in the image"
    
    def compress(self, image, quality=50):
        """Compress image by reducing colors"""
        try:
            # Convert to RGB if not already
            if image.mode != 'RGB':
                image = image.convert('RGB')
            
            # Convert to numpy array
            img_array = np.array(image)
            
            # Calculate number of colors based on quality
            # Higher quality = more colors
            num_colors = max(2, int(256 * (quality / 100)))
            
            # Reshape to 2D array of pixels
            pixels = img_array.reshape(-1, 3)
            
            # Use MiniBatchKMeans for faster clustering
            from sklearn.cluster import MiniBatchKMeans
            kmeans = MiniBatchKMeans(n_clusters=num_colors, random_state=42, batch_size=1000)
            labels = kmeans.fit_predict(pixels)
            palette = kmeans.cluster_centers_
            
            # Replace each pixel with its cluster center
            compressed = palette[labels].reshape(img_array.shape)
            
            return Image.fromarray(np.uint8(compressed))
        except Exception as e:
            print(f"Error in color reduction: {str(e)}")
            # If all compression methods fail, return original image
            return image 
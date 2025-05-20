import re
from typing import Dict, List, Tuple
import logging

logger = logging.getLogger(__name__)

def compress_text_lossy(text: str, quality: int = 50) -> Tuple[str, Dict]:
    """
    Compress text using lossy compression techniques.
    
    Args:
        text (str): The input text to compress
        quality (int): Compression quality (1-100)
        
    Returns:
        Tuple[str, Dict]: Compressed text and compression metadata
    """
    try:
        if not isinstance(text, str):
            raise TypeError(f"Expected string input, got {type(text)}")
            
        if not text:
            return "", {
                'algorithm': 'Lossy Text Compression',
                'original_size': 0,
                'compressed_size': 0,
                'ratio': 0
            }
        
        # Validate quality parameter
        if not 1 <= quality <= 100:
            raise ValueError(f"Quality must be between 1 and 100, got {quality}")
        
        # Convert quality to a float between 0 and 1
        quality_factor = quality / 100
        
        # Store original text for size calculation
        original_text = text
        
        # Remove extra whitespace
        text = re.sub(r'\s+', ' ', text)
        
        # Remove punctuation based on quality
        if quality_factor < 0.7:
            text = re.sub(r'[^\w\s]', '', text)
        
        # Convert to lowercase if quality is low
        if quality_factor < 0.5:
            text = text.lower()
        
        # Calculate compression stats
        original_size = len(original_text.encode('utf-8'))
        compressed_size = len(text.encode('utf-8'))
        ratio = original_size / compressed_size if compressed_size > 0 else 1
        
        metadata = {
            'algorithm': 'Lossy Text Compression',
            'original_size': original_size,
            'compressed_size': compressed_size,
            'ratio': ratio,
            'quality_factor': quality_factor,
            'success': True
        }
        
        return text, metadata
        
    except Exception as e:
        logger.error(f"Error in lossy compression: {str(e)}")
        raise RuntimeError(f"Lossy compression failed: {str(e)}") 
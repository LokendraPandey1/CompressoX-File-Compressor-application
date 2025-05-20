from .text_lossy_compression import compress_text_lossy
from .text_lossless_compression import compress_text_lossless
import logging
import os

# Configure logging
logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)

def compress_text(input_path: str, output_path: str, is_lossy: bool = True, quality: int = 50) -> dict:
    """
    Compress a text file using either lossy or lossless compression
    
    Args:
        input_path (str): Path to the input text file
        output_path (str): Path to save the compressed file
        is_lossy (bool): Whether to use lossy compression
        quality (int): Compression quality (1-100)
        
    Returns:
        dict: Compression metadata with success flag
    """
    try:
        # Validate input file
        if not os.path.exists(input_path):
            raise FileNotFoundError(f"Input file not found: {input_path}")
        
        # Validate quality parameter
        if not 1 <= quality <= 100:
            raise ValueError(f"Quality must be between 1 and 100, got {quality}")
        
        # Read the input file
        logger.debug(f"Reading file: {input_path}")
        with open(input_path, 'r', encoding='utf-8') as f:
            text = f.read()
        
        if not text:
            raise ValueError("Input file is empty")
        
        # Compress the text
        logger.debug(f"Starting {'lossy' if is_lossy else 'lossless'} compression")
        try:
            if is_lossy:
                compressed_text, metadata = compress_text_lossy(text, quality)
            else:
                compressed_text, metadata = compress_text_lossless(text, quality)
        except Exception as comp_error:
            logger.error(f"Compression error: {str(comp_error)}")
            raise RuntimeError(f"Compression failed: {str(comp_error)}")
        
        # Ensure output directory exists
        os.makedirs(os.path.dirname(output_path), exist_ok=True)
        
        # Write the compressed text
        logger.debug(f"Writing compressed file: {output_path}")
        with open(output_path, 'w', encoding='utf-8') as f:
            f.write(compressed_text)
        
        # Add success flag and file paths to metadata
        metadata.update({
            'success': True,
            'input_path': input_path,
            'output_path': output_path,
            'compression_type': 'lossy' if is_lossy else 'lossless',
            'quality': quality
        })
        
        logger.info(f"Compression completed successfully. Ratio: {metadata.get('ratio', 0):.2f}x")
        return metadata
        
    except FileNotFoundError as e:
        logger.error(f"File error: {str(e)}")
        return {
            'success': False,
            'error': f"File error: {str(e)}",
            'algorithm': 'Text Compression',
            'original_size': 0,
            'compressed_size': 0,
            'ratio': 0
        }
    except ValueError as e:
        logger.error(f"Validation error: {str(e)}")
        return {
            'success': False,
            'error': f"Validation error: {str(e)}",
            'algorithm': 'Text Compression',
            'original_size': 0,
            'compressed_size': 0,
            'ratio': 0
        }
    except Exception as e:
        logger.error(f"Unknown error: {str(e)}")
        return {
            'success': False,
            'error': f"Unknown error: {str(e)}",
            'algorithm': 'Text Compression',
            'original_size': 0,
            'compressed_size': 0,
            'ratio': 0
        }

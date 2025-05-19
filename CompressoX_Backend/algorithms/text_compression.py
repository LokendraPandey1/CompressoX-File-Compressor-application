from .text_lossy_compression import compress_text_lossy
from .text_lossless_compression import compress_text_lossless

def compress_text(input_path: str, output_path: str, is_lossy: bool = True) -> dict:
    """Compress a text file using either lossy or lossless compression"""
    if is_lossy:
        return compress_text_lossy(input_path, output_path)
    else:
        return compress_text_lossless(input_path, output_path)

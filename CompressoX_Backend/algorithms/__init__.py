from .text_compression import compress_text
from .text_lossy_compression import compress_text_lossy
from .text_lossless_compression import compress_text_lossless
from .image_compression import compress_image
from .video_compression import compress_video
from .pdf_compression import compress_pdf
from .docx_compression import compress_docx

__all__ = [
    'compress_text',
    'compress_text_lossy',
    'compress_text_lossless',
    'compress_image',
    'compress_video',
    'compress_pdf',
    'compress_docx'
]

from typing import Dict, List, Tuple
from collections import Counter
import heapq
import logging

logger = logging.getLogger(__name__)

class HuffmanNode:
    def __init__(self, char: str, freq: int):
        self.char = char
        self.freq = freq
        self.left = None
        self.right = None
        
    def __lt__(self, other):
        return self.freq < other.freq

def build_huffman_tree(text: str) -> HuffmanNode:
    """Build Huffman tree from input text."""
    try:
        # Count frequency of each character
        freq = Counter(text)
        
        if not freq:
            raise ValueError("Empty text or no valid characters found")
        
        # Create priority queue
        heap = [HuffmanNode(char, freq) for char, freq in freq.items()]
        heapq.heapify(heap)
        
        # Build tree
        while len(heap) > 1:
            left = heapq.heappop(heap)
            right = heapq.heappop(heap)
            
            internal = HuffmanNode(None, left.freq + right.freq)
            internal.left = left
            internal.right = right
            
            heapq.heappush(heap, internal)
        
        return heap[0]
    except Exception as e:
        logger.error(f"Error building Huffman tree: {str(e)}")
        raise

def build_huffman_codes(root: HuffmanNode, current_code: str = "", codes: Dict = None) -> Dict:
    """Build Huffman codes from tree."""
    if codes is None:
        codes = {}
    
    if root is None:
        return codes
    
    if root.char is not None:
        codes[root.char] = current_code if current_code else "0"
    
    build_huffman_codes(root.left, current_code + "0", codes)
    build_huffman_codes(root.right, current_code + "1", codes)
    
    return codes

def compress_text_lossless(text: str, quality: int = 100) -> Tuple[str, Dict]:
    """
    Compress text using lossless Huffman coding.
    
    Args:
        text (str): The input text to compress
        quality (int): Not used in lossless compression, kept for API consistency
        
    Returns:
        Tuple[str, Dict]: Compressed text and compression metadata
    """
    try:
        if not isinstance(text, str):
            raise TypeError(f"Expected string input, got {type(text)}")
            
        if not text:
            return "", {
                'algorithm': 'Lossless Text Compression (Huffman)',
                'original_size': 0,
                'compressed_size': 0,
                'ratio': 0,
                'success': True
            }
        
        # Build Huffman tree and codes
        tree = build_huffman_tree(text)
        codes = build_huffman_codes(tree)
        
        # Encode text
        try:
            encoded = ''.join(codes[char] for char in text)
        except KeyError as e:
            logger.error(f"Character not found in Huffman codes: {str(e)}")
            raise ValueError(f"Invalid character in input text: {str(e)}")
        
        # Calculate compression stats
        original_size = len(text.encode('utf-8'))
        compressed_size = (len(encoded) + 7) // 8  # Convert bits to bytes
        ratio = original_size / compressed_size if compressed_size > 0 else 1
        
        metadata = {
            'algorithm': 'Lossless Text Compression (Huffman)',
            'original_size': original_size,
            'compressed_size': compressed_size,
            'ratio': ratio,
            'huffman_codes': codes,
            'success': True
        }
        
        return encoded, metadata
        
    except Exception as e:
        logger.error(f"Error in lossless compression: {str(e)}")
        raise RuntimeError(f"Lossless compression failed: {str(e)}") 
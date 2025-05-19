import os
from typing import Dict, Tuple
from collections import Counter
import heapq

class HuffmanNode:
    def __init__(self, char: str, freq: int):
        self.char = char
        self.freq = freq
        self.left = None
        self.right = None

    def __lt__(self, other):
        return self.freq < other.freq

def build_huffman_tree(text: str) -> HuffmanNode:
    """Build a Huffman tree from the input text"""
    # Count character frequencies
    freq = Counter(text)
    
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

def build_huffman_codes(root: HuffmanNode, current_code: str = "", codes: Dict[str, str] = None) -> Dict[str, str]:
    """Build Huffman codes from the tree"""
    if codes is None:
        codes = {}
    
    if root is None:
        return codes
    
    if root.char is not None:
        codes[root.char] = current_code if current_code else "0"
    
    build_huffman_codes(root.left, current_code + "0", codes)
    build_huffman_codes(root.right, current_code + "1", codes)
    
    return codes

def run_length_encode(text: str) -> bytes:
    """Run-length encoding implementation"""
    if not text:
        return b''
    
    result = bytearray()
    count = 1
    current = text[0]
    
    for char in text[1:]:
        if char == current:
            count += 1
        else:
            result.extend(current.encode())
            result.extend(str(count).encode())
            current = char
            count = 1
    
    # Add the last character and its count
    result.extend(current.encode())
    result.extend(str(count).encode())
    
    return bytes(result)

def lz77_encode(text: str, window_size: int = 4096, lookahead_size: int = 64) -> bytes:
    """LZ77 compression implementation"""
    result = bytearray()
    pos = 0
    
    while pos < len(text):
        # Find the longest match in the window
        best_match = (0, 0)  # (offset, length)
        window_start = max(0, pos - window_size)
        
        for i in range(window_start, pos):
            match_length = 0
            while (pos + match_length < len(text) and 
                   match_length < lookahead_size and 
                   text[i + match_length] == text[pos + match_length]):
                match_length += 1
            
            if match_length > best_match[1]:
                best_match = (pos - i, match_length)
        
        # If we found a match
        if best_match[1] > 2:
            # Encode as (offset, length, next_char)
            result.extend(best_match[0].to_bytes(2, 'big'))
            result.extend(best_match[1].to_bytes(1, 'big'))
            if pos + best_match[1] < len(text):
                result.extend(text[pos + best_match[1]].encode())
            pos += best_match[1] + 1
        else:
            # Encode as (0, 0, char)
            result.extend(b'\x00\x00')
            result.extend(text[pos].encode())
            pos += 1
    
    return bytes(result)

def compress_text_lossless(input_path: str, output_path: str) -> dict:
    """Compress a text file using lossless compression algorithms"""
    try:
        # Get original size
        original_size = os.path.getsize(input_path)
        
        # Read input file
        with open(input_path, 'r', encoding='utf-8') as f:
            text = f.read()
        
        # Try each lossless algorithm
        algorithms = [
            (lambda t: run_length_encode(t), 'Run-Length Encoding', 'Uses run-length encoding for repeated characters'),
            (lambda t: lz77_encode(t), 'LZ77 Compression', 'Uses LZ77 sliding window compression'),
            (lambda t: huffman_encode(t), 'Huffman Coding', 'Uses Huffman coding for optimal compression')
        ]
        
        best_compressed_size = original_size
        best_algorithm = None
        
        for algo_func, name, description in algorithms:
            try:
                # Apply the algorithm
                compressed_data = algo_func(text)
                
                # Write to temporary file
                temp_output = f"{output_path}.temp"
                with open(temp_output, 'wb') as f:
                    f.write(compressed_data)
                
                # Get compressed size
                compressed_size = os.path.getsize(temp_output)
                
                # If this attempt produced better compression, keep it
                if compressed_size < best_compressed_size:
                    best_compressed_size = compressed_size
                    best_algorithm = (name, description)
                    # Move the temporary file to the final output path
                    os.replace(temp_output, output_path)
                else:
                    # Remove the temporary file
                    os.remove(temp_output)
                
            except Exception as e:
                print(f"Error in {name}: {str(e)}")
                if os.path.exists(temp_output):
                    os.remove(temp_output)
                continue
        
        # If no compression was successful, return error
        if best_compressed_size >= original_size:
            return {
                'success': False,
                'error': 'Could not achieve compression'
            }
        
        return {
            'success': True,
            'original_size': original_size,
            'compressed_size': best_compressed_size,
            'ratio': original_size / best_compressed_size if best_compressed_size > 0 else 1,
            'algorithm': best_algorithm[0],
            'description': best_algorithm[1]
        }
        
    except Exception as e:
        print(f"Error in lossless compression: {str(e)}")
        return {
            'success': False,
            'error': str(e)
        }

def huffman_encode(text: str) -> bytes:
    """Huffman coding implementation"""
    # Build Huffman tree and codes
    root = build_huffman_tree(text)
    codes = build_huffman_codes(root)
    
    # Encode text
    encoded = ''.join(codes[char] for char in text)
    
    # Convert to bytes
    padding = 8 - (len(encoded) % 8)
    encoded += '0' * padding
    
    # Convert to bytes
    result = bytearray()
    for i in range(0, len(encoded), 8):
        byte = encoded[i:i+8]
        result.append(int(byte, 2))
    
    # Add padding information
    result.insert(0, padding)
    
    # Add codes dictionary
    codes_str = str(codes)
    result.extend(len(codes_str).to_bytes(4, 'big'))
    result.extend(codes_str.encode())
    
    return bytes(result)
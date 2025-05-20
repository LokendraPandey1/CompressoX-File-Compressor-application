import os
import numpy as np
from collections import Counter
import heapq
import cv2
from typing import Dict, Tuple, List
import math
import time
from concurrent.futures import ThreadPoolExecutor, as_completed
from functools import partial

class HuffmanNode:
    def __init__(self, value: int, freq: int):
        self.value = value
        self.freq = freq
        self.left = None
        self.right = None
    
    def __lt__(self, other):
        return self.freq < other.freq

def build_huffman_tree(data: List[int]) -> HuffmanNode:
    """Build a Huffman tree from the input data"""
    freq = Counter(data)
    heap = [HuffmanNode(value, freq) for value, freq in freq.items()]
    heapq.heapify(heap)
    
    while len(heap) > 1:
        left = heapq.heappop(heap)
        right = heapq.heappop(heap)
        internal = HuffmanNode(None, left.freq + right.freq)
        internal.left = left
        internal.right = right
        heapq.heappush(heap, internal)
    
    return heap[0]

def build_huffman_codes(root: HuffmanNode, current_code: str = "", codes: Dict[int, str] = None) -> Dict[int, str]:
    """Build Huffman codes from the tree"""
    if codes is None:
        codes = {}
    
    if root is None:
        return codes
    
    if root.value is not None:
        codes[root.value] = current_code if current_code else "0"
    
    build_huffman_codes(root.left, current_code + "0", codes)
    build_huffman_codes(root.right, current_code + "1", codes)
    
    return codes

def huffman_encode(data: List[int]) -> bytes:
    """Encode data using Huffman coding"""
    root = build_huffman_tree(data)
    codes = build_huffman_codes(root)
    encoded = ''.join(codes[value] for value in data)
    
    # Convert to bytes
    padding = 8 - (len(encoded) % 8)
    encoded += '0' * padding
    
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

def run_length_encode(data: List[int]) -> bytes:
    """Run-length encoding implementation"""
    if not data:
        return b''
    
    result = bytearray()
    count = 1
    current = data[0]
    
    for value in data[1:]:
        if value == current:
            count += 1
        else:
            result.append(current)
            result.extend(str(count).encode())
            current = value
            count = 1
    
    # Add the last value and its count
    result.append(current)
    result.extend(str(count).encode())
    
    return bytes(result)

def lz77_encode(data: List[int], window_size: int = 4096, lookahead_size: int = 64) -> bytes:
    """LZ77 compression implementation"""
    result = bytearray()
    pos = 0
    
    while pos < len(data):
        # Find the longest match in the window
        best_match = (0, 0)  # (offset, length)
        window_start = max(0, pos - window_size)
        
        for i in range(window_start, pos):
            match_length = 0
            while (pos + match_length < len(data) and 
                   match_length < lookahead_size and 
                   data[i + match_length] == data[pos + match_length]):
                match_length += 1
            
            if match_length > best_match[1]:
                best_match = (pos - i, match_length)
        
        # If we found a match
        if best_match[1] > 2:
            # Encode as (offset, length, next_value)
            result.extend(best_match[0].to_bytes(2, 'big'))
            result.extend(best_match[1].to_bytes(1, 'big'))
            if pos + best_match[1] < len(data):
                result.append(data[pos + best_match[1]])
            pos += best_match[1] + 1
        else:
            # Encode as (0, 0, value)
            result.extend(b'\x00\x00')
            result.append(data[pos])
            pos += 1
    
    return bytes(result)

def apply_motion_estimation(frame1: np.ndarray, frame2: np.ndarray, block_size: int = 16) -> Tuple[np.ndarray, List[Tuple[int, int]]]:
    """Apply motion estimation between two frames"""
    height, width = frame1.shape[:2]
    motion_vectors = []
    
    # Convert frames to grayscale if they're not already
    if len(frame1.shape) == 3:
        frame1 = cv2.cvtColor(frame1, cv2.COLOR_BGR2GRAY)
    if len(frame2.shape) == 3:
        frame2 = cv2.cvtColor(frame2, cv2.COLOR_BGR2GRAY)
    
    # For each block in frame2
    for y in range(0, height - block_size + 1, block_size):
        for x in range(0, width - block_size + 1, block_size):
            block = frame2[y:y+block_size, x:x+block_size]
            min_diff = float('inf')
            best_mv = (0, 0)
            
            # Search in frame1
            search_range = 16
            for dy in range(-search_range, search_range + 1):
                for dx in range(-search_range, search_range + 1):
                    # Check if the search window is within frame1
                    if (y + dy >= 0 and y + dy + block_size <= height and
                        x + dx >= 0 and x + dx + block_size <= width):
                        # Calculate difference
                        diff = np.sum(np.abs(block - frame1[y+dy:y+dy+block_size, x+dx:x+dx+block_size]))
                        if diff < min_diff:
                            min_diff = diff
                            best_mv = (dx, dy)
            
            motion_vectors.append(best_mv)
    
    return frame1, motion_vectors

def apply_dct_transform(block: np.ndarray) -> np.ndarray:
    """Apply Discrete Cosine Transform to a block"""
    return cv2.dct(block.astype(np.float32))

def apply_quantization(dct_block: np.ndarray, quality: int = 50) -> np.ndarray:
    """Apply quantization to DCT coefficients"""
    # Standard quantization matrix
    q_matrix = np.array([
        [16, 11, 10, 16, 24, 40, 51, 61],
        [12, 12, 14, 19, 26, 58, 60, 55],
        [14, 13, 16, 24, 40, 57, 69, 56],
        [14, 17, 22, 29, 51, 87, 80, 62],
        [18, 22, 37, 56, 68, 109, 103, 77],
        [24, 35, 55, 64, 81, 104, 113, 92],
        [49, 64, 78, 87, 103, 121, 120, 101],
        [72, 92, 95, 98, 112, 100, 103, 99]
    ])
    
    # Scale quantization matrix based on quality
    scale = 1.0
    if quality < 50:
        scale = 50.0 / quality
    else:
        scale = (100 - quality) / 50.0
    
    q_matrix = q_matrix * scale
    
    # Quantize
    return np.round(dct_block / q_matrix) * q_matrix

def process_dct_frame(frame: np.ndarray, quality: int = 50) -> np.ndarray:
    """Process a frame using DCT compression by dividing it into 8x8 blocks"""
    height, width = frame.shape[:2]
    
    # Convert to YCrCb color space
    if len(frame.shape) == 3:
        ycrcb = cv2.cvtColor(frame, cv2.COLOR_BGR2YCrCb)
        y, cr, cb = cv2.split(ycrcb)
    else:
        y = frame
        cr = cb = None
    
    # Process Y channel in 8x8 blocks
    processed_y = np.zeros_like(y, dtype=np.float32)
    for i in range(0, height, 8):
        for j in range(0, width, 8):
            # Get 8x8 block
            block = y[i:min(i+8, height), j:min(j+8, width)]
            
            # Pad block if necessary
            if block.shape != (8, 8):
                padded_block = np.zeros((8, 8), dtype=np.float32)
                padded_block[:block.shape[0], :block.shape[1]] = block
                block = padded_block
            
            # Apply DCT and quantization
            dct_block = apply_dct_transform(block)
            quantized = apply_quantization(dct_block, quality)
            idct_block = cv2.idct(quantized)
            
            # Store result
            processed_y[i:min(i+8, height), j:min(j+8, width)] = idct_block[:block.shape[0], :block.shape[1]]
    
    # Process chrominance channels if they exist
    if cr is not None and cb is not None:
        # Downsample chrominance channels
        cr = cv2.resize(cr, (width//2, height//2))
        cb = cv2.resize(cb, (width//2, height//2))
        
        # Process Cr channel
        processed_cr = np.zeros_like(cr, dtype=np.float32)
        for i in range(0, cr.shape[0], 8):
            for j in range(0, cr.shape[1], 8):
                block = cr[i:min(i+8, cr.shape[0]), j:min(j+8, cr.shape[1])]
                if block.shape != (8, 8):
                    padded_block = np.zeros((8, 8), dtype=np.float32)
                    padded_block[:block.shape[0], :block.shape[1]] = block
                    block = padded_block
                dct_block = apply_dct_transform(block)
                quantized = apply_quantization(dct_block, quality)
                idct_block = cv2.idct(quantized)
                processed_cr[i:min(i+8, cr.shape[0]), j:min(j+8, cr.shape[1])] = idct_block[:block.shape[0], :block.shape[1]]
        
        # Process Cb channel
        processed_cb = np.zeros_like(cb, dtype=np.float32)
        for i in range(0, cb.shape[0], 8):
            for j in range(0, cb.shape[1], 8):
                block = cb[i:min(i+8, cb.shape[0]), j:min(j+8, cb.shape[1])]
                if block.shape != (8, 8):
                    padded_block = np.zeros((8, 8), dtype=np.float32)
                    padded_block[:block.shape[0], :block.shape[1]] = block
                    block = padded_block
                dct_block = apply_dct_transform(block)
                quantized = apply_quantization(dct_block, quality)
                idct_block = cv2.idct(quantized)
                processed_cb[i:min(i+8, cb.shape[0]), j:min(j+8, cb.shape[1])] = idct_block[:block.shape[0], :block.shape[1]]
        
        # Upsample chrominance channels
        processed_cr = cv2.resize(processed_cr, (width, height))
        processed_cb = cv2.resize(processed_cb, (width, height))
        
        # Merge channels
        processed_frame = cv2.merge([processed_y, processed_cr, processed_cb])
        return cv2.cvtColor(processed_frame, cv2.COLOR_YCrCb2BGR)
    
    return processed_y.astype(np.uint8)

def process_frame_chunk(frames: List[np.ndarray], algo: dict, prev_frame: np.ndarray = None) -> List[np.ndarray]:
    """Process a chunk of frames in parallel"""
    processed_frames = []
    current_prev = prev_frame
    
    for frame in frames:
        try:
            if algo['name'] == 'Motion Compensation':
                if current_prev is not None:
                    _, motion_vectors = apply_motion_estimation(current_prev, frame, algo['block_size'])
                    frame = cv2.addWeighted(frame, 0.7, current_prev, 0.3, 0)
            
            elif algo['name'] == 'DCT Compression':
                frame = process_dct_frame(frame, algo['quality'])
            
            elif algo['name'] == 'Hybrid Compression':
                if current_prev is not None:
                    _, motion_vectors = apply_motion_estimation(current_prev, frame, algo['block_size'])
                frame = process_dct_frame(frame, algo['quality'])
            
            elif algo['name'] == 'Huffman Coding':
                frame_bytes = frame.tobytes()
                compressed = huffman_encode(list(frame_bytes))
                frame = np.frombuffer(frame_bytes, dtype=np.uint8).reshape(frame.shape)
            
            elif algo['name'] == 'Run-Length Encoding':
                frame_bytes = frame.tobytes()
                compressed = run_length_encode(list(frame_bytes))
                frame = np.frombuffer(frame_bytes, dtype=np.uint8).reshape(frame.shape)
            
            elif algo['name'] == 'LZ77 Compression':
                frame_bytes = frame.tobytes()
                compressed = lz77_encode(list(frame_bytes))
                frame = np.frombuffer(frame_bytes, dtype=np.uint8).reshape(frame.shape)
            
            processed_frames.append(frame)
            current_prev = frame.copy()
        
        except Exception as e:
            print(f"Error processing frame: {str(e)}")
            processed_frames.append(frame)
            current_prev = frame.copy()
    
    return processed_frames

def compress_video(input_path: str, output_path: str, is_lossy: bool = True) -> dict:
    """Compress a video file using various algorithms"""
    start_time = time.time()
    
    try:
        # Get original size
        original_size = os.path.getsize(input_path)
        print(f"Original file size: {original_size / (1024*1024):.2f} MB")
        
        # Open video file
        cap = cv2.VideoCapture(input_path)
        if not cap.isOpened():
            return {
                'success': False,
                'error': 'Could not open video file'
            }
        
        # Get video properties
        width = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
        height = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
        fps = cap.get(cv2.CAP_PROP_FPS)
        total_frames = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
        
        print(f"Video properties: {width}x{height} @ {fps}fps, {total_frames} frames")
        
        # Define algorithms
        if is_lossy:
            algorithms = [
                {
                    'name': 'Motion Compensation',
                    'description': 'Uses motion estimation and compensation',
                    'block_size': 16,
                    'search_range': 16
                },
                {
                    'name': 'DCT Compression',
                    'description': 'Uses DCT transform and quantization',
                    'block_size': 8,
                    'quality': 50
                },
                {
                    'name': 'Hybrid Compression',
                    'description': 'Combines motion compensation and DCT',
                    'block_size': 16,
                    'quality': 60
                }
            ]
        else:
            algorithms = [
                {
                    'name': 'Huffman Coding',
                    'description': 'Uses Huffman coding for frame data',
                    'block_size': 8
                },
                {
                    'name': 'Run-Length Encoding',
                    'description': 'Uses RLE for frame data',
                    'block_size': 8
                },
                {
                    'name': 'LZ77 Compression',
                    'description': 'Uses LZ77 for frame data',
                    'block_size': 8
                }
            ]
        
        best_compressed_size = original_size
        best_algorithm = None
        
        # Determine optimal chunk size based on available memory
        chunk_size = min(30, max(1, total_frames // (os.cpu_count() or 1)))
        print(f"Using chunk size of {chunk_size} frames for parallel processing")
        
        for algo in algorithms:
            try:
                print(f"\nTrying algorithm: {algo['name']}")
                print(f"Description: {algo['description']}")
                
                # Reset video capture
                cap.set(cv2.CAP_PROP_POS_FRAMES, 0)
                
                # Create temporary output
                temp_output = f"{output_path}.temp"
                temp_out = cv2.VideoWriter(temp_output, cv2.VideoWriter_fourcc(*'avc1'), fps, (width, height))
                
                # Process frames in parallel
                processed_frames = 0
                last_progress = -1
                last_update_time = time.time()
                prev_frame = None
                
                with ThreadPoolExecutor(max_workers=os.cpu_count()) as executor:
                    while True:
                        # Read a chunk of frames
                        frames = []
                        for _ in range(chunk_size):
                            ret, frame = cap.read()
                            if not ret:
                                break
                            frames.append(frame)
                        
                        if not frames:
                            break
                        
                        # Process chunk
                        processed_chunk = process_frame_chunk(frames, algo, prev_frame)
                        
                        # Write processed frames
                        for frame in processed_chunk:
                            temp_out.write(frame)
                            processed_frames += 1
                            
                            # Update progress
                            current_time = time.time()
                            progress = (processed_frames / total_frames) * 100
                            elapsed_time = current_time - start_time
                            frames_per_second = processed_frames / elapsed_time
                            remaining_frames = total_frames - processed_frames
                            estimated_time = remaining_frames / frames_per_second if frames_per_second > 0 else 0
                            
                            # Update progress every second or when percentage changes
                            if (current_time - last_update_time >= 1.0 or 
                                int(progress) > last_progress):
                                last_progress = int(progress)
                                last_update_time = current_time
                                print(f"Progress: {progress:.1f}% ({processed_frames}/{total_frames} frames)")
                                print(f"Speed: {frames_per_second:.1f} fps")
                                print(f"Estimated time remaining: {estimated_time/60:.1f} minutes")
                        
                        prev_frame = processed_chunk[-1].copy()
                
                # Release video writer
                temp_out.release()
                
                # Get compressed size
                compressed_size = os.path.getsize(temp_output)
                compression_ratio = original_size / compressed_size if compressed_size > 0 else 1
                
                print(f"\nAlgorithm {algo['name']} results:")
                print(f"Compressed size: {compressed_size / (1024*1024):.2f} MB")
                print(f"Compression ratio: {compression_ratio:.2f}x")
                
                # If this attempt produced better compression, keep it
                if compressed_size < best_compressed_size:
                    best_compressed_size = compressed_size
                    best_algorithm = (algo['name'], algo['description'])
                    os.replace(temp_output, output_path)
                    print("New best compression achieved!")
                else:
                    os.remove(temp_output)
                
            except Exception as e:
                print(f"Error in {algo['name']}: {str(e)}")
                if os.path.exists(temp_output):
                    os.remove(temp_output)
                continue
        
        # Release video capture
        cap.release()
        
        # Calculate total time
        total_time = time.time() - start_time
        
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
            'description': best_algorithm[1],
            'processing_time': total_time
        }
        
    except Exception as e:
        print(f"Error in video compression: {str(e)}")
        return {
            'success': False,
            'error': str(e)
        }


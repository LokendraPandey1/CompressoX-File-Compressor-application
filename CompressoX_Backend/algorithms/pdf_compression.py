import heapq
import os
from PyPDF2 import PdfReader, PdfWriter
from PIL import Image
import io
import re
from collections import Counter

# -------------------- HUFFMAN CODING --------------------

class HuffmanNode:
    def __init__(self, byte, freq):
        self.byte = byte
        self.freq = freq
        self.left = None
        self.right = None

    def __lt__(self, other):
        return self.freq < other.freq

def build_huffman_tree(data):
    """Build a Huffman tree from the input data"""
    freq_map = {}
    for byte in data:
        freq_map[byte] = freq_map.get(byte, 0) + 1

    heap = [HuffmanNode(byte, freq) for byte, freq in freq_map.items()]
    heapq.heapify(heap)

    while len(heap) > 1:
        n1 = heapq.heappop(heap)
        n2 = heapq.heappop(heap)
        merged = HuffmanNode(None, n1.freq + n2.freq)
        merged.left = n1
        merged.right = n2
        heapq.heappush(heap, merged)

    return heap[0]

def generate_huffman_codes(root):
    """Generate Huffman codes from the tree"""
    codes = {}

    def helper(node, code=""):
        if node is None:
            return
        if node.byte is not None:
            codes[node.byte] = code
        helper(node.left, code + '0')
        helper(node.right, code + '1')

    helper(root)
    return codes

def huffman_encode(data):
    """Encode data using Huffman coding"""
    root = build_huffman_tree(data)
    codes = generate_huffman_codes(root)
    encoded = ''.join(codes[byte] for byte in data)
    
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

def run_length_encode(data):
    """Run-length encoding implementation"""
    if not data:
        return b''
    
    result = bytearray()
    count = 1
    current = data[0]
    
    for byte in data[1:]:
        if byte == current:
            count += 1
        else:
            result.append(current)
            result.extend(str(count).encode())
            current = byte
            count = 1
    
    # Add the last byte and its count
    result.append(current)
    result.extend(str(count).encode())
    
    return bytes(result)

def lz77_encode(data, window_size=4096, lookahead_size=64):
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
            # Encode as (offset, length, next_byte)
            result.extend(best_match[0].to_bytes(2, 'big'))
            result.extend(best_match[1].to_bytes(1, 'big'))
            if pos + best_match[1] < len(data):
                result.append(data[pos + best_match[1]])
            pos += best_match[1] + 1
        else:
            # Encode as (0, 0, byte)
            result.extend(b'\x00\x00')
            result.append(data[pos])
            pos += 1
    
    return bytes(result)

# -------------------- LZW CODING --------------------

def lzw_encode(bitstring):
    dict_size = 256
    dictionary = {chr(i): i for i in range(dict_size)}
    w = ""
    result = []

    for char in bitstring:
        wc = w + char
        if wc in dictionary:
            w = wc
        else:
            result.append(dictionary[w])
            dictionary[wc] = dict_size
            dict_size += 1
            w = char

    if w:
        result.append(dictionary[w])
    return result

# -------------------- PDF COMPRESSION --------------------

def optimize_pdf_structure(pdf_writer):
    """Optimize PDF structure by removing unnecessary elements and optimizing objects"""
    # Remove unnecessary metadata
    for key in ['/Metadata', '/PieceInfo', '/LastModified', '/CreationDate', '/ModDate']:
        if key in pdf_writer:
            del pdf_writer[key]
    
    # Optimize document catalog
    if '/Catalog' in pdf_writer:
        catalog = pdf_writer['/Catalog']
        for key in ['/OpenAction', '/PageLabels', '/Names']:
            if key in catalog:
                del catalog[key]

def compress_pdf(input_path, output_path, is_lossy=True):
    """Compress a PDF file using various algorithms"""
    try:
        # Open the PDF using PyPDF2
        reader = PdfReader(input_path)
        writer = PdfWriter()
        
        # Get original size
        original_size = os.path.getsize(input_path)
        
        # Define compression algorithms
        if is_lossy:
            algorithms = [
                {
                    'name': 'Aggressive Image Compression',
                    'description': 'Reduces image quality to 40% and dimensions by 50%',
                    'quality': 40,
                    'scale': 0.5,
                    'color_reduction': True
                },
                {
                    'name': 'Balanced Image Compression',
                    'description': 'Reduces image quality to 60% and dimensions by 30%',
                    'quality': 60,
                    'scale': 0.7,
                    'color_reduction': False
                },
                {
                    'name': 'Smart Image Compression',
                    'description': 'Adaptive compression based on image content',
                    'quality': 70,
                    'scale': 0.8,
                    'color_reduction': True
                }
            ]
        else:
            algorithms = [
                {
                    'name': 'Maximum Compression',
                    'description': 'Uses maximum compression settings with object optimization',
                    'compress_content': True,
                    'compress_images': True,
                    'optimize_objects': True,
                    'remove_metadata': True
                },
                {
                    'name': 'Balanced Compression',
                    'description': 'Balanced compression with moderate optimization',
                    'compress_content': True,
                    'compress_images': True,
                    'optimize_objects': True,
                    'remove_metadata': False
                },
                {
                    'name': 'Structure Optimization',
                    'description': 'Focuses on PDF structure optimization',
                    'compress_content': False,
                    'compress_images': False,
                    'optimize_objects': True,
                    'remove_metadata': True
                }
            ]
        
        best_compressed_size = original_size
        best_output_path = output_path
        best_algorithm = None
        
        for algo in algorithms:
            try:
                # Create a temporary output path for this attempt
                temp_output = f"{output_path}.temp"
                temp_writer = PdfWriter()
                
                if is_lossy:
                    # Process each page
                    for page in reader.pages:
                        # Add page to writer
                        temp_writer.add_page(page)
                        
                        # Compress page content
                        if '/Resources' in page and '/XObject' in page['/Resources']:
                            xObject = page['/Resources']['/XObject'].get_object()
                            for obj in xObject:
                                if xObject[obj]['/Subtype'] == '/Image':
                                    try:
                                        # Get image data
                                        image = xObject[obj]
                                        image_bytes = image.get_data()
                                        
                                        # Open image with PIL
                                        img = Image.open(io.BytesIO(image_bytes))
                                        
                                        # Get original dimensions
                                        width, height = img.size
                                        
                                        # Calculate new dimensions
                                        new_width = int(width * algo['scale'])
                                        new_height = int(height * algo['scale'])
                                        
                                        # Resize image
                                        img = img.resize((new_width, new_height), Image.Resampling.LANCZOS)
                                        
                                        # Color reduction if enabled
                                        if algo['color_reduction']:
                                            img = img.convert('P', palette=Image.ADAPTIVE, colors=64)
                                        
                                        # Save with specified quality
                                        buffer = io.BytesIO()
                                        img.save(buffer, format='JPEG', quality=algo['quality'], optimize=True)
                                        image_bytes = buffer.getvalue()
                                        
                                        # Update image data
                                        image._data = image_bytes
                                        
                                    except Exception as e:
                                        print(f"Error in image compression: {str(e)}")
                else:
                    # Process each page
                    for page in reader.pages:
                        # Add page to writer
                        temp_writer.add_page(page)
                        
                        # Compress page content
                        if '/Contents' in page:
                            try:
                                # Get page content
                                content = page['/Contents'].get_data()
                                
                                # Try different compression algorithms
                                compression_algorithms = [
                                    (huffman_encode, 'Huffman'),
                                    (run_length_encode, 'RLE'),
                                    (lz77_encode, 'LZ77')
                                ]
                                
                                best_compressed = None
                                best_size = float('inf')
                                
                                for comp_algo, name in compression_algorithms:
                                    compressed = comp_algo(content)
                                    if len(compressed) < best_size:
                                        best_compressed = compressed
                                        best_size = len(compressed)
                                
                                # Update page content
                                page['/Contents']._data = best_compressed
                                
                            except Exception as e:
                                print(f"Error in content compression: {str(e)}")
                
                # Optimize structure if enabled
                if not is_lossy and algo.get('optimize_objects', False):
                    optimize_pdf_structure(temp_writer)
                
                # Write to temporary file
                with open(temp_output, 'wb') as f:
                    temp_writer.write(f)
                
                # Get compressed size
                compressed_size = os.path.getsize(temp_output)
                
                # If this attempt produced better compression, keep it
                if compressed_size < best_compressed_size:
                    best_compressed_size = compressed_size
                    best_algorithm = (algo['name'], algo['description'])
                    # Move the temporary file to the final output path
                    os.replace(temp_output, output_path)
                else:
                    # Remove the temporary file
                    os.remove(temp_output)
                
            except Exception as e:
                print(f"Error in {algo['name']}: {str(e)}")
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
        print(f"Error in PDF compression: {str(e)}")
        return {
            'success': False,
            'error': str(e)
        }

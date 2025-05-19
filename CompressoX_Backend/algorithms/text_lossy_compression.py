import os
import re
from typing import Dict, Tuple

def compress_text_lossy(input_path: str, output_path: str) -> dict:
    """Compress a text file using lossy compression algorithms"""
    try:
        # Get original size
        original_size = os.path.getsize(input_path)
        
        # Read input file
        with open(input_path, 'r', encoding='utf-8') as f:
            text = f.read()
        
        # Try each lossy algorithm
        algorithms = [
            (lambda t: re.sub(r'\s+', ' ', t).lower().strip(), 'Whitespace Removal', 'Removes extra whitespace and converts to lowercase'),
            (lambda t: ' '.join(w for w in t.split() if len(w) > 3), 'Short Word Removal', 'Removes words shorter than 4 characters'),
            (lambda t: re.sub(r'[aeiouAEIOU]', '', t), 'Vowel Removal', 'Removes all vowels from text')
        ]
        
        best_compressed_size = original_size
        best_algorithm = None
        
        for algo_func, name, description in algorithms:
            try:
                # Apply the algorithm
                compressed_text = algo_func(text)
                
                # Write to temporary file
                temp_output = f"{output_path}.temp"
                with open(temp_output, 'w', encoding='utf-8') as f:
                    f.write(compressed_text)
                
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
        print(f"Error in lossy compression: {str(e)}")
        return {
            'success': False,
            'error': str(e)
        }
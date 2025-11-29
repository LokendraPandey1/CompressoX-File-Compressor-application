import os
import numpy as np
import cv2
import time
from concurrent.futures import ThreadPoolExecutor

def resize_frame(frame, scale):
    """Manually resize frame using bilinear interpolation (via OpenCV for performance)"""
    height, width = frame.shape[:2]
    new_height, new_width = int(height * scale), int(width * scale)
    return cv2.resize(frame, (new_width, new_height), interpolation=cv2.INTER_LINEAR)

def process_frame_chunk(frames, algo):
    """Process a chunk of frames based on the selected algorithm"""
    processed_frames = []
    
    if algo['name'] == 'Resolution Scaling':
        scale = algo.get('scale', 0.5)
        for frame in frames:
            processed_frames.append(resize_frame(frame, scale))
            
    elif algo['name'] == 'Frame Rate Reduction':
        # Keep every Nth frame
        skip = algo.get('skip', 2)
        for i, frame in enumerate(frames):
            if i % skip == 0:
                processed_frames.append(frame)
                
    elif algo['name'] == 'Grayscale Conversion':
        for frame in frames:
            gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
            processed_frames.append(cv2.cvtColor(gray, cv2.COLOR_GRAY2BGR))
            
    else:
        # Default: No change
        processed_frames = frames
        
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
            return {'success': False, 'error': 'Could not open video file'}
        
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
                    'name': 'Resolution Scaling',
                    'description': 'Reduces resolution by 50%',
                    'scale': 0.5
                },
                {
                    'name': 'Frame Rate Reduction',
                    'description': 'Reduces frame rate by half',
                    'skip': 2
                },
                {
                    'name': 'Grayscale Conversion',
                    'description': 'Converts video to grayscale',
                }
            ]
        else:
            # For "lossless", we just copy the stream but maybe in a more efficient container if possible
            # Or apply very mild optimization. Here we'll use High Quality Scaling
            algorithms = [
                {
                    'name': 'High Quality Optimization',
                    'description': 'Optimizes video stream structure',
                    'scale': 1.0 # No scaling, just re-encoding
                }
            ]
        
        best_compressed_size = original_size
        best_algorithm = None
        
        # We only try the first applicable algorithm for now to save time, 
        # or the user could select one. For this demo, we'll pick the most effective one based on mode.
        # If lossy, Resolution Scaling is usually best balance.
        selected_algo = algorithms[0]
        
        print(f"\nApplying algorithm: {selected_algo['name']}")
        
        # Reset video capture
        cap.set(cv2.CAP_PROP_POS_FRAMES, 0)
        
        # Create temporary output
        temp_output = f"{output_path}.temp.mp4"
        
        # Determine output dimensions/fps
        out_width, out_height = width, height
        out_fps = fps
        
        if selected_algo['name'] == 'Resolution Scaling':
            out_width = int(width * selected_algo['scale'])
            out_height = int(height * selected_algo['scale'])
        elif selected_algo['name'] == 'Frame Rate Reduction':
            out_fps = fps / selected_algo['skip']
            
        # Initialize Video Writer
        # H.264 is standard, but requires openh264 or similar. 'mp4v' is safer for basic opencv.
        fourcc = cv2.VideoWriter_fourcc(*'mp4v') 
        out = cv2.VideoWriter(temp_output, fourcc, out_fps, (out_width, out_height))
        
        processed_count = 0
        
        while True:
            ret, frame = cap.read()
            if not ret:
                break
                
            # Process frame
            if selected_algo['name'] == 'Resolution Scaling':
                frame = resize_frame(frame, selected_algo['scale'])
            elif selected_algo['name'] == 'Frame Rate Reduction':
                processed_count += 1
                if processed_count % selected_algo['skip'] != 0:
                    continue
            elif selected_algo['name'] == 'Grayscale Conversion':
                gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
                frame = cv2.cvtColor(gray, cv2.COLOR_GRAY2BGR)
                
            out.write(frame)
            
        cap.release()
        out.release()
        
        # Get compressed size
        if os.path.exists(temp_output):
            compressed_size = os.path.getsize(temp_output)
            
            # Move to final output
            if os.path.exists(output_path):
                os.remove(output_path)
            os.rename(temp_output, output_path)
            
            best_algorithm = (selected_algo['name'], selected_algo['description'])
            
            return {
                'success': True,
                'original_size': original_size,
                'compressed_size': compressed_size,
                'ratio': original_size / compressed_size if compressed_size > 0 else 1,
                'algorithm': best_algorithm[0],
                'description': best_algorithm[1],
                'processing_time': time.time() - start_time
            }
        else:
            return {'success': False, 'error': 'Output file creation failed'}
            
    except Exception as e:
        print(f"Error in video compression: {str(e)}")
        return {
            'success': False,
            'error': str(e)
        }

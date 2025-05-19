import os
import sys
import time
import shutil
import traceback
from flask import Flask, request, send_file, jsonify
from flask_cors import CORS
from werkzeug.utils import secure_filename
from PIL import Image
from concurrent.futures import ThreadPoolExecutor
import io

# Add the parent directory to Python path
current_dir = os.path.dirname(os.path.abspath(__file__))
parent_dir = os.path.dirname(current_dir)
sys.path.insert(0, parent_dir)

from CompressoX_Backend.algorithms.text_compression import compress_text
from CompressoX_Backend.algorithms.image_compression import compress_image
from CompressoX_Backend.algorithms.pdf_compression import compress_pdf
from CompressoX_Backend.algorithms.video_compression import compress_video
from CompressoX_Backend.algorithms.docx_compression import compress_docx

app = Flask(__name__)
CORS(app)

# Get the absolute path of the current directory
BASE_DIR = os.path.abspath(os.path.dirname(__file__))

# Configuration with absolute paths
UPLOAD_FOLDER = os.path.join(BASE_DIR, 'temp')
OUTPUT_FOLDER = os.path.join(BASE_DIR, 'compressed')

ALLOWED_EXTENSIONS = {
    'text': ['.txt', '.md', '.log'],
    'image': ['.jpg', '.jpeg', '.png', '.bmp', '.gif'],
    'pdf': ['.pdf'],
    'video': ['.mp4', '.avi', '.mov', '.wmv'],
    'docx': ['.docx', '.doc']
}

# Create necessary directories with proper permissions
def ensure_directories():
    try:
        os.makedirs(UPLOAD_FOLDER, exist_ok=True)
        os.makedirs(OUTPUT_FOLDER, exist_ok=True)
        print(f"Created/verified directories:")
        print(f"Upload folder: {UPLOAD_FOLDER}")
        print(f"Output folder: {OUTPUT_FOLDER}")
        
        # Test write permissions
        test_file = os.path.join(UPLOAD_FOLDER, 'test.txt')
        with open(test_file, 'w') as f:
            f.write('test')
        os.remove(test_file)
        print("Write permissions verified")
    except Exception as e:
        print(f"Error setting up directories: {str(e)}")
        raise

# Ensure directories exist at startup
ensure_directories()

def get_file_extension(filename):
    return os.path.splitext(filename)[1].lower()

def is_allowed_file(filename, file_type):
    return get_file_extension(filename) in ALLOWED_EXTENSIONS.get(file_type, [])

def get_output_filename(input_filename, file_type):
    base_name = os.path.splitext(input_filename)[0]
    timestamp = str(int(time.time()))
    extension = get_file_extension(input_filename)
    return f"compressed_{base_name}_{timestamp}{extension}"

@app.route('/compress/metadata', methods=['POST'])
def get_compression_metadata():
    try:
        if 'files' not in request.files:
            return jsonify({'error': 'No files provided'}), 400
            
        file = request.files['files']
        if file.filename == '':
            return jsonify({'error': 'No file selected'}), 400
            
        # Get compression options
        is_lossy = request.form.get('isLossy', 'true').lower() == 'true'
        quality = int(request.form.get('quality', 50))
        file_type = request.form.get('fileType', '').lower()
        
        if not file_type:
            return jsonify({'error': 'File type not specified'}), 400
        
        # Save uploaded file
        input_path = os.path.join(UPLOAD_FOLDER, secure_filename(file.filename))
        file.save(input_path)
        
        # Get file size
        file_size = os.path.getsize(input_path)
        
        # Generate output filename
        filename, ext = os.path.splitext(file.filename)
        output_filename = f"{filename}_compressed{ext}"
        output_path = os.path.join(UPLOAD_FOLDER, output_filename)
        
        # Get compression metadata
        result = None
        if file_type == 'image':
            result = compress_image(input_path, output_path, is_lossy, quality)
        elif file_type == 'text':
            result = compress_text(input_path, output_path)
        elif file_type == 'pdf':
            result = compress_pdf(input_path, output_path, is_lossy=is_lossy)
        elif file_type == 'video':
            result = compress_video(input_path, output_path)
        elif file_type == 'docx':
            result = compress_docx(input_path, output_path)
        else:
            return jsonify({'error': f'Unsupported file type: {file_type}'}), 400
            
        if not result:
            return jsonify({'error': 'Compression failed: No result returned'}), 500
            
        if not isinstance(result, dict):
            return jsonify({'error': 'Compression failed: Invalid result format'}), 500
            
        if not result.get('success', False):
            error_msg = result.get('error', 'Unknown compression error')
            return jsonify({'error': error_msg}), 500
            
        return jsonify(result)
        
    except Exception as e:
        print(f"Error in compression metadata: {str(e)}")
        return jsonify({'error': str(e)}), 500

@app.route('/compress/file', methods=['POST'])
def get_compressed_file():
    try:
        if 'files' not in request.files:
            return jsonify({'error': 'No files provided'}), 400
            
        file = request.files['files']
        if file.filename == '':
            return jsonify({'error': 'No file selected'}), 400
            
        # Get compression options
        is_lossy = request.form.get('isLossy', 'true').lower() == 'true'
        quality = int(request.form.get('quality', 50))
        file_type = request.form.get('fileType', '').lower()
        
        if not file_type:
            return jsonify({'error': 'File type not specified'}), 400
        
        # Save uploaded file
        input_path = os.path.join(UPLOAD_FOLDER, secure_filename(file.filename))
        file.save(input_path)
        
        # Generate output filename
        filename, ext = os.path.splitext(file.filename)
        output_filename = f"{filename}_compressed{ext}"
        output_path = os.path.join(UPLOAD_FOLDER, output_filename)
        
        # Compress file
        result = None
        if file_type == 'image':
            result = compress_image(input_path, output_path, is_lossy, quality)
        elif file_type == 'text':
            result = compress_text(input_path, output_path)
        elif file_type == 'pdf':
            result = compress_pdf(input_path, output_path, is_lossy=is_lossy)
        elif file_type == 'video':
            result = compress_video(input_path, output_path)
        elif file_type == 'docx':
            result = compress_docx(input_path, output_path)
        else:
            return jsonify({'error': f'Unsupported file type: {file_type}'}), 400
            
        if not result:
            return jsonify({'error': 'Compression failed: No result returned'}), 500
            
        if not isinstance(result, dict):
            return jsonify({'error': 'Compression failed: Invalid result format'}), 500
            
        if not result.get('success', False):
            error_msg = result.get('error', 'Unknown compression error')
            return jsonify({'error': error_msg}), 500
            
        # Verify output file exists
        if not os.path.exists(output_path):
            return jsonify({'error': 'Compressed file not found'}), 500
            
        # Read compressed file
        try:
            with open(output_path, 'rb') as f:
                compressed_data = f.read()
        except Exception as e:
            return jsonify({'error': f'Failed to read compressed file: {str(e)}'}), 500
            
        # Clean up temp files
        try:
            os.remove(input_path)
            os.remove(output_path)
        except Exception as e:
            print(f"Error cleaning up temp files: {str(e)}")
            
        return send_file(
            io.BytesIO(compressed_data),
            mimetype=file.content_type,
            as_attachment=True,
            download_name=output_filename
        )
        
    except Exception as e:
        print(f"Error in compression: {str(e)}")
        return jsonify({'error': str(e)}), 500

@app.route('/download/<filename>')
def download_file(filename):
    try:
        return send_file(
            os.path.join(OUTPUT_FOLDER, filename),
            as_attachment=True,
            download_name=filename
        )
    except Exception as e:
        return jsonify({'error': str(e)}), 404

@app.route('/health', methods=['GET'])
def health_check():
    return jsonify({
        'status': 'healthy',
        'upload_folder': UPLOAD_FOLDER,
        'output_folder': OUTPUT_FOLDER,
        'upload_folder_exists': os.path.exists(UPLOAD_FOLDER),
        'output_folder_exists': os.path.exists(OUTPUT_FOLDER)
    })

if __name__ == '__main__':
    print("\n=== Starting CompressoX Backend ===")
    print(f"Base directory: {BASE_DIR}")
    print(f"Upload folder: {UPLOAD_FOLDER}")
    print(f"Output folder: {OUTPUT_FOLDER}")
    app.run(port=8080, debug=True)

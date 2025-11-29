import heapq
import os
from PyPDF2 import PdfReader, PdfWriter
from PIL import Image
import io
import re
from collections import Counter
import logging

logger = logging.getLogger(__name__)

# -------------------- PDF COMPRESSION --------------------

def optimize_pdf_structure(pdf_writer):
    """Optimize PDF structure by removing unnecessary elements and optimizing objects"""
    try:
        # Remove unnecessary metadata
        for key in ['/Metadata', '/PieceInfo', '/LastModified', '/CreationDate', '/ModDate']:
            if key in pdf_writer._root_object:
                del pdf_writer._root_object[key]
        
        # Optimize document catalog
        if '/Catalog' in pdf_writer._root_object:
            catalog = pdf_writer._root_object['/Catalog']
            for key in ['/OpenAction', '/PageLabels', '/Names']:
                if key in catalog:
                    del catalog[key]
        
        # Optimize page objects
        for page in pdf_writer.pages:
            # Remove unnecessary page attributes
            for key in ['/Rotate', '/CropBox', '/BleedBox', '/TrimBox', '/ArtBox']:
                if key in page and key != '/MediaBox':  # Keep MediaBox as it's required
                    del page[key]
            
            # Optimize resources
            if '/Resources' in page:
                resources = page['/Resources']
                # Remove unused resources
                for key in ['/Font', '/XObject', '/ExtGState', '/ColorSpace', '/Pattern', '/Shading', '/Properties']:
                    if key in resources:
                        resource_dict = resources[key]
                        if isinstance(resource_dict, dict):
                            for res_key in list(resource_dict.keys()):
                                if not res_key.startswith('/'):
                                    del resource_dict[res_key]
    except Exception as e:
        print(f"Error in structure optimization: {str(e)}")

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
                    'name': 'Structure Optimization',
                    'description': 'Focuses on PDF structure optimization',
                    'optimize_objects': True,
                    'remove_metadata': True
                }
            ]
        
        best_compressed_size = original_size
        best_algorithm = None
        
        for algo in algorithms:
            try:
                # Create a temporary output path for this attempt
                temp_output = f"{output_path}.temp"
                temp_writer = PdfWriter()
                
                # Process each page
                for page in reader.pages:
                    # Add page to writer
                    temp_writer.add_page(page)
                    
                    if is_lossy:
                        # Compress images if enabled
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
                                        # print(f"Error in image compression: {str(e)}")
                                        pass
                
                # Optimize structure if enabled
                if algo.get('optimize_objects', False):
                    optimize_pdf_structure(temp_writer)
                
                # Write to temporary file with compression
                with open(temp_output, 'wb') as f:
                    temp_writer.write(f)
                
                # Get compressed size
                compressed_size = os.path.getsize(temp_output)
                
                # If this attempt produced better compression, keep it
                if compressed_size < best_compressed_size:
                    best_compressed_size = compressed_size
                    best_algorithm = (algo['name'], algo['description'])
                    # Move the temporary file to the final output path
                    if os.path.exists(output_path):
                        os.remove(output_path)
                    os.rename(temp_output, output_path)
                else:
                    # Remove the temporary file
                    os.remove(temp_output)
                
            except Exception as e:
                print(f"Error in {algo['name']}: {str(e)}")
                if os.path.exists(temp_output):
                    os.remove(temp_output)
                continue
        
        # If no compression was successful, try one last time with maximum compression
        if best_compressed_size >= original_size:
            try:
                # Create a new writer with maximum compression
                final_writer = PdfWriter()
                
                # Copy all pages
                for page in reader.pages:
                    final_writer.add_page(page)
                
                # Apply maximum optimization
                optimize_pdf_structure(final_writer)
                
                # Write with maximum compression
                with open(output_path, 'wb') as f:
                    final_writer.write(f)
                
                # Check if we achieved any compression
                final_size = os.path.getsize(output_path)
                if final_size < original_size:
                    return {
                        'success': True,
                        'original_size': original_size,
                        'compressed_size': final_size,
                        'ratio': original_size / final_size if final_size > 0 else 1,
                        'algorithm': 'Maximum Structure Optimization',
                        'description': 'Applied maximum structure optimization and compression'
                    }
            except Exception as e:
                print(f"Error in final compression attempt: {str(e)}")
            
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

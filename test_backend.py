import requests
import os
import io

BASE_URL = 'http://localhost:8080'

def test_upload_text():
    print("\nTesting Text Upload...")
    content = "This is a test file content. " * 100
    files = {'files': ('test.txt', content, 'text/plain')}
    data = {
        'fileType': 'text',
        'isLossy': 'false',
        'quality': '50'
    }
    
    try:
        # Test Metadata Endpoint
        print("1. Testing /compress/metadata...")
        response = requests.post(f'{BASE_URL}/compress/metadata', files=files, data=data)
        print(f"Status: {response.status_code}")
        print(f"Response: {response.text}")
        
        if response.status_code != 200:
            print("FAILED")
            return

        # Test File Endpoint
        print("2. Testing /compress/file...")
        # Need to reset file pointer or create new one
        files = {'files': ('test.txt', content, 'text/plain')}
        response = requests.post(f'{BASE_URL}/compress/file', files=files, data=data)
        print(f"Status: {response.status_code}")
        
        if response.status_code == 200:
            print(f"Success! Received {len(response.content)} bytes")
        else:
            print(f"FAILED: {response.text}")
            
    except Exception as e:
        print(f"Error: {e}")

def test_upload_image():
    print("\nTesting Image Upload...")
    # Create a simple dummy image
    from PIL import Image
    img = Image.new('RGB', (100, 100), color = 'red')
    img_byte_arr = io.BytesIO()
    img.save(img_byte_arr, format='PNG')
    img_byte_arr.seek(0)
    
    files = {'files': ('test.png', img_byte_arr, 'image/png')}
    data = {
        'fileType': 'image',
        'isLossy': 'true',
        'quality': '50'
    }
    
    try:
        print("1. Testing /compress/metadata...")
        response = requests.post(f'{BASE_URL}/compress/metadata', files=files, data=data)
        print(f"Status: {response.status_code}")
        print(f"Response: {response.text}")
        
        if response.status_code != 200:
            print("FAILED")
            return

        print("2. Testing /compress/file...")
        img_byte_arr.seek(0)
        files = {'files': ('test.png', img_byte_arr, 'image/png')}
        response = requests.post(f'{BASE_URL}/compress/file', files=files, data=data)
        print(f"Status: {response.status_code}")
        
        if response.status_code == 200:
            print(f"Success! Received {len(response.content)} bytes")
        else:
            print(f"FAILED: {response.text}")

    except Exception as e:
        print(f"Error: {e}")

if __name__ == '__main__':
    try:
        test_upload_text()
        test_upload_image()
    except Exception as e:
        print(f"Test Execution Error: {e}")

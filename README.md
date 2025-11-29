# CompressoX - Advanced File Compression Application

CompressoX is a powerful, full-stack file compression application designed to handle various file formats including Images, PDFs, Videos, DOCX, and Text files. It offers both lossy and lossless compression algorithms, providing users with flexibility between file size reduction and quality preservation.

## 🚀 Features

-   **Multi-Format Support**: Compress Images (JPG, PNG, etc.), PDFs, Videos (MP4, AVI, etc.), DOCX, and Text files.
-   **Advanced Algorithms**:
    -   **Images**: Intelligent resizing, quality adjustment, and format optimization.
    -   **PDFs**: Structure optimization, image downsampling, and content stream compression.
    -   **Videos**: Motion compensation, DCT compression, and frame optimization.
    -   **DOCX**: Image compression within documents and XML structure optimization.
    -   **Text**: Huffman coding, LZW, and other lossless techniques.
-   **Customizable Settings**: Choose between Lossy and Lossless modes, and adjust quality levels.
-   **Real-time Feedback**: View compression progress and results instantly.
-   **Secure**: Files are processed locally and cleaned up automatically.

## 🛠️ Tech Stack

-   **Backend**: Python, Flask
-   **Frontend**: HTML5, CSS3, JavaScript
-   **Libraries**:
    -   `Pillow` (Image processing)
    -   `PyPDF2` (PDF manipulation)
    -   `python-docx` (Word document processing)
    -   `OpenCV` (Video processing)
    -   `NumPy` (Numerical operations)

## 📦 Installation

### Prerequisites

-   Python 3.8+
-   pip (Python package manager)

### Backend Setup

1.  Clone the repository:
    ```bash
    git clone <repository-url>
    cd CompressoX-File-Compressor-application
    ```

2.  Install dependencies:
    ```bash
    pip install -r requirements.txt
    ```

3.  Run the backend server:
    ```bash
    python CompressoX_Backend/app.py
    ```
    The server will start on `http://localhost:8080`.

### Frontend Setup

1.  Navigate to the `frontend` directory.
2.  Open `index.html` in your preferred web browser.
    -   Alternatively, you can serve it using a simple HTTP server:
        ```bash
        cd frontend
        python -m http.server 3000
        ```
        Then open `http://localhost:3000` in your browser.

## 📖 Usage

1.  Open the application in your browser.
2.  Select the file type you want to compress (Image, PDF, Video, etc.).
3.  Upload your file.
4.  Configure compression settings (Quality, Lossy/Lossless).
5.  Click **Compress**.
6.  Download your compressed file once the process is complete.

## 🤝 Contributing

Contributions are welcome! Please feel free to submit a Pull Request.

## 📄 License

This project is licensed under the MIT License.
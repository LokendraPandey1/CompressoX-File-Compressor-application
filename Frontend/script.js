// DOM Elements
const form = document.getElementById('compressionForm');
const fileInput = document.getElementById('fileInput');
const statusContainer = document.getElementById('statusContainer');
const statusMessage = document.getElementById('statusMessage');
const progressBar = document.querySelector('.progress-bar');
const progress = document.querySelector('.progress-fill');
const progressText = document.getElementById('progressText');
const downloadLink = document.getElementById('downloadLink');
const compressBtn = document.querySelector('.btn');
const btnText = document.querySelector('.btn-text');
const filePreviews = document.getElementById('filePreviews');
const previewContainer = document.querySelector('.preview-grid');
const clearBtn = document.querySelector('.clear');

// API Configuration
const API_URL = 'http://localhost:8080/compress';

// File type detection
const FILE_TYPES = {
    // Images
    'image/jpeg': 'image',
    'image/png': 'image',
    'image/gif': 'image',
    'image/webp': 'image',
    'image/svg+xml': 'image',
    // Documents
    'application/pdf': 'pdf',
    'application/vnd.openxmlformats-officedocument.wordprocessingml.document': 'docx',
    'application/msword': 'doc',
    'text/plain': 'text',
    'text/html': 'text',
    'text/css': 'text',
    'text/javascript': 'text',
    // Videos
    'video/mp4': 'video',
    'video/webm': 'video',
    'video/ogg': 'video',
    'video/quicktime': 'video'
};

// Event Listeners
form.addEventListener('submit', handleSubmit);
fileInput.addEventListener('change', handleFileSelect);
fileInput.addEventListener('dragover', handleDragOver);
fileInput.addEventListener('drop', handleDrop);
clearBtn.addEventListener('click', clearFiles);

// Handle file selection
function handleFileSelect() {
    const files = fileInput.files;
    if (files.length > 0) {
        compressBtn.disabled = false;
        createFilePreviews();
    } else {
        compressBtn.disabled = true;
        filePreviews.classList.add('hidden');
    }
}

// Handle drag and drop
function handleDragOver(e) {
    e.preventDefault();
    e.stopPropagation();
    fileInput.parentElement.classList.add('drag-over');
}

function handleDrop(e) {
    e.preventDefault();
    e.stopPropagation();
    fileInput.parentElement.classList.remove('drag-over');
    fileInput.files = e.dataTransfer.files;
    handleFileSelect();
}

// Clear all files
function clearFiles() {
    fileInput.value = '';
    filePreviews.classList.add('hidden');
    compressBtn.disabled = true;
}

// Create file previews
function createFilePreviews() {
    const files = fileInput.files;
    
    if (files.length === 0) {
        filePreviews.classList.add('hidden');
        return;
    }
    
    filePreviews.classList.remove('hidden');
    previewContainer.innerHTML = '';
    
    Array.from(files).forEach((file, index) => {
        const fileType = detectFileType(file);
        const previewItem = document.createElement('div');
        previewItem.className = 'preview-item';
        previewItem.dataset.index = index;
        
        // Add click event to open file
        previewItem.addEventListener('click', (e) => {
            // Don't open if clicking the remove button
            if (!e.target.classList.contains('preview-remove')) {
                const fileToOpen = fileInput.files[index];
                if (fileToOpen) {
                    openFile(fileToOpen);
                }
            }
        });
        
        // Create remove button
        const removeBtn = document.createElement('div');
        removeBtn.className = 'preview-remove';
        removeBtn.innerHTML = '×';
        removeBtn.addEventListener('click', (e) => {
            e.stopPropagation();
            removeFile(index);
        });
        previewItem.appendChild(removeBtn);
        
        // Create preview based on file type
        if (fileType === 'image') {
            const img = document.createElement('img');
            img.className = 'preview-image';
            img.src = URL.createObjectURL(file);
            previewItem.appendChild(img);
        } else if (fileType === 'video') {
            const video = document.createElement('video');
            video.className = 'preview-video';
            video.src = URL.createObjectURL(file);
            video.controls = false;
            previewItem.appendChild(video);
        } else {
            // Document or other file types
            const docPreview = document.createElement('div');
            docPreview.className = 'preview-document';
            
            // Add appropriate icon based on file type
            const icon = document.createElement('div');
            icon.className = 'preview-document-icon';
            
            if (fileType === 'pdf') {
                icon.innerHTML = '📄';
            } else if (fileType === 'docx' || fileType === 'doc') {
                icon.innerHTML = '📝';
            } else if (fileType === 'text') {
                icon.innerHTML = '📋';
            } else {
                icon.innerHTML = '📁';
            }
            
            const fileName = document.createElement('div');
            fileName.className = 'preview-document-name';
            fileName.textContent = file.name;
            
            docPreview.appendChild(icon);
            docPreview.appendChild(fileName);
            previewItem.appendChild(docPreview);
        }
        
        previewContainer.appendChild(previewItem);
    });
}

// Open file in new tab/window
function openFile(file) {
    const fileURL = URL.createObjectURL(file);
    window.open(fileURL, '_blank');
}

// Remove file from input
function removeFile(index) {
    const dt = new DataTransfer();
    const files = fileInput.files;
    
    for (let i = 0; i < files.length; i++) {
        if (i !== index) {
            dt.items.add(files[i]);
        }
    }
    
    fileInput.files = dt.files;
    handleFileSelect();
}

// Show status message
function showStatus(message, isError = false) {
    statusContainer.classList.remove('hidden');
    statusMessage.textContent = message;
    statusMessage.style.color = isError ? '#e53e3e' : '#4a5568';
}

// Update progress bar
function updateProgress(percent) {
    progressBar.classList.remove('hidden');
    progress.style.width = `${percent}%`;
    progressText.textContent = `${percent}%`;
}

// Toggle loading state
function setLoading(isLoading) {
    compressBtn.disabled = isLoading;
    btnText.textContent = isLoading ? 'Compressing...' : 'Compress';
}

// Detect file type from MIME type
function detectFileType(file) {
    const mimeType = file.type;
    return FILE_TYPES[mimeType] || 'unknown';
}

// Handle form submission
async function handleSubmit(e) {
    e.preventDefault();

    const files = fileInput.files;

    if (!files.length) {
        showStatus('Please select files to compress', true);
        return;
    }

    try {
        setLoading(true);
        showStatus('Uploading files...');
        updateProgress(25);

        const formData = new FormData();
        for (let file of files) {
            formData.append('files', file);
            // Automatically detect and append file type
            const fileType = detectFileType(file);
            formData.append('fileType', fileType);
        }

        const response = await fetch(API_URL, {
            method: 'POST',
            body: formData
        });

        if (!response.ok) {
            throw new Error(`HTTP error! status: ${response.status}`);
        }

        updateProgress(75);
        showStatus('Compression successful!');

        const blob = await response.blob();
        const url = window.URL.createObjectURL(blob);
        downloadLink.href = url;
        downloadLink.classList.remove('hidden');
        updateProgress(100);

    } catch (error) {
        console.error('Error:', error);
        showStatus('Error: ' + error.message, true);
    } finally {
        setLoading(false);
    }
} 
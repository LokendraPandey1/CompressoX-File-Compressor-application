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

const API_URL = 'http://localhost:8080';

const FILE_TYPES = {
    'image/jpeg': 'image',
    'image/png': 'image',
    'image/gif': 'image',
    'image/webp': 'image',
    'image/svg+xml': 'image',
    'application/pdf': 'pdf',
    'application/vnd.openxmlformats-officedocument.wordprocessingml.document': 'docx',
    'application/msword': 'docx',
    'text/plain': 'text',
    'text/html': 'text',
    'text/css': 'text',
    'text/javascript': 'text',
    'video/mp4': 'video',
    'video/webm': 'video',
    'video/ogg': 'video',
    'video/quicktime': 'video'
};

form.addEventListener('submit', handleSubmit);
fileInput.addEventListener('change', handleFileSelect);
clearBtn.addEventListener('click', clearFiles);

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

function clearFiles() {
    fileInput.value = '';
    filePreviews.classList.add('hidden');
    compressBtn.disabled = true;
}

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

        const removeBtn = document.createElement('div');
        removeBtn.className = 'preview-remove';
        removeBtn.innerHTML = '×';
        removeBtn.addEventListener('click', (e) => {
            e.stopPropagation();
            removeFile(index);
        });
        previewItem.appendChild(removeBtn);

        if (fileType === 'image') {
            const img = document.createElement('img');
            img.className = 'preview-image';
            img.src = URL.createObjectURL(file);
            previewItem.appendChild(img);
        } else {
            const docPreview = document.createElement('div');
            docPreview.className = 'preview-document';
            const icon = document.createElement('div');
            icon.className = 'preview-document-icon';
            icon.innerHTML = '📄';
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

function detectFileType(file) {
    return FILE_TYPES[file.type] || 'unknown';
}

function showStatus(message, isError = false) {
    statusContainer.classList.remove('hidden');
    statusMessage.textContent = message;
    statusMessage.style.color = isError ? '#e53e3e' : '#4a5568';
}

function updateProgress(percent) {
    progress.style.width = `${percent}%`;
    progressText.textContent = `${percent}%`;
}

function setLoading(isLoading) {
    compressBtn.disabled = isLoading;
    btnText.textContent = isLoading ? 'Compressing...' : 'Compress File';
}

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

async function handleSubmit(e) {
    e.preventDefault();

    const files = fileInput.files;
    if (!files.length) {
        showStatus('Please select a file to compress.', true);
        return;
    }

    const formData = new FormData();
    const fileType = detectFileType(files[0]);
    formData.append('fileType', fileType);

    for (let file of files) {
        formData.append('files', file);
    }

    formData.append('isLossy', document.querySelector('input[name="isLossy"]:checked').value);
    formData.append('compressionType', document.getElementById('compressionType').value);
    formData.append('quality', document.getElementById('quality').value);

    try {
        setLoading(true);
        showStatus('Uploading files...');
        updateProgress(25);

        const response = await fetch(API_URL, {
            method: 'POST',
            body: formData
        });

        if (!response.ok) {
            throw new Error(`Compression failed. Server returned ${response.status}`);
        }

        updateProgress(75);
        showStatus('Compression successful! Preparing download...');

        const blob = await response.blob();
        const url = window.URL.createObjectURL(blob);
        downloadLink.href = url;
        downloadLink.download = 'compressed_output.txt';
        downloadLink.classList.remove('hidden');

        updateProgress(100);
    } catch (err) {
        console.error(err);
        showStatus('Error: ' + err.message, true);
        updateProgress(0);
    } finally {
        setLoading(false);
    }
}

// Handle compression options
document.addEventListener('DOMContentLoaded', function() {
    const isLossyRadios = document.querySelectorAll('input[name="isLossy"]');
    const compressionTypeSelect = document.getElementById('compressionType');
    const qualityInput = document.getElementById('quality');
    const qualityValue = document.getElementById('qualityValue');

    // Update quality value display
    qualityInput.addEventListener('input', function(e) {
        qualityValue.textContent = e.target.value + '%';
    });

    // Handle compression mode change
    isLossyRadios.forEach(radio => {
        radio.addEventListener('change', function() {
            const isLossy = this.value === 'true';
            const lossyOptions = compressionTypeSelect.querySelector('.lossy-options');
            const losslessOptions = compressionTypeSelect.querySelector('.lossless-options');
            
            // Show/hide appropriate options
            if (isLossy) {
                lossyOptions.style.display = 'block';
                losslessOptions.style.display = 'none';
                compressionTypeSelect.value = 'dct';
            } else {
                lossyOptions.style.display = 'none';
                losslessOptions.style.display = 'block';
                compressionTypeSelect.value = 'rle';
            }
        });
    });

    // Initialize compression type options
    const initialIsLossy = document.querySelector('input[name="isLossy"]:checked').value === 'true';
    const lossyOptions = compressionTypeSelect.querySelector('.lossy-options');
    const losslessOptions = compressionTypeSelect.querySelector('.lossless-options');
    
    if (initialIsLossy) {
        losslessOptions.style.display = 'none';
    } else {
        lossyOptions.style.display = 'none';
    }
});

// Update quality value display
document.getElementById('quality').addEventListener('input', function(e) {
    document.getElementById('qualityValue').textContent = e.target.value + '%';
});

// Remove all existing form submission handlers
form.removeEventListener('submit', handleSubmit);

// Single form submission handler
form.addEventListener('submit', async function(e) {
    e.preventDefault();
    
    const files = fileInput.files;
    if (!files.length) {
        showStatus('Please select a file to compress.', true);
        return;
    }

    const formData = new FormData();
    const isLossy = document.querySelector('input[name="compressionMode"]:checked').value === 'lossy';
    const quality = parseInt(document.getElementById('quality').value);

    // Add file and compression options
    formData.append('files', files[0]);
    formData.append('fileType', detectFileType(files[0]));
    formData.append('isLossy', isLossy);
    formData.append('quality', quality);

    try {
        setLoading(true);
        showStatus('Uploading file...');
        updateProgress(25);

        // First request to get compression metadata
        const metadataResponse = await fetch(`${API_URL}/compress/metadata`, {
            method: 'POST',
            body: formData
        });

        if (!metadataResponse.ok) {
            const errorData = await metadataResponse.json();
            throw new Error(errorData.error || `Compression failed. Server returned ${metadataResponse.status}`);
        }

        const metadata = await metadataResponse.json();
        
        // Update compression info with the metadata
        updateCompressionInfo({
            success: true,
            algorithm: metadata.algorithm,
            description: metadata.description,
            original_size: metadata.original_size,
            compressed_size: metadata.compressed_size,
            ratio: metadata.ratio
        });

        updateProgress(50);
        showStatus('Compressing file...');

        // Second request to get the compressed file
        const fileResponse = await fetch(`${API_URL}/compress/file`, {
            method: 'POST',
            body: formData
        });

        if (!fileResponse.ok) {
            throw new Error(`Failed to get compressed file. Server returned ${fileResponse.status}`);
        }

        updateProgress(75);
        showStatus('Compression successful! Preparing download...');

        // Create download link for the compressed file
        const compressedBlob = await fileResponse.blob();
        const url = window.URL.createObjectURL(compressedBlob);
        downloadLink.href = url;
        downloadLink.download = 'compressed_' + files[0].name;
        downloadLink.classList.remove('hidden');

        updateProgress(100);
        showStatus('Compression completed successfully!');
    } catch (error) {
        console.error('Compression error:', error);
        showStatus('Error: ' + error.message, true);
        updateProgress(0);
        
        // Show error in compression info
        updateCompressionInfo({
            success: false,
            error: error.message
        });
    } finally {
        setLoading(false);
    }
});

function formatFileSize(bytes) {
    if (bytes === 0) return '0 Bytes';
    const k = 1024;
    const sizes = ['Bytes', 'KB', 'MB', 'GB'];
    const i = Math.floor(Math.log(bytes) / Math.log(k));
    return parseFloat((bytes / Math.pow(k, i)).toFixed(2)) + ' ' + sizes[i];
}

function updateCompressionInfo(response) {
    const compressionInfo = document.querySelector('.compression-info');
    const algorithmUsed = document.getElementById('algorithmUsed');
    const algorithmDescription = document.getElementById('algorithmDescription');
    const originalSize = document.getElementById('originalSize');
    const compressedSize = document.getElementById('compressedSize');
    const compressionRatio = document.getElementById('compressionRatio');

    if (response.success) {
        // Update algorithm information
        algorithmUsed.textContent = response.algorithm || 'Unknown';
        algorithmDescription.textContent = response.description || 'No description available';

        // Update size information
        originalSize.textContent = formatFileSize(response.original_size);
        compressedSize.textContent = formatFileSize(response.compressed_size);
        compressionRatio.textContent = response.ratio.toFixed(2) + 'x';

        // Show compression info
        compressionInfo.style.display = 'block';
    } else {
        // Handle error
        algorithmUsed.textContent = 'Error';
        algorithmDescription.textContent = response.error || 'Compression failed';
        originalSize.textContent = '-';
        compressedSize.textContent = '-';
        compressionRatio.textContent = '-';
    }
}

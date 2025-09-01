// Voice Transcriber Web App JavaScript
class VoiceTranscriberApp {
    constructor() {
        this.socket = null;
        this.currentJobId = null;
        this.uploadedFile = null;
        this.initializeApp();
    }

    initializeApp() {
        this.setupSocketConnection();
        this.setupFileUpload();
        this.setupEventListeners();
    }

    setupSocketConnection() {
        this.socket = io();
        
        this.socket.on('connect', () => {
            console.log('Connected to server');
        });

        this.socket.on('progress_update', (data) => {
            this.updateProgress(data);
        });

        this.socket.on('disconnect', () => {
            console.log('Disconnected from server');
        });
    }

    setupFileUpload() {
        const uploadArea = document.getElementById('uploadArea');
        const fileInput = document.getElementById('fileInput');

        // Drag and drop events
        uploadArea.addEventListener('dragover', (e) => {
            e.preventDefault();
            uploadArea.classList.add('dragover');
        });

        uploadArea.addEventListener('dragleave', () => {
            uploadArea.classList.remove('dragover');
        });

        uploadArea.addEventListener('drop', (e) => {
            e.preventDefault();
            uploadArea.classList.remove('dragover');
            
            const files = e.dataTransfer.files;
            if (files.length > 0) {
                this.handleFileSelect(files[0]);
            }
        });

        // Click to upload
        uploadArea.addEventListener('click', () => {
            fileInput.click();
        });

        fileInput.addEventListener('change', (e) => {
            if (e.target.files.length > 0) {
                this.handleFileSelect(e.target.files[0]);
            }
        });
    }

    setupEventListeners() {
        // Update transcribe button state when file is selected
        document.getElementById('fileInput').addEventListener('change', () => {
            this.updateTranscribeButton();
        });
    }

    async handleFileSelect(file) {
        // Validate file type
        const allowedTypes = ['audio/wav', 'audio/mp3', 'audio/m4a', 'audio/flac', 'audio/ogg', 'audio/wma', 'audio/aac', 'video/mp4'];
        const fileExtension = file.name.split('.').pop().toLowerCase();
        const allowedExtensions = ['wav', 'mp3', 'm4a', 'flac', 'ogg', 'wma', 'aac', 'mp4'];
        
        if (!allowedExtensions.includes(fileExtension)) {
            this.showError('Invalid file type. Please select an audio file.');
            return;
        }

        // Validate file size (500MB limit)
        const maxSize = 500 * 1024 * 1024; // 500MB in bytes
        if (file.size > maxSize) {
            this.showError('File size too large. Maximum size is 500MB.');
            return;
        }

        try {
            this.showLoading(true);
            
            // Upload file
            const formData = new FormData();
            formData.append('file', file);

            const response = await fetch('/api/upload', {
                method: 'POST',
                body: formData
            });

            const result = await response.json();

            if (result.success) {
                this.uploadedFile = result;
                this.displayFileInfo(result);
                this.updateTranscribeButton();
            } else {
                this.showError(result.error || 'Upload failed');
            }
        } catch (error) {
            console.error('Upload error:', error);
            this.showError('Upload failed. Please try again.');
        } finally {
            this.showLoading(false);
        }
    }

    displayFileInfo(fileInfo) {
        const fileInfoDiv = document.getElementById('fileInfo');
        const fileName = document.getElementById('fileName');
        const fileSize = document.getElementById('fileSize');

        fileName.textContent = fileInfo.original_name;
        fileSize.textContent = `${fileInfo.size_mb} MB`;

        fileInfoDiv.style.display = 'block';
    }

    clearFile() {
        this.uploadedFile = null;
        document.getElementById('fileInfo').style.display = 'none';
        document.getElementById('fileInput').value = '';
        this.updateTranscribeButton();
        this.hideProgress();
        this.hideResults();
    }

    updateTranscribeButton() {
        const transcribeBtn = document.getElementById('transcribeBtn');
        transcribeBtn.disabled = !this.uploadedFile;
    }

    async startTranscription() {
        if (!this.uploadedFile) {
            this.showError('Please select a file first');
            return;
        }

        try {
            const modelSize = document.getElementById('modelSelect').value;
            const enableSpeakerDiarization = document.getElementById('speakerDiarization').checked;
            const language = document.getElementById('languageSelect').value;

            const response = await fetch('/api/transcribe', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json'
                },
                body: JSON.stringify({
                    filename: this.uploadedFile.filename,
                    model_size: modelSize,
                    enable_speaker_diarization: enableSpeakerDiarization,
                    language: language
                })
            });

            const result = await response.json();

            if (result.success) {
                this.currentJobId = result.job_id;
                this.showProgress();
                this.hideResults();
            } else {
                this.showError(result.error || 'Failed to start transcription');
            }
        } catch (error) {
            console.error('Transcription start error:', error);
            this.showError('Failed to start transcription. Please try again.');
        }
    }

    updateProgress(data) {
        if (data.job_id !== this.currentJobId) return;

        const progressFill = document.getElementById('progressFill');
        const progressPercent = document.getElementById('progressPercent');
        const progressMessage = document.getElementById('progressMessage');
        const progressDetails = document.getElementById('progressDetails');

        // Update progress bar
        progressFill.style.width = `${data.progress}%`;
        progressPercent.textContent = `${data.progress}%`;
        progressMessage.textContent = data.message;

        // Update progress details
        let detailsHtml = `
            <div class="progress-detail">
                <strong>Status:</strong> <span class="status-${data.status}">${this.getStatusText(data.status)}</span>
            </div>
        `;

        if (data.result) {
            detailsHtml += `
                <div class="progress-detail">
                    <strong>Language:</strong> ${data.result.language}
                </div>
                <div class="progress-detail">
                    <strong>Duration:</strong> ${data.result.duration}
                </div>
                <div class="progress-detail">
                    <strong>Speakers:</strong> ${data.result.speakers}
                </div>
            `;
        }

        progressDetails.innerHTML = detailsHtml;

        // Handle completion
        if (data.status === 'completed') {
            this.showResults(data.result);
            this.hideProgress();
        } else if (data.status === 'error') {
            this.showError(data.message);
            this.hideProgress();
        }
    }

    getStatusText(status) {
        const statusMap = {
            'starting': 'Starting...',
            'loading_model': 'Loading AI Model...',
            'transcribing': 'Transcribing Audio...',
            'processing': 'Processing Results...',
            'completed': 'Completed',
            'error': 'Error'
        };
        return statusMap[status] || status;
    }

    showProgress() {
        document.getElementById('progressSection').style.display = 'block';
        document.getElementById('transcribeBtn').disabled = true;
    }

    hideProgress() {
        document.getElementById('progressSection').style.display = 'none';
        document.getElementById('transcribeBtn').disabled = false;
    }

    showResults(result) {
        const resultsSection = document.getElementById('resultsSection');
        const resultSummary = document.getElementById('resultSummary');

        let summaryHtml = `
            <div class="result-item">
                <i class="fas fa-check-circle text-success"></i>
                <strong>Transcription completed successfully!</strong>
            </div>
            <div class="result-item">
                <i class="fas fa-language"></i>
                <strong>Language:</strong> ${result.language}
            </div>
            <div class="result-item">
                <i class="fas fa-clock"></i>
                <strong>Duration:</strong> ${result.duration}
            </div>
            <div class="result-item">
                <i class="fas fa-users"></i>
                <strong>Speakers:</strong> ${result.speakers}
            </div>
            <div class="result-item">
                <i class="fas fa-file-alt"></i>
                <strong>Output File:</strong> ${result.output_file}
            </div>
        `;

        resultSummary.innerHTML = summaryHtml;
        resultsSection.style.display = 'block';

        // Store result for download
        this.currentResult = result;
    }

    hideResults() {
        document.getElementById('resultsSection').style.display = 'none';
    }

    downloadResult() {
        if (this.currentResult && this.currentResult.output_file) {
            const downloadUrl = `/api/download/${this.currentResult.output_file}`;
            const link = document.createElement('a');
            link.href = downloadUrl;
            link.download = this.currentResult.output_file;
            document.body.appendChild(link);
            link.click();
            document.body.removeChild(link);
        }
    }

    startNewTranscription() {
        this.clearFile();
        this.hideProgress();
        this.hideResults();
        this.currentJobId = null;
        this.currentResult = null;
    }

    showLoading(show) {
        document.getElementById('loadingOverlay').style.display = show ? 'flex' : 'none';
    }

    showError(message) {
        // Create a simple error notification
        const errorDiv = document.createElement('div');
        errorDiv.className = 'error-notification';
        errorDiv.style.cssText = `
            position: fixed;
            top: 20px;
            right: 20px;
            background: #dc3545;
            color: white;
            padding: 15px 20px;
            border-radius: 8px;
            box-shadow: 0 4px 12px rgba(0,0,0,0.15);
            z-index: 10000;
            max-width: 400px;
            animation: slideIn 0.3s ease;
        `;
        errorDiv.innerHTML = `
            <div style="display: flex; align-items: center; gap: 10px;">
                <i class="fas fa-exclamation-triangle"></i>
                <span>${message}</span>
                <button onclick="this.parentElement.parentElement.remove()" style="background: none; border: none; color: white; cursor: pointer; margin-left: auto;">
                    <i class="fas fa-times"></i>
                </button>
            </div>
        `;

        document.body.appendChild(errorDiv);

        // Auto-remove after 5 seconds
        setTimeout(() => {
            if (errorDiv.parentElement) {
                errorDiv.remove();
            }
        }, 5000);
    }
}

// Global functions for HTML onclick handlers
function startTranscription() {
    app.startTranscription();
}

function clearFile() {
    app.clearFile();
}

function downloadResult() {
    app.downloadResult();
}

function startNewTranscription() {
    app.startNewTranscription();
}

// Initialize app when DOM is loaded
document.addEventListener('DOMContentLoaded', () => {
    window.app = new VoiceTranscriberApp();
});

// Add CSS for animations
const style = document.createElement('style');
style.textContent = `
    @keyframes slideIn {
        from {
            transform: translateX(100%);
            opacity: 0;
        }
        to {
            transform: translateX(0);
            opacity: 1;
        }
    }
    
    .result-item {
        display: flex;
        align-items: center;
        gap: 10px;
        margin-bottom: 10px;
        padding: 8px 0;
    }
    
    .result-item i {
        width: 20px;
        text-align: center;
    }
    
    .text-success {
        color: #28a745;
    }
    
    .progress-detail {
        margin-bottom: 8px;
        padding: 5px 0;
    }
`;
document.head.appendChild(style);

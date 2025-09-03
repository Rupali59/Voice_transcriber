// Voice Transcriber Web App JavaScript
class VoiceTranscriberApp {
    constructor() {
        this.socket = null;
        this.currentJobId = null;
        this.uploadedFile = null;
        this.startTime = null;
        this.refreshInterval = null;
        this.currentResult = null;
        this.initializeApp();
    }

    initializeApp() {
        this.setupSocketConnection();
        this.setupFileUpload();
        this.setupEventListeners();
        this.loadMyFiles();
        this.loadQuotaInfo();
    }

    setupSocketConnection() {
        this.socket = io();
        
        this.socket.on('connect', () => {
            console.log('Connected to server');
            this.updateConnectionStatus('connected');
        });

        this.socket.on('progress_update', (data) => {
            this.updateProgress(data);
        });

        this.socket.on('disconnect', () => {
            console.log('Disconnected from server');
            this.updateConnectionStatus('disconnected');
        });

        this.socket.on('connect_error', () => {
            console.log('Connection error');
            this.updateConnectionStatus('disconnected');
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
                this.showSuccess('File uploaded successfully!');
                // Refresh file list and quota info
                this.loadMyFiles();
                this.loadQuotaInfo();
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
            const temperature = parseFloat(document.getElementById('temperatureSelect').value);

            const response = await fetch('/api/transcribe', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json'
                },
                body: JSON.stringify({
                    filename: this.uploadedFile.filename,
                    model_size: modelSize,
                    enable_speaker_diarization: enableSpeakerDiarization,
                    language: language,
                    temperature: temperature
                })
            });

            const result = await response.json();

            if (result.success) {
                this.currentJobId = result.job_id;
                this.startTime = new Date();
                this.showProgress();
                this.hideResults();
                this.startStatusRefresh();
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
        this.updateStatusInfo();
    }

    hideProgress() {
        document.getElementById('progressSection').style.display = 'none';
        document.getElementById('transcribeBtn').disabled = false;
        this.stopStatusRefresh();
    }

    updateStatusInfo() {
        if (this.currentJobId) {
            document.getElementById('jobId').textContent = this.currentJobId;
        }
        
        if (this.startTime) {
            const timeString = this.startTime.toLocaleTimeString();
            document.getElementById('startTime').textContent = timeString;
        }
    }

    updateConnectionStatus(status) {
        const statusElement = document.getElementById('connectionStatus');
        if (statusElement) {
            statusElement.className = `status-${status}`;
            statusElement.textContent = status.charAt(0).toUpperCase() + status.slice(1);
        }
    }

    startStatusRefresh() {
        // Refresh status every 5 seconds as a fallback
        this.refreshInterval = setInterval(() => {
            if (this.currentJobId) {
                this.refreshStatus();
            }
        }, 5000);
    }

    stopStatusRefresh() {
        if (this.refreshInterval) {
            clearInterval(this.refreshInterval);
            this.refreshInterval = null;
        }
    }

    async refreshStatus() {
        if (!this.currentJobId) return;

        const refreshBtn = document.getElementById('refreshStatusBtn');
        const originalContent = refreshBtn.innerHTML;
        
        try {
            // Show loading state
            refreshBtn.innerHTML = '<i class="fas fa-sync-alt btn-refreshing"></i> Refreshing...';
            refreshBtn.disabled = true;

            const response = await fetch(`/api/job-status/${this.currentJobId}`);
            const result = await response.json();

            if (result.success) {
                // Update progress with the latest status
                this.updateProgress({
                    job_id: this.currentJobId,
                    status: result.status,
                    progress: result.progress || 0,
                    message: result.message || 'Processing...',
                    result: result.result
                });
            } else {
                console.error('Failed to refresh status:', result.error);
            }
        } catch (error) {
            console.error('Error refreshing status:', error);
        } finally {
            // Restore button state
            refreshBtn.innerHTML = originalContent;
            refreshBtn.disabled = false;
        }
    }

    async cancelTranscription() {
        if (!this.currentJobId) return;

        if (!confirm('Are you sure you want to cancel this transcription?')) {
            return;
        }

        try {
            const response = await fetch(`/api/cancel-job/${this.currentJobId}`, {
                method: 'POST'
            });
            
            const result = await response.json();
            
            if (result.success) {
                this.showError('Transcription cancelled');
                this.hideProgress();
                this.hideResults();
                this.currentJobId = null;
                this.startTime = null;
            } else {
                this.showError(result.error || 'Failed to cancel transcription');
            }
        } catch (error) {
            console.error('Error cancelling transcription:', error);
            this.showError('Failed to cancel transcription');
        }
    }

    async viewTranscript(filename = null) {
        // If no filename provided, try to get from current result
        if (!filename && this.currentResult && this.currentResult.output_file) {
            filename = this.currentResult.output_file;
        }
        
        // If still no filename, show error
        if (!filename) {
            this.showError('No transcript available to view');
            return;
        }

        document.getElementById('transcriptFilename').textContent = filename;
        document.getElementById('transcriptContent').textContent = 'Loading transcript...';
        
        // Show modal
        const modal = new bootstrap.Modal(document.getElementById('transcriptModal'));
        modal.show();
        
        try {
            const response = await fetch(`/api/transcript/${filename}`);
            const data = await response.json();
            
            if (data.success) {
                document.getElementById('transcriptContent').textContent = data.content;
            } else {
                document.getElementById('transcriptContent').textContent = 'Error loading transcript: ' + data.error;
            }
        } catch (error) {
            console.error('Error loading transcript:', error);
            document.getElementById('transcriptContent').textContent = 'Error loading transcript: ' + error.message;
        }
    }

    downloadTranscript() {
        if (this.currentResult && this.currentResult.output_file) {
            const filename = this.currentResult.output_file;
            const link = document.createElement('a');
            link.href = `/api/download/${filename}`;
            link.download = filename;
            document.body.appendChild(link);
            link.click();
            document.body.removeChild(link);
        } else {
            this.showError('No transcript available to download');
        }
    }

    // File Management Methods
    async loadMyFiles() {
        try {
            const response = await fetch('/api/my-files');
            const data = await response.json();
            
            if (data.success) {
                this.displayMyFiles(data.files);
            } else {
                console.error('Failed to load files:', data.error);
                this.showError('Failed to load your files');
            }
        } catch (error) {
            console.error('Error loading files:', error);
            this.showError('Error loading your files');
        }
    }

    async loadQuotaInfo() {
        try {
            const response = await fetch('/api/my-quota');
            const data = await response.json();
            
            if (data.success) {
                this.displayQuotaInfo(data.stats);
            } else {
                console.error('Failed to load quota info:', data.error);
            }
        } catch (error) {
            console.error('Error loading quota info:', error);
        }
    }

    displayMyFiles(files) {
        const filesList = document.getElementById('filesList');
        
        if (files.length === 0) {
            filesList.innerHTML = `
                <div class="no-files">
                    <i class="fas fa-folder-open"></i>
                    <p>No files uploaded yet</p>
                </div>
            `;
            return;
        }

        filesList.innerHTML = files.map(file => {
            const fileIcon = this.getFileIcon(file.original_name);
            const uploadDate = new Date(file.upload_time).toLocaleString();
            const fileSize = this.formatFileSize(file.size_mb);
            
            return `
                <div class="file-item">
                    <div class="file-info">
                        <div class="file-icon ${fileIcon.type}">
                            <i class="${fileIcon.icon}"></i>
                        </div>
                        <div class="file-details">
                            <h6>${file.original_name}</h6>
                            <p>${fileSize} • Uploaded ${uploadDate}</p>
                        </div>
                    </div>
                    <div class="file-actions">
                        <button class="btn btn-sm btn-outline-info" onclick="app.downloadFile('${file.filename}')">
                            <i class="fas fa-download"></i>
                        </button>
                        <button class="btn btn-sm btn-outline-danger" onclick="app.deleteFile('${file.filename}')">
                            <i class="fas fa-trash"></i>
                        </button>
                    </div>
                </div>
            `;
        }).join('');
    }

    displayQuotaInfo(stats) {
        const quota = stats.quota;
        if (!quota) return;

        // Update quota displays
        document.getElementById('quotaFiles').textContent = `${quota.total_files} / ${stats.limits.max_files_per_ip}`;
        document.getElementById('quotaStorage').textContent = `${quota.total_size_mb.toFixed(1)} MB / ${stats.limits.max_size_mb_per_ip} MB`;
        document.getElementById('quota24hFiles').textContent = `${quota.file_count_24h} / ${stats.limits.max_files_24h_per_ip}`;
        document.getElementById('quota24hStorage').textContent = `${quota.size_mb_24h.toFixed(1)} MB / ${stats.limits.max_size_24h_mb_per_ip} MB`;

        // Add warning styles if approaching limits
        this.updateQuotaWarnings(quota, stats.limits);
    }

    updateQuotaWarnings(quota, limits) {
        const quotaItems = document.querySelectorAll('.quota-item');
        
        // Check file quota
        const fileUsage = quota.total_files / limits.max_files_per_ip;
        if (fileUsage > 0.8) {
            quotaItems[0].classList.add(fileUsage > 0.9 ? 'quota-critical' : 'quota-warning');
            document.getElementById('quotaFiles').classList.add(fileUsage > 0.9 ? 'critical' : 'warning');
        }

        // Check storage quota
        const storageUsage = quota.total_size_mb / limits.max_size_mb_per_ip;
        if (storageUsage > 0.8) {
            quotaItems[1].classList.add(storageUsage > 0.9 ? 'quota-critical' : 'quota-warning');
            document.getElementById('quotaStorage').classList.add(storageUsage > 0.9 ? 'critical' : 'warning');
        }

        // Check 24h file quota
        const file24hUsage = quota.file_count_24h / limits.max_files_24h_per_ip;
        if (file24hUsage > 0.8) {
            quotaItems[2].classList.add(file24hUsage > 0.9 ? 'quota-critical' : 'quota-warning');
            document.getElementById('quota24hFiles').classList.add(file24hUsage > 0.9 ? 'critical' : 'warning');
        }

        // Check 24h storage quota
        const storage24hUsage = quota.size_mb_24h / limits.max_size_24h_mb_per_ip;
        if (storage24hUsage > 0.8) {
            quotaItems[3].classList.add(storage24hUsage > 0.9 ? 'quota-critical' : 'quota-warning');
            document.getElementById('quota24hStorage').classList.add(storage24hUsage > 0.9 ? 'critical' : 'warning');
        }
    }

    getFileIcon(filename) {
        const ext = filename.split('.').pop().toLowerCase();
        const audioExts = ['wav', 'mp3', 'm4a', 'flac', 'ogg', 'wma', 'aac'];
        const videoExts = ['mp4', 'avi', 'mov', 'mkv', 'webm'];
        
        if (audioExts.includes(ext)) {
            return { type: 'audio', icon: 'fas fa-music' };
        } else if (videoExts.includes(ext)) {
            return { type: 'video', icon: 'fas fa-video' };
        } else {
            return { type: 'other', icon: 'fas fa-file' };
        }
    }

    formatFileSize(sizeMB) {
        if (sizeMB < 1) {
            return `${(sizeMB * 1024).toFixed(0)} KB`;
        } else if (sizeMB < 1024) {
            return `${sizeMB.toFixed(1)} MB`;
        } else {
            return `${(sizeMB / 1024).toFixed(1)} GB`;
        }
    }

    async downloadFile(filename) {
        try {
            window.open(`/download/${filename}`, '_blank');
        } catch (error) {
            console.error('Error downloading file:', error);
            this.showError('Error downloading file');
        }
    }

    async deleteFile(filename) {
        if (!confirm('Are you sure you want to delete this file?')) {
            return;
        }

        try {
            const response = await fetch(`/api/my-files/${filename}`, {
                method: 'DELETE'
            });
            const data = await response.json();
            
            if (data.success) {
                this.showSuccess('File deleted successfully');
                this.loadMyFiles();
                this.loadQuotaInfo();
            } else {
                this.showError(data.error || 'Failed to delete file');
            }
        } catch (error) {
            console.error('Error deleting file:', error);
            this.showError('Error deleting file');
        }
    }

    async cleanupMyFiles() {
        if (!confirm('Are you sure you want to delete ALL your files? This action cannot be undone.')) {
            return;
        }

        try {
            const response = await fetch('/api/my-files/cleanup', {
                method: 'POST'
            });
            const data = await response.json();
            
            if (data.success) {
                this.showSuccess(`Cleaned up ${data.deleted_count} files`);
                this.loadMyFiles();
                this.loadQuotaInfo();
            } else {
                this.showError(data.error || 'Failed to cleanup files');
            }
        } catch (error) {
            console.error('Error cleaning up files:', error);
            this.showError('Error cleaning up files');
        }
    }

    showSuccess(message) {
        this.showNotification(message, 'success');
    }

    showError(message) {
        this.showNotification(message, 'error');
    }

    showNotification(message, type) {
        // Create notification element
        const notification = document.createElement('div');
        notification.className = `notification notification-${type}`;
        notification.innerHTML = `
            <i class="fas fa-${type === 'success' ? 'check-circle' : 'exclamation-circle'}"></i>
            <span>${message}</span>
        `;
        
        // Add to page
        document.body.appendChild(notification);
        
        // Show notification
        setTimeout(() => notification.classList.add('show'), 100);
        
        // Remove after 3 seconds
        setTimeout(() => {
            notification.classList.remove('show');
            setTimeout(() => notification.remove(), 300);
        }, 3000);
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
            <div class="result-item">
                <i class="fas fa-eye text-info"></i>
                <strong>Opening transcript viewer...</strong>
            </div>
        `;

        resultSummary.innerHTML = summaryHtml;
        resultsSection.style.display = 'block';

        // Store result for download
        this.currentResult = result;
        
        // Automatically show transcript when transcription completes
        if (result.output_file) {
            setTimeout(() => {
                this.viewTranscript();
            }, 1500); // Small delay to let the results section appear first
        }
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

function refreshStatus() {
    app.refreshStatus();
}

function cancelTranscription() {
    app.cancelTranscription();
}

function viewTranscript(filename = null) {
    app.viewTranscript(filename);
}

function downloadTranscript() {
    app.downloadTranscript();
}

// File Management Functions
function refreshMyFiles() {
    app.loadMyFiles();
    app.loadQuotaInfo();
}

function cleanupMyFiles() {
    app.cleanupMyFiles();
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

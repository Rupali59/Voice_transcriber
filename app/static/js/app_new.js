/**
 * Voice Transcriber Application - Material Design + Tailwind CSS Version
 * Modern, component-based JavaScript for the redesigned interface
 */

class VoiceTranscriberApp {
    constructor() {
        this.socket = null;
        this.currentJobId = null;
        this.uploadedFile = null;
        this.isTranscribing = false;
        
        this.initializeApp();
    }

    initializeApp() {
        this.setupEventListeners();
        this.initializeSocket();
        this.loadMyFiles();
        this.loadQuotaInfo();
        this.checkExistingTranscripts();
    }

    setupEventListeners() {
        // File upload
        const uploadArea = document.getElementById('uploadArea');
        const fileInput = document.getElementById('fileInput');
        
        if (uploadArea) {
            uploadArea.addEventListener('click', () => fileInput.click());
            uploadArea.addEventListener('dragover', this.handleDragOver.bind(this));
            uploadArea.addEventListener('dragleave', this.handleDragLeave.bind(this));
            uploadArea.addEventListener('drop', this.handleDrop.bind(this));
        }

        if (fileInput) {
            fileInput.addEventListener('change', this.handleFileSelect.bind(this));
        }

        // Transcription button
        const transcribeBtn = document.getElementById('transcribeBtn');
        if (transcribeBtn) {
            transcribeBtn.addEventListener('click', this.startTranscription.bind(this));
        }

        // Form validation
        this.setupFormValidation();
    }

    initializeSocket() {
        this.socket = io();
        
        this.socket.on('connect', () => {
            this.updateConnectionStatus('Connected', 'success');
        });

        this.socket.on('disconnect', () => {
            this.updateConnectionStatus('Disconnected', 'error');
        });

        this.socket.on('transcription_progress', (data) => {
            this.updateProgress(data);
        });

        this.socket.on('transcription_complete', (data) => {
            this.handleTranscriptionComplete(data);
        });

        this.socket.on('transcription_error', (data) => {
            this.handleTranscriptionError(data);
        });
    }

    // File Upload Methods
    handleDragOver(e) {
        e.preventDefault();
        e.currentTarget.classList.add('border-primary-500', 'bg-primary-50');
    }

    handleDragLeave(e) {
        e.preventDefault();
        e.currentTarget.classList.remove('border-primary-500', 'bg-primary-50');
    }

    handleDrop(e) {
        e.preventDefault();
        e.currentTarget.classList.remove('border-primary-500', 'bg-primary-50');
        
        const files = e.dataTransfer.files;
        if (files.length > 0) {
            this.processFile(files[0]);
        }
    }

    handleFileSelect(e) {
        const file = e.target.files[0];
        if (file) {
            this.processFile(file);
        }
    }

    processFile(file) {
        if (!this.validateFile(file)) {
            return;
        }

        this.uploadedFile = file;
        this.displayFileInfo(file);
        this.enableTranscriptionButton();
        this.showSuccess('File uploaded successfully!');
    }

    validateFile(file) {
        const allowedTypes = [
            'audio/wav', 'audio/mp3', 'audio/mpeg', 'audio/m4a', 'audio/flac',
            'audio/ogg', 'audio/wma', 'audio/aac', 'video/mp4'
        ];
        
        const maxSize = 500 * 1024 * 1024; // 500MB

        if (!allowedTypes.includes(file.type) && !file.name.match(/\.(wav|mp3|m4a|flac|ogg|wma|aac|mp4)$/i)) {
            this.showError('Please select a valid audio file.');
            return false;
        }

        if (file.size > maxSize) {
            this.showError('File size must be less than 500MB.');
            return false;
        }

        return true;
    }

    displayFileInfo(file) {
        const fileInfo = document.getElementById('fileInfo');
        const fileName = document.getElementById('fileName');
        const fileSize = document.getElementById('fileSize');

        if (fileInfo && fileName && fileSize) {
            fileName.textContent = file.name;
            fileSize.textContent = this.formatFileSize(file.size);
            fileInfo.classList.remove('hidden');
        }
    }

    enableTranscriptionButton() {
        const transcribeBtn = document.getElementById('transcribeBtn');
        if (transcribeBtn) {
            transcribeBtn.disabled = false;
        }
    }

    // Transcription Methods
    async startTranscription() {
        if (!this.uploadedFile) {
            this.showError('Please upload a file first.');
            return;
        }

        this.isTranscribing = true;
        this.showProgressSection();
        this.updateTranscriptionButton('Transcribing...', true);

        try {
            const formData = new FormData();
            formData.append('file', this.uploadedFile);
            formData.append('model', document.getElementById('modelSelect')?.value || 'base');
            formData.append('language', document.getElementById('languageSelect')?.value || 'auto');
            formData.append('diarization', document.getElementById('diarizationCheckbox')?.checked || false);
            formData.append('temperature', document.getElementById('temperatureSelect')?.value || '0.2');

            const response = await fetch('/api/transcribe', {
                method: 'POST',
                body: formData
            });

            if (!response.ok) {
                throw new Error(`HTTP error! status: ${response.status}`);
            }

            const result = await response.json();
            this.currentJobId = result.job_id;
            this.updateJobInfo(result);

        } catch (error) {
            console.error('Transcription error:', error);
            this.handleTranscriptionError({ error: error.message });
        }
    }

    updateTranscriptionButton(text, disabled) {
        const transcribeBtn = document.getElementById('transcribeBtn');
        if (transcribeBtn) {
            transcribeBtn.textContent = text;
            transcribeBtn.disabled = disabled;
        }
    }

    showProgressSection() {
        const progressSection = document.getElementById('progressSection');
        if (progressSection) {
            progressSection.classList.remove('hidden');
            progressSection.scrollIntoView({ behavior: 'smooth' });
        }
    }

    updateJobInfo(data) {
        const startTime = document.getElementById('startTime');
        const jobId = document.getElementById('jobId');

        if (startTime) {
            startTime.textContent = new Date().toLocaleTimeString();
        }

        if (jobId) {
            jobId.textContent = data.job_id || '-';
        }
    }

    updateProgress(data) {
        const progressPercent = document.getElementById('progressPercent');
        const progressFill = document.getElementById('progressFill');
        const progressMessage = document.getElementById('progressMessage');

        if (progressPercent && progressFill) {
            const percent = Math.round(data.progress || 0);
            progressPercent.textContent = `${percent}%`;
            progressFill.style.width = `${percent}%`;
        }

        if (progressMessage) {
            progressMessage.textContent = data.message || 'Processing...';
        }
    }

    handleTranscriptionComplete(data) {
        this.isTranscribing = false;
        this.updateTranscriptionButton('Start Transcription', false);
        this.showResultsSection(data);
        this.loadMyFiles();
        this.loadQuotaInfo();
    }

    handleTranscriptionError(data) {
        this.isTranscribing = false;
        this.updateTranscriptionButton('Start Transcription', false);
        this.showError(data.error || 'Transcription failed. Please try again.');
    }

    showResultsSection(data) {
        const resultsSection = document.getElementById('resultsSection');
        const transcriptContent = document.getElementById('transcriptContent');
        const transcriptionSummary = document.getElementById('transcriptionSummary');

        if (resultsSection) {
            resultsSection.classList.remove('hidden');
            resultsSection.scrollIntoView({ behavior: 'smooth' });
        }

        if (transcriptContent && data.transcript) {
            transcriptContent.textContent = data.transcript;
        }

        if (transcriptionSummary) {
            const wordCount = data.transcript ? data.transcript.split(' ').length : 0;
            transcriptionSummary.textContent = `Transcribed ${wordCount} words successfully.`;
        }
    }

    // File Management Methods
    async loadMyFiles() {
        try {
            const response = await fetch('/api/my-files');
            if (response.ok) {
                const data = await response.json();
                this.displayMyFiles(data.files || []);
            }
        } catch (error) {
            console.error('Error loading files:', error);
        }
    }

    displayMyFiles(files) {
        const filesList = document.getElementById('filesList');
        const myFilesSection = document.getElementById('myFilesSection');

        if (!filesList) return;

        if (files.length === 0) {
            filesList.innerHTML = `
                <div class="text-center py-8 text-surface-500">
                    <span class="material-icons text-4xl mb-2">folder_open</span>
                    <p>No files uploaded yet</p>
                </div>
            `;
            if (myFilesSection) {
                myFilesSection.classList.add('hidden');
            }
            return;
        }

        if (myFilesSection) {
            myFilesSection.classList.remove('hidden');
        }

        filesList.innerHTML = files.map(file => `
            <div class="flex items-center justify-between p-4 border border-surface-200 rounded-lg hover:border-primary-300 hover:bg-primary-50 transition-colors">
                <div class="flex items-center gap-3">
                    <span class="material-icons text-primary-500">${this.getFileIcon(file.name)}</span>
                    <div>
                        <h5 class="font-medium text-surface-900">${file.name}</h5>
                        <p class="text-sm text-surface-600">${this.formatFileSize(file.size)} • ${new Date(file.uploaded_at).toLocaleDateString()}</p>
                    </div>
                </div>
                <div class="flex gap-2">
                    <button class="p-2 rounded-lg hover:bg-surface-100 transition-colors" onclick="downloadFile('${file.name}')">
                        <span class="material-icons text-surface-600">download</span>
                    </button>
                    <button class="p-2 rounded-lg hover:bg-error-50 transition-colors" onclick="deleteFile('${file.name}')">
                        <span class="material-icons text-error">delete</span>
                    </button>
                </div>
            </div>
        `).join('');
    }

    async loadQuotaInfo() {
        try {
            const response = await fetch('/api/my-quota');
            if (response.ok) {
                const data = await response.json();
                this.displayQuotaInfo(data);
            }
        } catch (error) {
            console.error('Error loading quota:', error);
        }
    }

    displayQuotaInfo(quota) {
        const quotaInfo = document.getElementById('quotaInfo');
        if (!quotaInfo) return;

        quotaInfo.innerHTML = `
            <div class="bg-primary-50 border border-primary-200 rounded-lg p-4">
                <div class="flex items-center gap-3">
                    <span class="material-icons text-primary-500">storage</span>
                    <div>
                        <p class="text-sm text-primary-700">Storage Used</p>
                        <p class="font-medium text-primary-900">${this.formatFileSize(quota.storage_used || 0)} / ${this.formatFileSize(quota.storage_limit || 0)}</p>
                    </div>
                </div>
            </div>
            <div class="bg-warning-50 border border-warning-200 rounded-lg p-4">
                <div class="flex items-center gap-3">
                    <span class="material-icons text-warning">description</span>
                    <div>
                        <p class="text-sm text-warning-700">Files Count</p>
                        <p class="font-medium text-warning-900">${quota.files_count || 0} / ${quota.files_limit || 0}</p>
                    </div>
                </div>
            </div>
            <div class="bg-success-50 border border-success-200 rounded-lg p-4">
                <div class="flex items-center gap-3">
                    <span class="material-icons text-success">schedule</span>
                    <div>
                        <p class="text-sm text-success-700">24h Usage</p>
                        <p class="font-medium text-success-900">${quota.daily_usage || 0} / ${quota.daily_limit || 0}</p>
                    </div>
                </div>
            </div>
        `;
    }

    async checkExistingTranscripts() {
        try {
            const response = await fetch('/api/transcripts');
            if (response.ok) {
                const data = await response.json();
                this.displayExistingTranscripts(data.transcripts || []);
            }
        } catch (error) {
            console.error('Error loading transcripts:', error);
        }
    }

    displayExistingTranscripts(transcripts) {
        const existingTranscriptsList = document.getElementById('existingTranscriptsList');
        const existingTranscriptsSection = document.getElementById('existingTranscriptsSection');

        if (!existingTranscriptsList) return;

        if (transcripts.length === 0) {
            if (existingTranscriptsSection) {
                existingTranscriptsSection.classList.add('hidden');
            }
            return;
        }

        if (existingTranscriptsSection) {
            existingTranscriptsSection.classList.remove('hidden');
        }

        existingTranscriptsList.innerHTML = transcripts.map(transcript => `
            <div class="flex items-center justify-between p-4 border border-surface-200 rounded-lg hover:border-primary-300 hover:bg-primary-50 transition-colors">
                <div class="flex items-center gap-3">
                    <span class="material-icons text-primary-500">description</span>
                    <div>
                        <h5 class="font-medium text-surface-900">${transcript.filename}</h5>
                        <p class="text-sm text-surface-600">${new Date(transcript.created_at).toLocaleDateString()}</p>
                    </div>
                </div>
                <div class="flex gap-2">
                    <button class="p-2 rounded-lg hover:bg-surface-100 transition-colors" onclick="downloadTranscript('${transcript.filename}')">
                        <span class="material-icons text-surface-600">download</span>
                    </button>
                </div>
            </div>
        `).join('');
    }

    // Utility Methods
    formatFileSize(bytes) {
        if (bytes === 0) return '0 Bytes';
        const k = 1024;
        const sizes = ['Bytes', 'KB', 'MB', 'GB'];
        const i = Math.floor(Math.log(bytes) / Math.log(k));
        return parseFloat((bytes / Math.pow(k, i)).toFixed(2)) + ' ' + sizes[i];
    }

    getFileIcon(filename) {
        const ext = filename.split('.').pop().toLowerCase();
        const iconMap = {
            'wav': 'audiotrack',
            'mp3': 'audiotrack',
            'm4a': 'audiotrack',
            'flac': 'audiotrack',
            'ogg': 'audiotrack',
            'wma': 'audiotrack',
            'aac': 'audiotrack',
            'mp4': 'video_file',
            'txt': 'description',
            'md': 'description'
        };
        return iconMap[ext] || 'description';
    }

    updateConnectionStatus(status, type) {
        const connectionStatus = document.getElementById('connectionStatus');
        if (connectionStatus) {
            connectionStatus.textContent = status;
            connectionStatus.className = `text-sm font-medium text-${type}`;
        }
    }

    setupFormValidation() {
        // Add real-time validation for form inputs
        const inputs = document.querySelectorAll('select, input[type="checkbox"]');
        inputs.forEach(input => {
            input.addEventListener('change', () => {
                this.validateForm();
            });
        });
    }

    validateForm() {
        const hasFile = this.uploadedFile !== null;
        const transcribeBtn = document.getElementById('transcribeBtn');
        
        if (transcribeBtn) {
            transcribeBtn.disabled = !hasFile || this.isTranscribing;
        }
    }

    // Notification Methods
    showNotification(message, type = 'info', duration = 5000) {
        const container = document.getElementById('notificationContainer');
        if (!container) return;

        const notification = document.createElement('div');
        notification.className = `
            flex items-center gap-3 p-4 rounded-lg shadow-md-4
            ${type === 'success' ? 'bg-success text-white' : ''}
            ${type === 'error' ? 'bg-error text-white' : ''}
            ${type === 'warning' ? 'bg-warning text-white' : ''}
            ${type === 'info' ? 'bg-info text-white' : ''}
            animate-slide-up
        `;

        const icon = {
            'success': 'check_circle',
            'error': 'error',
            'warning': 'warning',
            'info': 'info'
        }[type] || 'info';

        notification.innerHTML = `
            <span class="material-icons">${icon}</span>
            <span>${message}</span>
            <button class="ml-auto" onclick="this.parentElement.remove()">
                <span class="material-icons">close</span>
            </button>
        `;

        container.appendChild(notification);

        setTimeout(() => {
            if (notification.parentElement) {
                notification.remove();
            }
        }, duration);
    }

    showSuccess(message) {
        this.showNotification(message, 'success');
    }

    showError(message) {
        this.showNotification(message, 'error');
    }

    showWarning(message) {
        this.showNotification(message, 'warning');
    }

    showInfo(message) {
        this.showNotification(message, 'info');
    }
}

// Global functions for HTML onclick handlers
function clearFile() {
    const fileInput = document.getElementById('fileInput');
    const fileInfo = document.getElementById('fileInfo');
    const transcribeBtn = document.getElementById('transcribeBtn');
    
    if (fileInput) fileInput.value = '';
    if (fileInfo) fileInfo.classList.add('hidden');
    if (transcribeBtn) transcribeBtn.disabled = true;
    
    app.uploadedFile = null;
}

function refreshProgress() {
    if (app.currentJobId) {
        app.socket.emit('get_progress', { job_id: app.currentJobId });
    }
}

function cancelTranscription() {
    if (app.currentJobId) {
        app.socket.emit('cancel_transcription', { job_id: app.currentJobId });
        app.isTranscribing = false;
        app.updateTranscriptionButton('Start Transcription', false);
    }
}

function downloadTranscript() {
    // Implementation for downloading transcript
    app.showInfo('Download functionality will be implemented');
}

function copyTranscript() {
    const transcriptContent = document.getElementById('transcriptContent');
    if (transcriptContent) {
        navigator.clipboard.writeText(transcriptContent.textContent);
        app.showSuccess('Transcript copied to clipboard!');
    }
}

function refreshMyFiles() {
    app.loadMyFiles();
    app.loadQuotaInfo();
}

function cleanupMyFiles() {
    if (confirm('Are you sure you want to cleanup old files?')) {
        fetch('/api/my-files/cleanup', { method: 'POST' })
            .then(response => response.json())
            .then(data => {
                app.showSuccess('Files cleaned up successfully!');
                app.loadMyFiles();
                app.loadQuotaInfo();
            })
            .catch(error => {
                app.showError('Error cleaning up files');
            });
    }
}

function downloadFile(filename) {
    window.open(`/api/my-files/${filename}`, '_blank');
}

function deleteFile(filename) {
    if (confirm(`Are you sure you want to delete ${filename}?`)) {
        fetch(`/api/my-files/${filename}`, { method: 'DELETE' })
            .then(response => {
                if (response.ok) {
                    app.showSuccess('File deleted successfully!');
                    app.loadMyFiles();
                    app.loadQuotaInfo();
                } else {
                    app.showError('Error deleting file');
                }
            })
            .catch(error => {
                app.showError('Error deleting file');
            });
    }
}

function downloadTranscript(filename) {
    window.open(`/api/transcripts/${filename}`, '_blank');
}

function showSettings() {
    app.showInfo('Settings panel will be implemented');
}

// Initialize the application
let app;
function initializeApp() {
    app = new VoiceTranscriberApp();
}

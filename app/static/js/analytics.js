/**
 * Analytics Tracking Module for Voice Transcriber
 * Handles Google Analytics 4 and Hotjar integration with comprehensive event tracking
 */

class AnalyticsTracker {
    constructor(config) {
        this.config = config;
        this.sessionId = config.session_id;
        this.debug = config.debug;
        this.gaEnabled = config.google_analytics.enabled;
        this.hotjarEnabled = config.hotjar.enabled;
        this.gaMeasurementId = config.google_analytics.measurement_id;
        this.hotjarSiteId = config.hotjar.site_id;
        
        this.initializeTracking();
        this.setupEventListeners();
    }
    
    /**
     * Initialize tracking services
     */
    initializeTracking() {
        if (this.gaEnabled && this.gaMeasurementId) {
            this.initializeGoogleAnalytics();
        }
        
        if (this.hotjarEnabled && this.hotjarSiteId) {
            this.initializeHotjar();
        }
        
        this.log('Analytics initialized', {
            ga_enabled: this.gaEnabled,
            hotjar_enabled: this.hotjarEnabled
        });
    }
    
    /**
     * Initialize Google Analytics 4
     */
    initializeGoogleAnalytics() {
        // Load Google Analytics script
        const script = document.createElement('script');
        script.async = true;
        script.src = `https://www.googletagmanager.com/gtag/js?id=${this.gaMeasurementId}`;
        document.head.appendChild(script);
        
        // Initialize gtag
        window.dataLayer = window.dataLayer || [];
        function gtag(){dataLayer.push(arguments);}
        window.gtag = gtag;
        
        gtag('js', new Date());
        gtag('config', this.gaMeasurementId, {
            'custom_map': {
                'custom_parameter_1': 'session_id',
                'custom_parameter_2': 'user_type'
            }
        });
        
        // Set session ID
        gtag('config', this.gaMeasurementId, {
            'session_id': this.sessionId
        });
        
        this.log('Google Analytics initialized', { measurement_id: this.gaMeasurementId });
    }
    
    /**
     * Initialize Hotjar
     */
    initializeHotjar() {
        // Load Hotjar script
        const script = document.createElement('script');
        script.innerHTML = `
            (function(h,o,t,j,a,r){
                h.hj=h.hj||function(){(h.hj.q=h.hj.q||[]).push(arguments)};
                h._hjSettings={hjid:${this.hotjarSiteId},hjsv:6};
                a=o.getElementsByTagName('head')[0];
                r=o.createElement('script');r.async=1;
                r.src=t+h._hjSettings.hjid+j+h._hjSettings.hjsv;
                a.appendChild(r);
            })(window,document,'https://static.hotjar.com/c/hotjar-','.js?sv=');
        `;
        document.head.appendChild(script);
        
        this.log('Hotjar initialized', { site_id: this.hotjarSiteId });
    }
    
    /**
     * Setup event listeners for automatic tracking
     */
    setupEventListeners() {
        // Track file uploads
        this.trackFileUploads();
        
        // Track form interactions
        this.trackFormInteractions();
        
        // Track button clicks
        this.trackButtonClicks();
        
        // Track page visibility changes
        this.trackPageVisibility();
        
        // Track scroll depth
        this.trackScrollDepth();
        
        // Track time on page
        this.trackTimeOnPage();
        
        // Track transcription progress
        this.trackTranscriptionProgress();
    }
    
    /**
     * Track file upload events
     */
    trackFileUploads() {
        const fileInput = document.getElementById('fileInput');
        if (fileInput) {
            fileInput.addEventListener('change', (event) => {
                const files = event.target.files;
                if (files && files.length > 0) {
                    const file = files[0];
                    this.trackEvent('file_upload', {
                        file_name: file.name,
                        file_size: file.size,
                        file_type: file.type,
                        file_extension: file.name.split('.').pop()
                    });
                }
            });
        }
        
        // Track drag and drop
        const uploadArea = document.getElementById('uploadArea');
        if (uploadArea) {
            uploadArea.addEventListener('dragover', () => {
                this.trackEvent('drag_over', { element: 'upload_area' });
            });
            
            uploadArea.addEventListener('drop', (event) => {
                const files = event.dataTransfer.files;
                if (files && files.length > 0) {
                    const file = files[0];
                    this.trackEvent('file_drop', {
                        file_name: file.name,
                        file_size: file.size,
                        file_type: file.type
                    });
                }
            });
        }
    }
    
    /**
     * Track form interactions
     */
    trackFormInteractions() {
        // Track model selection changes
        const modelSelect = document.getElementById('modelSelect');
        if (modelSelect) {
            modelSelect.addEventListener('change', (event) => {
                this.trackEvent('model_selection', {
                    model: event.target.value,
                    element: 'model_select'
                });
            });
        }
        
        // Track language selection changes
        const languageSelect = document.getElementById('languageSelect');
        if (languageSelect) {
            languageSelect.addEventListener('change', (event) => {
                this.trackEvent('language_selection', {
                    language: event.target.value,
                    element: 'language_select'
                });
            });
        }
        
        // Track temperature selection changes
        const temperatureSelect = document.getElementById('temperatureSelect');
        if (temperatureSelect) {
            temperatureSelect.addEventListener('change', (event) => {
                this.trackEvent('temperature_selection', {
                    temperature: event.target.value,
                    element: 'temperature_select'
                });
            });
        }
        
        // Track speaker diarization toggle
        const speakerDiarization = document.getElementById('speakerDiarization');
        if (speakerDiarization) {
            speakerDiarization.addEventListener('change', (event) => {
                this.trackEvent('speaker_diarization_toggle', {
                    enabled: event.target.checked,
                    element: 'speaker_diarization_checkbox'
                });
            });
        }
    }
    
    /**
     * Track button clicks
     */
    trackButtonClicks() {
        // Track transcription start
        const transcribeBtn = document.getElementById('transcribeBtn');
        if (transcribeBtn) {
            transcribeBtn.addEventListener('click', () => {
                const model = document.getElementById('modelSelect')?.value;
                const language = document.getElementById('languageSelect')?.value;
                const temperature = document.getElementById('temperatureSelect')?.value;
                const speakerDiarization = document.getElementById('speakerDiarization')?.checked;
                
                this.trackEvent('transcription_start', {
                    model: model,
                    language: language,
                    temperature: temperature,
                    speaker_diarization: speakerDiarization
                });
            });
        }
        
        // Track download button clicks
        const downloadBtn = document.getElementById('downloadBtn');
        if (downloadBtn) {
            downloadBtn.addEventListener('click', () => {
                this.trackEvent('download_click', {
                    element: 'download_button'
                });
            });
        }
        
        // Track view transcript button clicks
        const viewTranscriptBtn = document.getElementById('viewTranscriptBtn');
        if (viewTranscriptBtn) {
            viewTranscriptBtn.addEventListener('click', () => {
                this.trackEvent('view_transcript_click', {
                    element: 'view_transcript_button'
                });
            });
        }
        
        // Track refresh button clicks
        const refreshBtn = document.getElementById('refreshStatusBtn');
        if (refreshBtn) {
            refreshBtn.addEventListener('click', () => {
                this.trackEvent('refresh_status_click', {
                    element: 'refresh_status_button'
                });
            });
        }
        
        // Track cancel button clicks
        const cancelBtn = document.getElementById('cancelJobBtn');
        if (cancelBtn) {
            cancelBtn.addEventListener('click', () => {
                this.trackEvent('cancel_transcription_click', {
                    element: 'cancel_transcription_button'
                });
            });
        }
    }
    
    /**
     * Track page visibility changes
     */
    trackPageVisibility() {
        document.addEventListener('visibilitychange', () => {
            if (document.hidden) {
                this.trackEvent('page_hidden', {
                    timestamp: Date.now()
                });
            } else {
                this.trackEvent('page_visible', {
                    timestamp: Date.now()
                });
            }
        });
    }
    
    /**
     * Track scroll depth
     */
    trackScrollDepth() {
        let maxScrollDepth = 0;
        const scrollThresholds = [25, 50, 75, 90, 100];
        const trackedThresholds = new Set();
        
        window.addEventListener('scroll', () => {
            const scrollTop = window.pageYOffset || document.documentElement.scrollTop;
            const documentHeight = document.documentElement.scrollHeight - window.innerHeight;
            const scrollPercentage = Math.round((scrollTop / documentHeight) * 100);
            
            if (scrollPercentage > maxScrollDepth) {
                maxScrollDepth = scrollPercentage;
                
                // Track scroll depth milestones
                scrollThresholds.forEach(threshold => {
                    if (scrollPercentage >= threshold && !trackedThresholds.has(threshold)) {
                        trackedThresholds.add(threshold);
                        this.trackEvent('scroll_depth', {
                            depth_percentage: threshold,
                            max_depth: maxScrollDepth
                        });
                    }
                });
            }
        });
    }
    
    /**
     * Track time on page
     */
    trackTimeOnPage() {
        const startTime = Date.now();
        
        // Track time milestones
        const timeThresholds = [30, 60, 120, 300, 600]; // seconds
        const trackedTimes = new Set();
        
        timeThresholds.forEach(threshold => {
            setTimeout(() => {
                if (!trackedTimes.has(threshold)) {
                    trackedTimes.add(threshold);
                    this.trackEvent('time_on_page', {
                        time_seconds: threshold,
                        time_minutes: Math.round(threshold / 60)
                    });
                }
            }, threshold * 1000);
        });
        
        // Track before page unload
        window.addEventListener('beforeunload', () => {
            const totalTime = Math.round((Date.now() - startTime) / 1000);
            this.trackEvent('page_exit', {
                total_time_seconds: totalTime,
                total_time_minutes: Math.round(totalTime / 60)
            });
        });
    }
    
    /**
     * Track transcription progress
     */
    trackTranscriptionProgress() {
        // Track progress updates
        const originalUpdateProgress = window.updateProgress;
        if (originalUpdateProgress) {
            window.updateProgress = (progress, message) => {
                originalUpdateProgress(progress, message);
                
                // Track progress milestones
                const progressThresholds = [25, 50, 75, 90, 100];
                if (progressThresholds.includes(progress)) {
                    this.trackEvent('transcription_progress', {
                        progress_percentage: progress,
                        progress_message: message
                    });
                }
            };
        }
        
        // Track completion
        const originalShowResults = window.showResults;
        if (originalShowResults) {
            window.showResults = (result) => {
                originalShowResults(result);
                
                this.trackEvent('transcription_complete', {
                    success: true,
                    result_type: typeof result
                });
            };
        }
        
        // Track errors
        const originalShowError = window.showError;
        if (originalShowError) {
            window.showError = (error) => {
                originalShowError(error);
                
                this.trackEvent('transcription_error', {
                    error_message: error.message || error,
                    error_type: error.type || 'unknown'
                });
            };
        }
    }
    
    /**
     * Track custom events
     */
    trackEvent(eventName, parameters = {}) {
        const eventData = {
            event_name: eventName,
            timestamp: new Date().toISOString(),
            session_id: this.sessionId,
            ...parameters
        };
        
        // Send to Google Analytics
        if (this.gaEnabled && window.gtag) {
            gtag('event', eventName, {
                ...parameters,
                custom_parameter_1: this.sessionId,
                custom_parameter_2: 'voice_transcriber_user'
            });
        }
        
        // Send to Hotjar
        if (this.hotjarEnabled && window.hj) {
            hj('event', eventName);
        }
        
        // Log for debugging
        this.log('Event tracked', eventData);
        
        // Send to backend for server-side tracking
        this.sendToBackend(eventData);
    }
    
    /**
     * Send event data to backend
     */
    async sendToBackend(eventData) {
        try {
            await fetch('/api/analytics/track', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify(eventData)
            });
        } catch (error) {
            this.log('Error sending event to backend', { error: error.message });
        }
    }
    
    /**
     * Track page view
     */
    trackPageView(pageTitle, pagePath = null) {
        const path = pagePath || window.location.pathname;
        
        if (this.gaEnabled && window.gtag) {
            gtag('config', this.gaMeasurementId, {
                page_title: pageTitle,
                page_location: window.location.href,
                page_path: path
            });
        }
        
        this.trackEvent('page_view', {
            page_title: pageTitle,
            page_path: path,
            page_url: window.location.href
        });
    }
    
    /**
     * Set user properties
     */
    setUserProperty(propertyName, propertyValue) {
        if (this.gaEnabled && window.gtag) {
            gtag('config', this.gaMeasurementId, {
                [propertyName]: propertyValue
            });
        }
        
        this.log('User property set', {
            property: propertyName,
            value: propertyValue
        });
    }
    
    /**
     * Track performance metrics
     */
    trackPerformance(metricName, metricValue, unit = null) {
        this.trackEvent('performance_metric', {
            metric_name: metricName,
            metric_value: metricValue,
            unit: unit
        });
    }
    
    /**
     * Log messages for debugging
     */
    log(message, data = {}) {
        if (this.debug) {
            console.log(`[Analytics] ${message}`, data);
        }
    }
    
    /**
     * Get analytics summary
     */
    async getAnalyticsSummary() {
        try {
            const response = await fetch('/api/analytics/summary');
            const summary = await response.json();
            return summary;
        } catch (error) {
            this.log('Error getting analytics summary', { error: error.message });
            return null;
        }
    }
}

// Initialize analytics when DOM is loaded
document.addEventListener('DOMContentLoaded', function() {
    // Get analytics config from server
    fetch('/api/analytics/config')
        .then(response => response.json())
        .then(config => {
            if (config.enabled) {
                window.analyticsTracker = new AnalyticsTracker(config);
                
                // Track initial page view
                window.analyticsTracker.trackPageView(
                    document.title,
                    window.location.pathname
                );
            }
        })
        .catch(error => {
            console.error('Failed to initialize analytics:', error);
        });
});

// Export for global access
window.AnalyticsTracker = AnalyticsTracker;

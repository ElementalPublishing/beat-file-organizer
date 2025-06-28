/**
 * 🎵 BEAT ORGANIZER: THE PRODUCER'S LIBERATION ARMY
 * Revolutionary Frontend Architecture - Defeating the God Object!
 * 
 * Born from the enemy's $5.53 insulting offer.
 * This modular architecture eliminates memory leaks, performance issues,
 * and the God Object anti-pattern. Built for VICTORY!
 */

// 🛡️ CORE TASK MANAGER (Eliminates global state chaos!)
class TaskManager {
    constructor() {
        this.activeTasks = new Map();
        this.websocket = null;
        this.reconnectAttempts = 0;
        this.maxReconnectAttempts = 5;
    }

    async startTask(endpoint, data) {
        try {
            const response = await fetch(endpoint, {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify(data)
            });

            const result = await response.json();
            
            if (result.success && result.task_id) {
                this.activeTasks.set(result.task_id, {
                    id: result.task_id,
                    status: 'running',
                    progress: 0
                });
                
                // Connect to WebSocket for real-time updates
                this.connectWebSocket();
                
                return result.task_id;
            } else {
                throw new Error(result.error || 'Task creation failed');
            }
        } catch (error) {
            throw new Error(`Failed to start task: ${error.message}`);
        }
    }

    connectWebSocket() {
        if (this.websocket?.readyState === WebSocket.OPEN) return;

        try {
            this.websocket = new WebSocket(`ws://${window.location.host}/ws/progress`);
            
            this.websocket.onopen = () => {
                console.log('🔗 WebSocket connected for real-time updates');
                this.reconnectAttempts = 0;
            };

            this.websocket.onmessage = (event) => {
                const message = JSON.parse(event.data);
                if (message.type === 'progress_update') {
                    this.handleProgressUpdate(message.task_id, message.data);
                }
            };

            this.websocket.onclose = () => {
                console.log('🔌 WebSocket disconnected');
                this.attemptReconnect();
            };

            this.websocket.onerror = (error) => {
                console.error('🚨 WebSocket error:', error);
            };
        } catch (error) {
            console.error('🚨 WebSocket connection failed:', error);
        }
    }

    attemptReconnect() {
        if (this.reconnectAttempts < this.maxReconnectAttempts) {
            this.reconnectAttempts++;
            setTimeout(() => {
                console.log(`🔄 Reconnecting WebSocket (attempt ${this.reconnectAttempts})`);
                this.connectWebSocket();
            }, 2000 * this.reconnectAttempts);
        }
    }

    handleProgressUpdate(taskId, data) {
        console.log('📊 WebSocket progress update:', taskId, data);
        const task = this.activeTasks.get(taskId);
        if (task) {
            task.progress = data.progress;
            task.phase = data.phase;
            task.currentFile = data.current_file;
            
            // Emit custom event for UI components to listen
            window.dispatchEvent(new CustomEvent('taskProgress', {
                detail: { taskId, ...data }
            }));

            if (data.phase === 'completed' || data.phase === 'failed') {
                this.completeTask(taskId, data);
            }
        }
    }

    completeTask(taskId, data) {
        const task = this.activeTasks.get(taskId);
        if (task) {
            task.status = data.phase;
            task.result = data.result;
            task.error = data.error;
            
            // Emit completion event
            window.dispatchEvent(new CustomEvent('taskComplete', {
                detail: { taskId, ...data }
            }));
        }
    }

    getTask(taskId) {
        return this.activeTasks.get(taskId);
    }

    cleanup() {
        if (this.websocket) {
            this.websocket.close();
        }
        this.activeTasks.clear();
    }
}

// 🎯 NOTIFICATION SYSTEM (Memory-safe notifications!)
class NotificationManager {
    constructor() {
        this.notifications = [];
        this.maxNotifications = 5;
        this.createContainer();
    }

    createContainer() {
        this.container = document.createElement('div');
        this.container.id = 'notification-container';
        this.container.style.cssText = `
            position: fixed;
            top: 2rem;
            right: 2rem;
            z-index: 9999;
            display: flex;
            flex-direction: column;
            gap: 0.5rem;
            max-width: 400px;
        `;
        document.body.appendChild(this.container);
    }

    show(message, type = 'info', duration = 5000) {
        // Remove old notifications if at limit
        if (this.notifications.length >= this.maxNotifications) {
            this.remove(this.notifications[0]);
        }

        const notification = this.createNotification(message, type);
        this.notifications.push(notification);
        this.container.appendChild(notification);

        // Auto-remove after duration
        if (duration > 0) {
            setTimeout(() => this.remove(notification), duration);
        }

        return notification;
    }

    createNotification(message, type) {
        const notification = document.createElement('div');
        notification.className = `notification notification-${type}`;
        notification.style.cssText = `
            padding: 1rem 1.5rem;
            border-radius: 8px;
            color: white;
            font-weight: 500;
            box-shadow: 0 4px 12px rgba(0, 0, 0, 0.15);
            animation: slideInRight 0.3s ease-out;
            cursor: pointer;
            position: relative;
            background: ${this.getTypeColor(type)};
        `;

        notification.innerHTML = `
            <div style="display: flex; align-items: center; justify-content: space-between;">
                <span>${message}</span>
                <button style="background: none; border: none; color: white; font-size: 1.2rem; cursor: pointer; margin-left: 1rem;">&times;</button>
            </div>
        `;

        // Close button functionality
        notification.querySelector('button').onclick = () => this.remove(notification);
        notification.onclick = () => this.remove(notification);

        return notification;
    }

    getTypeColor(type) {
        const colors = {
            success: '#27ae60',
            warning: '#f39c12', 
            danger: '#e74c3c',
            info: '#3498db'
        };
        return colors[type] || colors.info;
    }

    remove(notification) {
        if (notification && notification.parentNode) {
            notification.style.animation = 'slideOutRight 0.3s ease-out';
            setTimeout(() => {
                if (notification.parentNode) {
                    notification.parentNode.removeChild(notification);
                }
                this.notifications = this.notifications.filter(n => n !== notification);
            }, 300);
        }
    }

    cleanup() {
        this.notifications.forEach(n => this.remove(n));
        if (this.container && this.container.parentNode) {
            this.container.parentNode.removeChild(this.container);
        }
    }
}

// 🎵 AUDIO PLAYER (Resource-safe audio management!)
class AudioPlayer {
    constructor() {
        this.currentAudio = null;
        this.currentButton = null;
    }

    async play(filepath, filename, playButton) {
        try {
            // Stop current audio if playing
            this.stop();

            // Update button to loading state
            this.setButtonState(playButton, 'loading');

            const response = await fetch('/api/audio', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ filepath })
            });

            if (!response.ok) throw new Error('Failed to load audio');

            const blob = await response.blob();
            const audioUrl = URL.createObjectURL(blob);
            
            this.currentAudio = new Audio(audioUrl);
            this.currentButton = playButton;

            // Set up event listeners
            this.currentAudio.onloadeddata = () => {
                this.setButtonState(playButton, 'playing');
            };

            this.currentAudio.onended = () => {
                this.cleanup();
            };

            this.currentAudio.onerror = () => {
                this.setButtonState(playButton, 'error');
                this.cleanup();
            };

            await this.currentAudio.play();
            
        } catch (error) {
            this.setButtonState(playButton, 'error');
            throw error;
        }
    }

    stop() {
        if (this.currentAudio) {
            this.currentAudio.pause();
            this.currentAudio.currentTime = 0;
            
            // Revoke blob URL to prevent memory leaks
            if (this.currentAudio.src.startsWith('blob:')) {
                URL.revokeObjectURL(this.currentAudio.src);
            }
            
            this.cleanup();
        }
    }

    pause() {
        if (this.currentAudio && !this.currentAudio.paused) {
            this.currentAudio.pause();
            this.setButtonState(this.currentButton, 'paused');
        }
    }

    resume() {
        if (this.currentAudio && this.currentAudio.paused) {
            this.currentAudio.play();
            this.setButtonState(this.currentButton, 'playing');
        }
    }

    setButtonState(button, state) {
        if (!button) return;

        const icons = {
            loading: '<i class="fas fa-spinner fa-spin"></i>',
            playing: '<i class="fas fa-pause"></i>',
            paused: '<i class="fas fa-play"></i>',
            stopped: '<i class="fas fa-play"></i>',
            error: '<i class="fas fa-exclamation-triangle"></i>'
        };

        button.innerHTML = icons[state] || icons.stopped;
        
        const classes = {
            loading: 'btn-warning',
            playing: 'btn-success', 
            paused: 'btn-primary',
            stopped: 'btn-outline-primary',
            error: 'btn-danger'
        };

        // Reset classes
        button.className = button.className.split(' ').filter(c => !c.startsWith('btn-')).join(' ');
        button.classList.add('btn', 'btn-sm', classes[state] || classes.stopped);
    }

    cleanup() {
        this.setButtonState(this.currentButton, 'stopped');
        this.currentAudio = null;
        this.currentButton = null;
    }
}

// 🌊 WAVEFORM RENDERER (Memory-efficient visualization!)
class WaveformRenderer {
    constructor() {
        this.canvasCache = new Map();
        this.maxCacheSize = 50;
    }

    renderToCanvas(canvas, waveformData, options = {}) {
        if (!canvas || !waveformData || waveformData.length === 0) return;

        const cacheKey = this.getCacheKey(waveformData, canvas.width, canvas.height);
        
        // Check cache first
        if (this.canvasCache.has(cacheKey)) {
            const cachedImageData = this.canvasCache.get(cacheKey);
            const ctx = canvas.getContext('2d');
            ctx.putImageData(cachedImageData, 0, 0);
            return;
        }

        const ctx = canvas.getContext('2d');
        const width = canvas.width;
        const height = canvas.height;

        // Clear canvas
        ctx.clearRect(0, 0, width, height);

        // Normalize data
        const maxValue = Math.max(...waveformData.map(Math.abs));
        const normalizedData = maxValue > 0 ? waveformData.map(v => v / maxValue) : waveformData;

        // Set style
        ctx.strokeStyle = options.color || '#e94560';
        ctx.lineWidth = options.lineWidth || 2;
        ctx.fillStyle = options.fillColor || 'rgba(233, 69, 96, 0.3)';

        // Draw waveform
        ctx.beginPath();
        ctx.moveTo(0, height / 2);

        normalizedData.forEach((value, index) => {
            const x = (index / normalizedData.length) * width;
            const y = (height / 2) - (value * (height / 2) * 0.8);
            ctx.lineTo(x, y);
        });

        ctx.lineTo(width, height / 2);
        ctx.closePath();
        ctx.fill();
        ctx.stroke();

        // Cache the result (manage cache size)
        if (this.canvasCache.size >= this.maxCacheSize) {
            const firstKey = this.canvasCache.keys().next().value;
            this.canvasCache.delete(firstKey);
        }
        
        this.canvasCache.set(cacheKey, ctx.getImageData(0, 0, width, height));
    }

    getCacheKey(waveformData, width, height) {
        // Create a simple hash for caching
        const dataHash = waveformData.slice(0, 10).join(',');
        return `${dataHash}_${width}_${height}`;
    }

    clearCache() {
        this.canvasCache.clear();
    }
}

// 🚀 MAIN DASHBOARD CONTROLLER (Revolutionary modular architecture!)
class BeatOrganizerDashboard {
    constructor() {
        this.taskManager = new TaskManager();
        this.notifications = new NotificationManager();
        this.audioPlayer = new AudioPlayer();
        this.waveformRenderer = new WaveformRenderer();
        
        this.currentFiles = [];
        this.currentDirectory = null;
        
        this.initializeEventListeners();
        this.checkAPIHealth();
        
        // Setup cleanup on page unload
        window.addEventListener('beforeunload', () => this.cleanup());
    }

    async checkAPIHealth() {
        try {
            const response = await fetch('/api/health');
            const health = await response.json();
            
            if (health.success) {
                console.log('🎵 Beat Organizer API is healthy');
                if (!health.dependencies.ffmpeg) {
                    this.notifications.show('⚠️ FFmpeg not available - some features limited', 'warning');
                }
            } else {
                this.notifications.show('❌ API health check failed', 'danger');
            }
        } catch (error) {
            this.notifications.show('🔌 Cannot connect to API - please start the server', 'danger');
        }
    }

    initializeEventListeners() {
        // Scan controls
        document.getElementById('scanBtn')?.addEventListener('click', () => this.startScan());
        document.getElementById('browseBtn')?.addEventListener('click', () => this.browseDirectory());
        
        // Progress tracking
        window.addEventListener('taskProgress', (e) => this.handleTaskProgress(e.detail));
        window.addEventListener('taskComplete', (e) => this.handleTaskComplete(e.detail));
        
        // Directory input
        document.getElementById('directoryPath')?.addEventListener('keypress', (e) => {
            if (e.key === 'Enter') this.startScan();
        });
        
        // Initialize rotating placeholder roasts
        this.initializeRotatingPlaceholder();
    }

    initializeRotatingPlaceholder() {
        const placeholderRoasts = [
            "C:\\Users\\YourName\\Music\\Beats (53 tracks, thousands of plays, international fans calling them 'masterpieces' = $5.53 total)",
            "C:\\Users\\YourName\\Music\\Beats (Billboard #1 in your bedroom = $5.53 total)",
            "C:\\Users\\YourName\\Music\\Beats (Grammy-worthy according to your mom)", 
            "C:\\Users\\YourName\\Music\\Beats (Fire beats, ice cold bank account)",
            "C:\\Users\\YourName\\Music\\Beats (Platinum status on SoundCloud, food stamps IRL)",
            "C:\\Users\\YourName\\Music\\Beats (More followers than income)",
            "C:\\Users\\YourName\\Music\\Beats (Producer by night, Uber driver by day)",
            "C:\\Users\\YourName\\Music\\Beats (Beats harder than your financial situation)",
            "C:\\Users\\YourName\\Music\\Beats (Rich in talent, poor in royalties)",
            "C:\\Users\\YourName\\Music\\Beats (Creating art while streaming platforms create poverty)"
        ];

        const directoryInput = document.getElementById('directoryPath');
        if (directoryInput) {
            let currentIndex = 0;
            
            // Set initial placeholder
            directoryInput.placeholder = placeholderRoasts[currentIndex];
            
            // Rotate every 3 seconds when input is empty and not focused
            setInterval(() => {
                if (!directoryInput.value.trim() && document.activeElement !== directoryInput) {
                    currentIndex = (currentIndex + 1) % placeholderRoasts.length;
                    directoryInput.placeholder = placeholderRoasts[currentIndex];
                }
            }, 3000);
        }
    }

    async startScan() {
        const directoryPath = document.getElementById('directoryPath')?.value?.trim();
        
        if (!directoryPath) {
            this.notifications.show('Please enter a directory path', 'warning');
            return;
        }

        try {
            this.showProgress('🔍 Starting comprehensive scan...');
            
            const taskId = await this.taskManager.startTask('/api/scan', {
                directory: directoryPath
            });
            
            this.currentTaskId = taskId;
            this.notifications.show('🚀 Scan started! Real-time progress will appear below.', 'success');
            
            // Start polling as fallback if WebSocket doesn't work (only if not already polling)
            if (!this.progressPoller) {
                this.startProgressPolling(taskId);
            }
            
        } catch (error) {
            this.hideProgress();
            this.notifications.show(`❌ Scan failed: ${error.message}`, 'danger');
        }
    }

    async browseDirectory() {
        try {
            const response = await fetch('/api/browse');
            const result = await response.json();
            
            if (result.success && result.directory) {
                document.getElementById('directoryPath').value = result.directory;
                this.notifications.show('📁 Directory selected!', 'success');
            } else {
                throw new Error(result.error || 'Failed to browse directory');
            }
        } catch (error) {
            this.notifications.show(`❌ Browse failed: ${error.message}`, 'danger');
        }
    }

    handleTaskProgress(data) {
        if (data.taskId === this.currentTaskId) {
            this.updateProgressDisplay(data);
        }
    }

    handleTaskComplete(data) {
        if (data.taskId === this.currentTaskId) {
            this.hideProgress();
            
            if (data.phase === 'completed' && data.result) {
                this.handleScanComplete(data.result);
            } else if (data.phase === 'failed') {
                this.notifications.show(`❌ Scan failed: ${data.error}`, 'danger');
            }
        }
    }

    handleScanComplete(result) {
        this.currentFiles = result.files || [];
        this.currentDirectory = result.directory;
        
        this.updateCollectionOverview(result);
        this.updateFileBrowser(this.currentFiles);
        this.updateDuplicateDisplay(result);
        
        const message = `✅ Scan complete! Found ${result.total_files} files with ${result.duplicate_groups_count || 0} duplicate groups.`;
        this.notifications.show(message, 'success');
    }

    updateProgressDisplay(data) {
        console.log('🎯 updateProgressDisplay called with:', data); // Debug log
        
        const progressContainer = document.getElementById('scanProgress');
        const progressBar = progressContainer?.querySelector('.progress-bar');
        const loadingText = progressContainer?.querySelector('.loading');
        
        if (!progressContainer) {
            console.log('❌ Progress container not found!');
            return;
        }
        
        progressContainer.classList.remove('hidden');
        
        if (progressBar) {
            progressBar.style.width = `${data.progress || 0}%`;
            this.setProgressBarColor(progressBar, data.phase);
            console.log('📊 Progress bar updated:', `${data.progress || 0}%`);
        }
        
        if (loadingText) {
            const message = this.getProgressMessage(data);
            loadingText.innerHTML = `
                <span class="spinner"></span>
                ${message}
            `;
            console.log('💬 Progress message updated:', message);
        }
    }

    setProgressBarColor(progressBar, phase) {
        const colorMap = {
            discovery: 'bg-primary',
            fingerprinting: 'bg-warning', 
            duplicates: 'bg-info',
            waveforms: 'bg-secondary',
            analysis: 'bg-warning',
            comparison: 'bg-success',
            finalizing: 'bg-success'
        };
        
        progressBar.className = 'progress-bar ' + (colorMap[phase] || 'bg-primary');
    }

    getProgressMessage(data) {
        const roasts = {
            discovering: [
                "🔍 Discovering audio files... Finding your hidden gems!",
                "🔍 Scanning files... Looking for beats better than what's on the radio",
                "🔍 Discovering files... Hunting for tracks that deserve more than $0.003 per stream"
            ],
            fingerprinting: [
                "🔑 Generating audio fingerprints... Each file gets more attention than artists get from labels",
                "🔑 Creating audio signatures... Still faster than waiting for Spotify payments",
                "🔑 Audio fingerprinting... This process pays better than streaming royalties",
                "🔑 Building waveform hashes... More reliable than record label promises",
                "🔑 Generating fingerprints... Each signature worth more than a million streams"
            ],
            duplicates: [
                "🕵️ Finding duplicates... Exposing fake copies like the music industry exposes talent",
                "🕵️ Duplicate detection... Cleaning up files better than labels clean up contracts",
                "🕵️ Hunting copies... Finding duplicates faster than labels find excuses not to pay",
                "🕵️ Exposing the imposters... Finding audio twins hiding in your collection",
                "🕵️ Duplicate hunt... Tracking down file clones with forensic precision"
            ],
            waveforms: [
                "🌊 Generating waveforms... Visual beauty that streaming platforms will never appreciate",
                "🌊 Creating audio visuals... These waveforms are worth more than your Spotify earnings",
                "🌊 Building waveform graphics... More artistic than anything on the Billboard charts",
                "🌊 Crafting visual soundwaves... Better than most music videos getting millions of views",
                "🌊 Waveform generation... Creating art that deserves more recognition than TikTok remixes"
            ],
            analyzing: [
                "📊 Analyzing audio quality... Organizing better than major label accounting",
                "📊 LUFS and peak analysis... Making files accessible, unlike streaming profits",
                "📊 Quality assessment... Professional analysis for your liberation army",
                "📊 Audio metrics analysis... Preparing your collection for inspection",
                "📊 Full audio analysis... More thorough than label A&R departments",
                "📊 Technical analysis... Getting the real specs while Spotify hides the real numbers",
                "📊 Audio forensics... Examining files with more care than labels examine contracts",
                "📊 Sound science... More accurate than Billboard's mysterious chart calculations"
            ],
            quality: [
                "⚖️ Comparing quality... Finding the best versions while streaming platforms pay the worst rates",
                "⚖️ Quality analysis... More attention to detail than record labels give to contracts",
                "⚖️ Ranking audio files... More fair than Spotify's $5.53 lifetime payment system",
                "⚖️ Quality comparison... These files get better treatment than artists on major labels",
                "⚖️ Judging audio merit... More honest than Billboard chart rankings",
                "⚖️ File evaluation... Still more accurate than Grammy nominations",
                "⚖️ Comparing versions... Finding gems worth more than a million TikTok plays",
                "⚖️ Quality assessment... More transparent than streaming royalty calculations"
            ],
            finalizing: [
                "✨ Finalizing results... Preparing your beats for world domination",
                "✨ Last steps... Getting ready to show those streaming overlords what real music looks like",
                "✨ Almost done... Your collection is about to be more organized than the music industry wishes it was",
                "✨ Final touches... Almost ready for your liberation army review"
            ]
        };

        // Map data.phase to roast categories
        let phase = 'discovering';
        const dataPhase = data.phase || '';
        
        if (dataPhase.includes('fingerprint') || dataPhase.includes('hashing')) {
            phase = 'fingerprinting';
        } else if (dataPhase.includes('duplicate')) {
            phase = 'duplicates';
        } else if (dataPhase.includes('waveform')) {
            phase = 'waveforms';
        } else if (dataPhase.includes('analysis') || dataPhase.includes('analyzing')) {
            phase = 'analyzing';
        } else if (dataPhase.includes('quality') || dataPhase.includes('comparison')) {
            phase = 'quality';
        } else if (dataPhase.includes('finalizing') || dataPhase.includes('complete')) {
            phase = 'finalizing';
        }

        const messages = roasts[phase];
        const randomMessage = messages[Math.floor(Math.random() * messages.length)];
        
        if (data.current_file) {
            return `${randomMessage}<br><small style="opacity: 0.8">${data.current_file}</small>`;
        }
        
        return randomMessage;
    }

    updateCollectionOverview(result) {
        document.getElementById('totalFiles').textContent = result.total_files || 0;
        document.getElementById('totalSize').textContent = result.total_size_formatted || '0 B';
        document.getElementById('duplicateCount').textContent = result.duplicate_files || 0;
        
        const wastedSpace = this.calculateWastedSpace(result.duplicate_groups || []);
        document.getElementById('wastedSpace').textContent = this.formatBytes(wastedSpace);
        
        document.getElementById('collectionOverview')?.classList.remove('hidden');
        
        if (result.duplicate_groups && result.duplicate_groups.length > 0) {
            document.getElementById('duplicateManager')?.classList.remove('hidden');
        }
    }

    calculateWastedSpace(duplicateGroups) {
        return duplicateGroups.reduce((total, group) => {
            const fileSizes = group.files?.map(f => f.filesize || 0) || [];
            const largestFile = Math.max(...fileSizes);
            const totalGroupSize = fileSizes.reduce((sum, size) => sum + size, 0);
            return total + (totalGroupSize - largestFile);
        }, 0);
    }

    updateFileBrowser(files) {
        const fileList = document.getElementById('fileList');
        if (!fileList) return;
        
        fileList.innerHTML = '';
        
        files.forEach((file, index) => {
            const fileItem = this.createFileItem(file, index);
            fileList.appendChild(fileItem);
        });
        
        document.getElementById('fileBrowser')?.classList.remove('hidden');
    }

    createFileItem(file, index) {
        const fileItem = document.createElement('div');
        fileItem.className = 'file-item';
        fileItem.dataset.index = index;
        
        const hasWaveform = file.waveform && file.waveform.length > 0;
        
        fileItem.innerHTML = `
            <div class="file-info">
                <i class="fas fa-music file-icon"></i>
                <div class="file-details">
                    <div class="file-name">${file.filename}</div>
                    <div class="file-meta">
                        ${file.filesize_formatted || this.formatBytes(file.filesize || 0)} • 
                        ${file.duration_formatted || 'Unknown'} • 
                        ${(file.format || '').toUpperCase()}
                    </div>
                    ${hasWaveform ? 
                        `<div class="file-waveform-container">
                            <canvas class="file-waveform" width="200" height="30"></canvas>
                         </div>` : 
                        `<div class="file-waveform-placeholder">
                            <span class="text-muted">Click analyze for waveform</span>
                         </div>`
                    }
                </div>
            </div>
            <div class="file-actions">
                <button class="btn btn-sm btn-outline-primary play-btn" data-filepath="${file.filepath}">
                    <i class="fas fa-play"></i> Play
                </button>
                <button class="btn btn-sm btn-outline-secondary analyze-btn" data-filepath="${file.filepath}">
                    <i class="fas fa-microscope"></i> Analyze
                </button>
            </div>
        `;
        
        // Render waveform if available
        if (hasWaveform) {
            const canvas = fileItem.querySelector('.file-waveform');
            setTimeout(() => {
                this.waveformRenderer.renderToCanvas(canvas, file.waveform);
            }, 0);
        }
        
        // Add event listeners
        this.addFileItemListeners(fileItem);
        
        return fileItem;
    }

    addFileItemListeners(fileItem) {
        const playBtn = fileItem.querySelector('.play-btn');
        const analyzeBtn = fileItem.querySelector('.analyze-btn');
        
        playBtn?.addEventListener('click', (e) => {
            const filepath = e.target.closest('.play-btn').dataset.filepath;
            const filename = fileItem.querySelector('.file-name').textContent;
            this.playAudio(filepath, filename, playBtn);
        });
        
        analyzeBtn?.addEventListener('click', (e) => {
            const filepath = e.target.closest('.analyze-btn').dataset.filepath;
            this.analyzeFile(filepath);
        });
    }

    async playAudio(filepath, filename, button) {
        try {
            // If this file is currently playing, pause it
            if (this.audioPlayer.currentButton === button && 
                this.audioPlayer.currentAudio && !this.audioPlayer.currentAudio.paused) {
                this.audioPlayer.pause();
                return;
            }
            
            await this.audioPlayer.play(filepath, filename, button);
            this.notifications.show(`🎵 Playing: ${filename}`, 'info', 3000);
            
        } catch (error) {
            this.notifications.show(`❌ Failed to play: ${error.message}`, 'danger');
        }
    }

    async analyzeFile(filepath) {
        try {
            this.showProgress('🔬 Analyzing audio file...');
            
            const response = await fetch('/api/analyze', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ filepath })
            });
            
            const result = await response.json();
            
            if (result.success) {
                this.showAnalysisResults(result);
                this.notifications.show(`✅ Analysis complete: ${result.quality.label}`, 'success');
            } else {
                throw new Error(result.error || 'Analysis failed');
            }
            
        } catch (error) {
            this.notifications.show(`❌ Analysis failed: ${error.message}`, 'danger');
        } finally {
            this.hideProgress();
        }
    }

    showAnalysisResults(result) {
        // Implementation for showing detailed analysis results
        // This would open a modal or expand a section with the analysis data
        console.log('📊 Analysis results:', result);
    }

    updateDuplicateDisplay(result) {
        const duplicateGroups = document.getElementById('duplicateGroups');
        if (!duplicateGroups) return;
        
        duplicateGroups.innerHTML = '';
        
        const groups = result.duplicate_groups || [];
        
        if (groups.length === 0) {
            duplicateGroups.innerHTML = `
                <div class="no-duplicates">
                    <h3>🎉 No duplicates found!</h3>
                    <p>Your collection is clean - no duplicate files detected.</p>
                </div>
            `;
            return;
        }
        
        groups.forEach((group, index) => {
            const groupElement = this.createDuplicateGroup(group, index);
            duplicateGroups.appendChild(groupElement);
        });
    }

    createDuplicateGroup(group, index) {
        const groupDiv = document.createElement('div');
        groupDiv.className = 'duplicate-group';
        
        groupDiv.innerHTML = `
            <div class="duplicate-header">
                <h4>🔄 Duplicate Group ${index + 1}</h4>
                <div class="duplicate-stats">
                    <span class="stat-item">
                        <i class="fas fa-copy"></i> ${group.count} files
                    </span>
                    <span class="stat-item">
                        <i class="fas fa-weight"></i> ${group.total_size_formatted}
                    </span>
                </div>
            </div>
            <div class="duplicate-files">
                ${group.files?.map((file, fileIndex) => this.createDuplicateFileHTML(file, fileIndex)).join('') || ''}
            </div>
        `;
        
        return groupDiv;
    }

    createDuplicateFileHTML(file, index) {
        return `
            <div class="duplicate-file ${index === 0 ? 'recommended' : ''}" data-filepath="${file.filepath}">
                <div class="file-header">
                    <div class="file-info">
                        <strong class="filename">${file.filename}</strong>
                        <div class="quality-badge quality-${file.quality_hint || 'unknown'}">
                            ${this.getQualityIcon(file.quality_hint)} ${(file.quality_hint || 'unknown').toUpperCase()}
                            ${index === 0 ? ' (RECOMMENDED)' : ''}
                        </div>
                    </div>
                    <div class="file-actions">
                        <button class="btn btn-sm btn-outline-primary play-btn" data-filepath="${file.filepath}">
                            <i class="fas fa-play"></i>
                        </button>
                        <button class="btn btn-sm btn-outline-danger delete-btn" data-filepath="${file.filepath}">
                            <i class="fas fa-trash"></i>
                        </button>
                    </div>
                </div>
                <div class="file-details">
                    <span><i class="fas fa-file"></i> ${file.filesize_formatted}</span>
                    <span><i class="fas fa-clock"></i> ${file.duration_formatted || 'Unknown'}</span>
                    <span><i class="fas fa-music"></i> ${(file.format || '').toUpperCase()}</span>
                </div>
                <div class="file-path" title="${file.filepath}">${file.filepath}</div>
            </div>
        `;
    }

    getQualityIcon(quality) {
        const icons = {
            best: '🏆',
            good: '✅', 
            acceptable: '⚠️',
            poor: '❌',
            unknown: '❓'
        };
        return icons[quality] || '❓';
    }

    formatBytes(bytes) {
        if (!bytes) return '0 B';
        const k = 1024;
        const sizes = ['B', 'KB', 'MB', 'GB'];
        const i = Math.floor(Math.log(bytes) / Math.log(k));
        return parseFloat((bytes / Math.pow(k, i)).toFixed(1)) + ' ' + sizes[i];
    }

    showProgress(message) {
        const progress = document.getElementById('scanProgress');
        if (progress) {
            progress.classList.remove('hidden');
            const loadingText = progress.querySelector('.loading');
            if (loadingText) {
                loadingText.innerHTML = `<span class="spinner"></span> ${message}`;
            }
        }
    }

    hideProgress() {
        const progress = document.getElementById('scanProgress');
        if (progress) {
            progress.classList.add('hidden');
        }
    }

    startProgressPolling(taskId) {
        if (this.progressPoller) {
            clearInterval(this.progressPoller);
        }
        
        let pollCount = 0;
        const maxPolls = 300; // 5 minutes max (300 seconds)
        
        this.progressPoller = setInterval(async () => {
            try {
                pollCount++;
                
                // Safety: stop polling after max attempts
                if (pollCount > maxPolls) {
                    console.log('⚠️ Polling timeout reached, stopping');
                    clearInterval(this.progressPoller);
                    this.progressPoller = null;
                    this.notifications.show('⚠️ Polling timeout - please refresh if scan is still running', 'warning');
                    return;
                }
                
                const response = await fetch(`/api/scan/progress?task_id=${taskId}`);
                const result = await response.json();
                
                console.log('📊 Polling progress:', result); // Debug log
                
                if (result.success && result.task) {
                    console.log('📈 Updating progress display:', {
                        progress: result.task.progress,
                        phase: result.task.phase,
                        current_file: result.task.current_file,
                        status: result.task.status
                    }); // Debug log
                    
                    this.updateProgressDisplay({
                        progress: result.task.progress || 0,
                        phase: result.task.phase || 'running',
                        current_file: result.task.current_file || '',
                        completed: result.task.completed || 0,
                        total: result.task.total || 0
                    });
                    
                    // Stop polling when complete
                    if (result.task.status === 'completed' || result.task.status === 'failed') {
                        console.log('🛑 Task completed, stopping polling');
                        clearInterval(this.progressPoller);
                        this.progressPoller = null;
                        this.handleTaskComplete({
                            taskId: taskId,
                            phase: result.task.status,
                            result: result.task.result,
                            error: result.task.error
                        });
                    }
                }
                // Check direct result properties (alternative API format)
                else if (result.scanning === false && result.result) {
                    console.log('🛑 Scan completed (direct format), stopping polling');
                    clearInterval(this.progressPoller);
                    this.progressPoller = null;
                    this.handleTaskComplete({
                        taskId: taskId,
                        phase: 'completed',
                        result: result.result,
                        error: result.error
                    });
                }
            } catch (error) {
                console.error('❌ Progress polling failed:', error);
            }
        }, 1000); // Poll every second
    }

    // 🧹 CLEANUP METHODS (Prevent memory leaks!)
    cleanup() {
        this.taskManager.cleanup();
        this.notifications.cleanup();
        this.audioPlayer.stop();
        this.waveformRenderer.clearCache();
        
        // Remove all event listeners
        window.removeEventListener('taskProgress', this.handleTaskProgress);
        window.removeEventListener('taskComplete', this.handleTaskComplete);
        
        console.log('🧹 Beat Organizer Dashboard cleaned up');
    }
}

// 🚀 INITIALIZE THE REVOLUTION
let dashboard;

document.addEventListener('DOMContentLoaded', () => {
    console.log('🎵 Initializing Producer\'s Liberation Army Dashboard...');
    dashboard = new BeatOrganizerDashboard();
    console.log('⚡ Revolutionary architecture loaded successfully!');
});

// Add CSS animations
const style = document.createElement('style');
style.textContent = `
    @keyframes slideInRight {
        from { transform: translateX(100%); opacity: 0; }
        to { transform: translateX(0); opacity: 1; }
    }
    
    @keyframes slideOutRight {
        from { transform: translateX(0); opacity: 1; }
        to { transform: translateX(100%); opacity: 0; }
    }
    
    .spinner {
        display: inline-block;
        width: 1rem;
        height: 1rem;
        border: 2px solid rgba(255,255,255,0.3);
        border-radius: 50%;
        border-top-color: #fff;
        animation: spin 1s ease-in-out infinite;
    }
    
    @keyframes spin {
        to { transform: rotate(360deg); }
    }
`;
document.head.appendChild(style);

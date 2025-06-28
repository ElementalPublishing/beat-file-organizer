/*
 * Elemental Publishing - Beat File Organizer Dashboard
 * Professional Music Producer Interface
 * Artist Liberation War - "Something Different"
 */

class BeatOrganizerDashboard {
    constructor() {
        this.currentFiles = [];
        this.currentAnalysis = null;
        this.currentDirectory = null;
        this.isScanning = false;
        this.currentAudio = null;
        this.filesToDelete = new Set();
        this.initializeEventListeners();
        this.checkAPIHealth();
    }

    // Initialize all event listeners
    initializeEventListeners() {
        // Directory scanning
        document.getElementById('scanBtn').addEventListener('click', () => this.scanDirectory());
        document.getElementById('browseBtn').addEventListener('click', () => this.browseDirectory());
        
        // Analysis
        document.getElementById('analyzeAllBtn').addEventListener('click', () => this.analyzeCollection());
        
        // Sorting
        document.getElementById('sortByName').addEventListener('click', () => this.sortFiles('name'));
        document.getElementById('sortBySize').addEventListener('click', () => this.sortFiles('size'));
        document.getElementById('sortByQuality').addEventListener('click', () => this.sortFiles('quality'));
        
        // Duplicate management
        document.getElementById('autoResolveDuplicates').addEventListener('click', () => this.autoResolveDuplicates());
        
        // Audio analyzer
        document.getElementById('closeAnalyzer').addEventListener('click', () => this.closeAnalyzer());
        
        // Export
        document.getElementById('exportReportBtn').addEventListener('click', () => this.exportReport());
        
        // Cancel scan
        document.getElementById('cancelScanBtn').addEventListener('click', () => this.cancelScan());
        
        // Directory path input
        document.getElementById('directoryPath').addEventListener('keypress', (e) => {
            if (e.key === 'Enter') {
                this.scanDirectory();
            }
        });
    }

    // Check API health on startup
    async checkAPIHealth() {
        try {
            const response = await fetch('/api/health');
            const health = await response.json();
            
            if (health.success) {
                console.log('🎵 Beat Organizer API is healthy');
                if (!health.dependencies.ffmpeg) {
                    this.showNotification('⚠️ FFmpeg not available - some features limited', 'warning');
                }
            } else {
                this.showNotification('❌ API health check failed', 'danger');
            }
        } catch (error) {
            this.showNotification('🔌 Cannot connect to API - please start the server', 'danger');
        }
    }

    // Browse for directory using backend file dialog
    async browseDirectory() {
        try {
            this.showNotification('🔍 Opening directory browser...', 'info');
            
            const response = await fetch('/api/browse');
            const result = await response.json();
            
            if (result.success && result.directory) {
                // Set the directory path in the input field
                document.getElementById('directoryPath').value = result.directory;
                this.showNotification('📁 Directory selected! Ready to scan your beats and expose the streaming economy\'s $5.53 insult.', 'success');
            } else {
                if (result.error === 'No directory selected') {
                    this.showNotification('📂 No directory selected - the revolution waits for no one!', 'warning');
                } else if (result.error.includes('tkinter not installed')) {
                    // Fallback to HTML5 directory picker
                    this.browseDirectoryHTML5();
                } else {
                    this.showNotification(`❌ Browse error: ${result.error}`, 'danger');
                }
            }
        } catch (error) {
            console.error('Browse directory error:', error);
            this.showNotification('🔌 Network error - trying fallback browser picker...', 'warning');
            // Fallback to HTML5 directory picker
            this.browseDirectoryHTML5();
        }
    }

    // Fallback HTML5 directory picker (less reliable for paths)
    browseDirectoryHTML5() {
        const dirInput = document.createElement('input');
        dirInput.type = 'file';
        dirInput.webkitdirectory = true;
        dirInput.multiple = true;
        dirInput.style.display = 'none';
        
        dirInput.onchange = (event) => {
            const files = event.target.files;
            if (files.length > 0) {
                const firstFile = files[0];
                const pathParts = firstFile.webkitRelativePath.split('/');
                pathParts.pop(); // Remove filename
                
                // Try to get the full path (limited browser support)
                let directoryPath = '';
                if (firstFile.path) {
                    directoryPath = firstFile.path.substring(0, firstFile.path.lastIndexOf('\\'));
                } else {
                    directoryPath = pathParts.join('/');
                }
                
                document.getElementById('directoryPath').value = directoryPath || pathParts.join('/');
                this.showNotification('📁 Directory selected (browser fallback)! Note: you may need to manually verify the path.', 'warning');
            }
        };
        
        document.body.appendChild(dirInput);
        dirInput.click();
        document.body.removeChild(dirInput);
    }

    // Scan directory for audio files
    async scanDirectory() {
        const directoryPath = document.getElementById('directoryPath').value.trim();
        
        if (!directoryPath) {
            this.showNotification('Please enter a directory path', 'warning');
            return;
        }

        // Prevent multiple simultaneous scans
        if (this.isScanning) {
            this.showNotification('⏳ Scan already in progress! Please wait...', 'warning');
            return;
        }

        // Lock scanning
        this.isScanning = true;
        
        // Disable scan button
        const scanBtn = document.getElementById('scanBtn');
        const originalText = scanBtn.textContent;
        scanBtn.disabled = true;
        scanBtn.textContent = 'Scanning...';

        // Start the scan
        this.showProgress('Starting scan...');
        
        try {
            const response = await fetch('/api/scan', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify({
                    directory: directoryPath
                })
            });

            const result = await response.json();
            
            if (result.success) {
                // Start polling for progress
                this.pollScanProgress();
            } else {
                this.hideProgress();
                this.showNotification(`❌ Scan failed: ${result.error}`, 'danger');
                this.resetScanState(scanBtn, originalText);
            }
        } catch (error) {
            this.hideProgress();
            this.showNotification(`🔌 Network error: ${error.message}`, 'danger');
            this.resetScanState(scanBtn, originalText);
        }
    }

    // Reset scan state when scan completes or fails
    resetScanState(scanBtn, originalText) {
        this.isScanning = false;
        scanBtn.disabled = false;
        scanBtn.textContent = originalText || 'Scan Directory';
    }

    // Poll for scan progress
    async pollScanProgress() {
        try {
            const response = await fetch('/api/scan/progress');
            const progress = await response.json();
            
            if (progress.scanning || (!progress.result && !progress.error)) {
                // Still processing - keep updating progress
                this.updateProgressDisplay(progress);
                
                // Continue polling
                setTimeout(() => this.pollScanProgress(), 500);
            } else if (progress.result) {
                // Scan completed successfully
                this.currentFiles = progress.result.files;
                this.currentDirectory = progress.result.directory;
                this.updateCollectionOverview(progress.result);
                this.updateFileBrowser(progress.result.files);
                
                // Update duplicate display with results from the scan
                this.updateDuplicateDisplay(progress.result);
                
                this.hideProgress();
                this.showNotification(`✅ Found ${progress.result.total_files} audio files - fans called them 'masterpieces' but streaming paid $0.0000112 per play`, 'success');
                
                // Reset scan state
                this.resetScanState(document.getElementById('scanBtn'), 'Scan Directory');
            } else if (progress.error) {
                // Scan failed
                this.hideProgress();
                this.showNotification(`❌ Scan failed: ${progress.error}`, 'danger');
                this.resetScanState(document.getElementById('scanBtn'), 'Scan Directory');
            }
        } catch (error) {
            console.error('Progress polling error:', error);
            this.hideProgress();
            this.showNotification('🔌 Lost connection to server', 'danger');
            this.resetScanState(document.getElementById('scanBtn'), 'Scan Directory');
        }
    }

    // Update progress display with real-time info
    updateProgressDisplay(progress) {
        const progressContainer = document.getElementById('scanProgress');
        const progressBar = progressContainer.querySelector('.progress-bar');
        const loadingText = progressContainer.querySelector('.loading');
        
        // Show progress container
        progressContainer.classList.remove('hidden');
        
        // Update progress bar
        const progressPercent = progress.progress || 0;
        progressBar.style.width = `${progressPercent}%`;
        
        // Change progress bar color based on phase
        const currentFile = progress.current_file || '';
        progressBar.className = 'progress-bar'; // Reset classes
        
        if (currentFile.includes('Phase 1') || currentFile.includes('Discovering') || currentFile.includes('Discovery')) {
            progressBar.classList.add('bg-primary'); // Blue for discovery
        } else if (currentFile.includes('Phase 2') || currentFile.includes('fingerprint') || currentFile.includes('Fingerprint')) {
            progressBar.classList.add('bg-warning'); // Yellow for fingerprinting
        } else if (currentFile.includes('Phase 3') || currentFile.includes('duplicate') || currentFile.includes('Duplicate')) {
            progressBar.classList.add('bg-info'); // Blue for duplicate detection
        } else if (currentFile.includes('Phase 4') || currentFile.includes('Analyzing') || currentFile.includes('analysis')) {
            progressBar.classList.add('bg-secondary'); // Gray for analysis
        } else if (currentFile.includes('Phase 5') || currentFile.includes('Preparing') || currentFile.includes('Final')) {
            progressBar.classList.add('bg-success'); // Green for finalizing
        } else {
            progressBar.classList.add('bg-primary'); // Default blue
        }
        
        // Generate entertaining status messages with roasts
        let statusText = this.getProgressMessage(progress);
        
        if (progress.completed_files && progress.total_files) {
            statusText += ` (${progress.completed_files}/${progress.total_files})`;
        }
        
        loadingText.innerHTML = `
            <span class="spinner"></span>
            ${statusText}
        `;
    }

    // Generate entertaining progress messages based on current phase
    getProgressMessage(progress) {
        const roasts = {
            discovering: [
                "🔍 Discovering audio files... Finding your hidden gems!",
                "🔍 Scanning files... Looking for beats better than what's on the radio",
                "🔍 Discovering files... Hunting for tracks that deserve more than $0.003 per stream"
            ],
            hashing: [
                "� Generating audio fingerprints... Each file gets more attention than artists get from labels",
                "� Creating audio signatures... Still faster than waiting for Spotify payments",
                "� Audio fingerprinting... This process pays better than streaming royalties",
                "� Building waveform hashes... More reliable than record label promises",
                "� Generating fingerprints... Each signature worth more than a million streams"
            ],
            duplicates: [
                "🔍 Finding duplicates... Exposing fake copies like the music industry exposes talent",
                "🔍 Duplicate detection... Cleaning up files better than labels clean up contracts",
                "🔍 Hunting copies... Finding duplicates faster than labels find excuses not to pay",
                "🕵️ Exposing the imposters... Finding audio twins hiding in your collection",
                "🔍 Duplicate hunt... Tracking down file clones with forensic precision"
            ],
            processing: [
                "📊 Analyzing audio quality... Organizing better than major label accounting",
                "📊 LUFS and peak analysis... Making files accessible, unlike streaming profits",
                "📊 Quality assessment... Professional analysis for your liberation army",
                "📊 Audio metrics analysis... Preparing your collection for inspection",
                "📊 Full audio analysis... More thorough than label A&R departments"
            ],
            finalizing: [
                "✨ Finalizing results... Preparing your beats for world domination",
                "✨ Last steps... Getting ready to show those streaming overlords what real music looks like",
                "✨ Almost done... Your collection is about to be more organized than the music industry wishes it was",
                "✨ Final touches... Almost ready for your liberation army review"
            ]
        };

        // Determine current phase based on progress percentage and message content
        let phase = 'discovering';
        let currentFile = progress.current_file || '';
        let progressPercent = progress.progress || 0;
        
        // Match the new backend phases
        if (currentFile.includes('Phase 1') || currentFile.includes('Discovering') || currentFile.includes('Discovery')) {
            phase = 'discovering';
        } else if (currentFile.includes('Phase 2') || currentFile.includes('fingerprint') || currentFile.includes('Fingerprint')) {
            phase = 'hashing'; // Fingerprinting maps to hashing messages
        } else if (currentFile.includes('Phase 3') || currentFile.includes('duplicate') || currentFile.includes('Duplicate')) {
            phase = 'duplicates';
        } else if (currentFile.includes('Phase 4') || currentFile.includes('analysis') || currentFile.includes('Analysis') || currentFile.includes('LUFS')) {
            phase = 'processing'; // Full analysis maps to processing messages
        } else if (currentFile.includes('Phase 5') || currentFile.includes('Preparing') || currentFile.includes('Final')) {
            phase = 'finalizing';
        } else if (progressPercent >= 95) {
            phase = 'finalizing';
        } else if (progressPercent >= 65 && progressPercent < 95) {
            // Analysis phase (65-95%)
            phase = 'processing';
        } else if (progressPercent >= 50 && progressPercent < 65) {
            // Duplicate detection phase (50-65%)
            phase = 'duplicates';
        } else if (progressPercent >= 20 && progressPercent < 50) {
            // Fingerprinting phase (20-50%)
            phase = 'hashing';
        } else {
            // Discovery phase (0-20%)
            phase = 'discovering';
        }

        const messages = roasts[phase];
        const randomMessage = messages[Math.floor(Math.random() * messages.length)];
        
        // If we have specific file info, show it with the roast
        if (progress.current_file && !progress.current_file.includes('...')) {
            return `${randomMessage}<br><small style="opacity: 0.8">${progress.current_file}</small>`;
        }
        
        return randomMessage;
    }

    // Update collection overview display
    updateCollectionOverview(scanResult) {
        document.getElementById('totalFiles').textContent = scanResult.total_files;
        document.getElementById('totalSize').textContent = scanResult.total_size_formatted || this.formatBytes(scanResult.total_size || 0);
        
        // Update duplicate information
        document.getElementById('duplicateCount').textContent = scanResult.duplicate_files || 0;
        document.getElementById('wastedSpace').textContent = scanResult.wasted_space_formatted || this.formatBytes(scanResult.wasted_space || 0);
        
        // Show the collection overview
        document.getElementById('collectionOverview').classList.remove('hidden');
        
        // Show duplicate manager if duplicates found
        if (scanResult.duplicate_groups > 0) {
            document.getElementById('duplicateManager').classList.remove('hidden');
            this.updateDuplicateDisplay(scanResult);
        }
    }

    // Update file browser
    updateFileBrowser(files) {
        const fileList = document.getElementById('fileList');
        fileList.innerHTML = '';

        files.forEach(file => {
            const fileItem = document.createElement('div');
            fileItem.className = 'file-item';
            
            fileItem.innerHTML = `
                <div class="file-info">
                    <i class="fas fa-music file-icon"></i>
                    <div class="file-details">
                        <div class="file-name">${file.filename}</div>
                        <div class="file-meta">
                            ${file.filesize_formatted} • ${file.duration_formatted} • ${file.format.toUpperCase()}
                        </div>
                    </div>
                </div>
                <div class="flex items-center gap-1">
                    <button class="btn btn-success btn-sm play-btn" data-filepath="${file.filepath}">
                        <i class="fas fa-play"></i>
                        Play
                    </button>
                    <button class="btn btn-secondary analyze-btn" data-filepath="${file.filepath}">
                        <i class="fas fa-microscope"></i>
                        Analyze
                    </button>
                </div>
            `;
            
            // Add event listeners to buttons
            const analyzeBtn = fileItem.querySelector('.analyze-btn');
            const playBtn = fileItem.querySelector('.play-btn');
            
            analyzeBtn.addEventListener('click', () => {
                this.analyzeFile(file.filepath);
            });
            
            playBtn.addEventListener('click', () => {
                this.playAudio(file.filepath, file.filename);
            });
            
            fileList.appendChild(fileItem);
        });

        // Show the file browser
        document.getElementById('fileBrowser').classList.remove('hidden');
    }

    // Analyze a single file
    async analyzeFile(filepath) {
        this.showProgress('Analyzing audio file...');
        
        try {
            const response = await fetch('/api/analyze', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify({
                    filepath: filepath
                })
            });

            const result = await response.json();
            
            if (result.success) {
                this.showAnalyzer(result);
                this.hideProgress();
                this.showNotification(`✅ Analysis complete: ${result.quality.label}`, 'success');
            } else {
                this.hideProgress();
                this.showNotification(`❌ Analysis failed: ${result.error}`, 'danger');
            }
        } catch (error) {
            this.hideProgress();
            this.showNotification(`🔌 Network error: ${error.message}`, 'danger');
        }
    }

    // Show audio analyzer with results
    showAnalyzer(analysisResult) {
        this.currentAnalysis = analysisResult;
        
        // Update analyzer content
        document.getElementById('analyzingFileName').textContent = analysisResult.filename;
        
        // Update quality badge
        const badge = document.getElementById('analyzerQualityBadge');
        badge.innerHTML = `<span class="quality-badge quality-${analysisResult.quality.level.replace('_', '-')}">${analysisResult.quality.label}</span>`;
        
        // Update metrics
        const metrics = analysisResult.metrics;
        document.getElementById('lufsValue').textContent = metrics.lufs ? `${metrics.lufs.toFixed(1)}` : '--';
        document.getElementById('truePeakValue').textContent = metrics.true_peak ? `${metrics.true_peak.toFixed(1)} dB` : '--';
        document.getElementById('dynamicRangeValue').textContent = metrics.dynamic_range ? `${metrics.dynamic_range.toFixed(1)} LU` : '--';
        document.getElementById('qualityScoreValue').textContent = metrics.quality_score ? `${metrics.quality_score}/100` : '--';
        
        // Update recommendations
        this.updateRecommendations('analysisRecommendations', analysisResult.quality.recommendations);
        
        // Show the analyzer
        document.getElementById('audioAnalyzer').classList.remove('hidden');
        
        // Generate waveform
        this.generateWaveform(analysisResult.filepath);
    }

    // Generate waveform visualization
    async generateWaveform(filepath) {
        try {
            const response = await fetch('/api/waveform', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify({
                    filepath: filepath,
                    width: 800,
                    height: 120
                })
            });

            const result = await response.json();
            
            if (result.success) {
                // Display waveform data
                this.renderWaveform(result.waveform);
            } else {
                document.getElementById('waveformDisplay').innerHTML = `
                    <div style="display: flex; align-items: center; justify-content: center; height: 100%; color: rgba(245, 245, 245, 0.5);">
                        <i class="fas fa-exclamation-triangle" style="margin-right: 1rem;"></i>
                        Waveform generation failed
                    </div>
                `;
            }
        } catch (error) {
            console.log('Waveform generation error:', error);
        }
    }

    // Render waveform data as SVG
    renderWaveform(waveformData) {
        if (!waveformData || waveformData.length === 0) return;
        
        const container = document.getElementById('waveformDisplay');
        const width = 800;
        const height = 120;
        
        // Create SVG
        const svg = document.createElementNS('http://www.w3.org/2000/svg', 'svg');
        svg.setAttribute('width', '100%');
        svg.setAttribute('height', height);
        svg.setAttribute('viewBox', `0 0 ${width} ${height}`);
        
        // Create waveform path
        const path = document.createElementNS('http://www.w3.org/2000/svg', 'path');
        let pathData = `M 0 ${height/2}`;
        
        waveformData.forEach((value, index) => {
            const x = (index / waveformData.length) * width;
            const y = (height/2) - value;
            pathData += ` L ${x} ${y}`;
        });
        
        // Mirror for symmetrical waveform
        waveformData.reverse().forEach((value, index) => {
            const x = width - (index / waveformData.length) * width;
            const y = (height/2) + value;
            pathData += ` L ${x} ${y}`;
        });
        
        pathData += ' Z';
        
        path.setAttribute('d', pathData);
        path.setAttribute('fill', 'rgba(233, 69, 96, 0.3)');
        path.setAttribute('stroke', 'var(--ep-accent)');
        path.setAttribute('stroke-width', '1');
        
        svg.appendChild(path);
        container.innerHTML = '';
        container.appendChild(svg);
    }

    // Close analyzer
    closeAnalyzer() {
        document.getElementById('audioAnalyzer').classList.add('hidden');
        this.currentAnalysis = null;
    }

    // Find duplicate files
    // Mark file for deletion (placeholder)
    markForDeletion(filepath) {
        console.log(`🗑️ Marking file for deletion: ${filepath}`);
        
        this.filesToDelete.add(filepath);
        
        // Update UI to show file is marked for deletion
        const fileElement = document.querySelector(`[data-filepath="${filepath}"]`);
        if (fileElement) {
            fileElement.style.opacity = '0.5';
            fileElement.classList.add('marked-for-deletion');
            
            const deleteBtn = fileElement.querySelector('.delete-btn');
            if (deleteBtn) {
                deleteBtn.innerHTML = '<i class="fas fa-check"></i> Marked';
                deleteBtn.disabled = true;
                deleteBtn.classList.remove('btn-outline-danger');
                deleteBtn.classList.add('btn-success');
            }
        }
        
        this.updateDeletionCounter();
        this.showSuccess(`File marked for deletion: ${filepath.split('/').pop()}`);
    }

    // Auto resolve duplicates (placeholder)
    autoResolveDuplicates() {
        this.showNotification('🤖 Smart cleanup feature coming soon', 'info');
    }

    // Analyze entire collection
    async analyzeCollection() {
        if (!this.currentDirectory) return;
        
        this.showProgress('Analyzing collection quality...');
        
        try {
            const response = await fetch('/api/collection-stats', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify({
                    directory: this.currentDirectory
                })
            });

            const result = await response.json();
            
            if (result.success) {
                this.updateQualityAnalysis(result);
                this.hideProgress();
                this.showNotification('✅ Collection analysis complete - your beats earned international acclaim but streaming platforms paid lunch money', 'success');
            } else {
                this.hideProgress();
                this.showNotification(`❌ Analysis failed: ${result.error}`, 'danger');
            }
        } catch (error) {
            this.hideProgress();
            this.showNotification(`🔌 Network error: ${error.message}`, 'danger');
        }
    }

    // Update quality analysis display
    updateQualityAnalysis(statsResult) {
        const quality = statsResult.quality_stats || {};
        
        document.getElementById('streamingReady').textContent = quality.STREAMING_READY || 0;
        document.getElementById('clippedFiles').textContent = quality.CLIPPED || 0;
        document.getElementById('loudFiles').textContent = quality.TOO_LOUD || 0;
        document.getElementById('quietFiles').textContent = quality.TOO_QUIET || 0;
        
        // Update recommendations
        this.updateRecommendations('qualityRecommendations', statsResult.recommendations || []);
        
        // Show quality analysis
        document.getElementById('qualityAnalysis').classList.remove('hidden');
    }

    // Update recommendations display
    updateRecommendations(containerId, recommendations) {
        const container = document.getElementById(containerId);
        container.innerHTML = '';

        if (recommendations.length === 0) {
            container.innerHTML = '<p style="color: rgba(245, 245, 245, 0.6); text-align: center;">No specific recommendations at this time.</p>';
            return;
        }

        recommendations.forEach(rec => {
            const recDiv = document.createElement('div');
            recDiv.className = `alert alert-${rec.type || 'info'}`;
            recDiv.style.cssText = `
                padding: 1rem;
                margin: 0.5rem 0;
                border-radius: 8px;
                border-left: 4px solid var(--ep-${rec.type === 'critical' ? 'danger' : rec.type === 'warning' ? 'warning' : 'accent'});
                background: rgba(${rec.type === 'critical' ? '231, 76, 60' : rec.type === 'warning' ? '243, 156, 18' : '233, 69, 96'}, 0.1);
            `;
            
            recDiv.innerHTML = `
                <div style="display: flex; align-items: center; gap: 0.5rem;">
                    <i class="fas fa-${rec.type === 'critical' ? 'exclamation-triangle' : rec.type === 'warning' ? 'exclamation-circle' : 'info-circle'}"></i>
                    <span>${rec.message || rec}</span>
                </div>
            `;
            
            container.appendChild(recDiv);
        });
    }

    // Sort files
    sortFiles(sortBy) {
        if (!this.currentFiles.length) return;
        
        let sortedFiles = [...this.currentFiles];
        
        switch (sortBy) {
            case 'name':
                sortedFiles.sort((a, b) => a.filename.localeCompare(b.filename));
                break;
            case 'size':
                sortedFiles.sort((a, b) => b.filesize - a.filesize);
                break;
            case 'quality':
                // Sort by quality would require analysis data
                this.showNotification('Quality sorting requires analysis first', 'info');
                return;
        }
        
        this.updateFileBrowser(sortedFiles);
        this.showNotification(`📋 Files sorted by ${sortBy}`, 'success');
    }

    // Export report (placeholder)
    exportReport() {
        this.showNotification('📊 Export feature coming soon', 'info');
    }

    // Audio playback functionality
    playAudio(filepath, filename) {
        console.log(`🎵 Playing audio file: ${filepath}`);
        
        // Stop current audio if playing
        if (this.currentAudio && !this.currentAudio.paused) {
            this.currentAudio.pause();
            this.currentAudio.currentTime = 0;
        }
        
        // Request audio file from server
        fetch('/api/audio', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ filepath: filepath })
        })
        .then(response => {
            if (!response.ok) {
                throw new Error('Failed to load audio file');
            }
            return response.blob();
        })
        .then(blob => {
            const audioUrl = URL.createObjectURL(blob);
            this.currentAudio = new Audio(audioUrl);
            this.currentAudio.play();
            
            // Show currently playing indicator
            document.querySelectorAll('.play-btn').forEach(btn => {
                btn.innerHTML = '<i class="fas fa-play"></i>';
                btn.classList.remove('btn-success');
                btn.classList.add('btn-outline-primary');
            });
            
            const playBtn = document.querySelector(`[data-filepath="${filepath}"] .play-btn`);
            if (playBtn) {
                playBtn.innerHTML = '<i class="fas fa-pause"></i>';
                playBtn.classList.remove('btn-outline-primary');
                playBtn.classList.add('btn-success');
            }
            
            // Reset button when audio ends
            this.currentAudio.addEventListener('ended', () => {
                if (playBtn) {
                    playBtn.innerHTML = '<i class="fas fa-play"></i>';
                    playBtn.classList.remove('btn-success');
                    playBtn.classList.add('btn-outline-primary');
                }
            });
        })
        .catch(error => {
            console.error('Error playing audio:', error);
            this.showError('Failed to play audio file: ' + error.message);
        });
    }

    // Stop audio playback
    stopAudio() {
        if (this.currentAudio) {
            this.currentAudio.pause();
            this.currentAudio = null;
            this.showNotification('⏹️ Audio stopped', 'info');
        }
    }

    // Utility: Show progress indicator
    showProgress(message) {
        const progress = document.getElementById('scanProgress');
        progress.classList.remove('hidden');
        progress.querySelector('p').innerHTML = `
            <span class="spinner"></span>
            ${message}
        `;
    }

    // Utility: Hide progress indicator
    hideProgress() {
        document.getElementById('scanProgress').classList.add('hidden');
    }

    // Utility: Show notification
    showNotification(message, type = 'info') {
        // Create notification element
        const notification = document.createElement('div');
        notification.className = `notification notification-${type}`;
        notification.style.cssText = `
            position: fixed;
            top: 2rem;
            right: 2rem;
            padding: 1rem 1.5rem;
            border-radius: 8px;
            color: white;
            font-weight: 500;
            z-index: 9999;
            box-shadow: var(--shadow-large);
            max-width: 400px;
            animation: slideInRight 0.3s ease-out;
            background: ${type === 'success' ? 'var(--ep-success)' : 
                       type === 'warning' ? 'var(--ep-warning)' : 
                       type === 'danger' ? 'var(--ep-danger)' : 
                       'var(--ep-accent)'};
        `;
        
        notification.textContent = message;
        document.body.appendChild(notification);
        
        // Auto remove after 5 seconds
        setTimeout(() => {
            notification.style.animation = 'slideOutRight 0.3s ease-out';
            setTimeout(() => {
                if (notification.parentNode) {
                    notification.parentNode.removeChild(notification);
                }
            }, 300);
        }, 5000);
    }

    // Utility: Format bytes
    formatBytes(bytes) {
        if (bytes === 0) return '0 B';
        const k = 1024;
        const sizes = ['B', 'KB', 'MB', 'GB'];
        const i = Math.floor(Math.log(bytes) / Math.log(k));
        return parseFloat((bytes / Math.pow(k, i)).toFixed(1)) + ' ' + sizes[i];
    }

    // Cancel current scan
    async cancelScan() {
        try {
            const response = await fetch('/api/scan/cancel', {
                method: 'POST'
            });
            
            const result = await response.json();
            
            if (result.success) {
                this.hideProgress();
                this.showNotification('🛑 Scan cancelled', 'info');
                this.resetScanState(document.getElementById('scanBtn'), 'Scan Directory');
            }
        } catch (error) {
            console.error('Cancel scan error:', error);
            this.showNotification('❌ Failed to cancel scan', 'danger');
        }
    }

    // Update duplicate display with results from scan
    updateDuplicateDisplay(scanResult) {
        const duplicateGroups = document.getElementById('duplicateGroups');
        
        // Clear existing content
        duplicateGroups.innerHTML = '';
        
        if (!scanResult.duplicate_groups || scanResult.duplicate_groups.length === 0) {
            duplicateGroups.innerHTML = `
                <div class="no-duplicates">
                    <h3>🎉 No duplicates found!</h3>
                    <p>Your collection is clean - no duplicate files detected.</p>
                    ${scanResult.unique_files ? `<p><strong>${scanResult.unique_files}</strong> unique files ready for analysis.</p>` : ''}
                </div>
            `;
            
            // Show unique files section
            if (scanResult.unique_file_paths && scanResult.unique_file_paths.length > 0) {
                this.showUniqueFilesSection(scanResult.unique_file_paths);
            }
            return;
        }
        
        // Display duplicate groups with enhanced information
        scanResult.duplicate_groups.forEach((group, index) => {
            const groupDiv = document.createElement('div');
            groupDiv.className = 'duplicate-group';
            groupDiv.setAttribute('data-group-hash', group.hash);
            
            // Sort files by quality recommendation (best first)
            const sortedFiles = [...group.files].sort((a, b) => {
                const qualityOrder = { 'best': 0, 'good': 1, 'acceptable': 2, 'poor': 3, 'unknown': 4 };
                return (qualityOrder[a.quality_hint] || 4) - (qualityOrder[b.quality_hint] || 4);
            });
            
            groupDiv.innerHTML = `
                <div class="duplicate-header">
                    <h4>🔄 Duplicate Group ${index + 1}</h4>
                    <div class="duplicate-stats">
                        <span class="stat-item"><i class="fas fa-copy"></i> ${group.count} files</span>
                        <span class="stat-item"><i class="fas fa-weight"></i> ${group.total_size_formatted} total</span>
                        <span class="stat-item wasted-space"><i class="fas fa-exclamation-triangle"></i> ${this.formatBytes(group.total_size - Math.max(...group.files.map(f => f.filesize)))} wasted</span>
                    </div>
                </div>
                <div class="duplicate-files">
                    ${sortedFiles.map((file, fileIndex) => `
                        <div class="duplicate-file ${fileIndex === 0 ? 'recommended' : ''}" data-filepath="${file.filepath}">
                            <div class="file-header">
                                <div class="file-info">
                                    <strong class="filename">${file.filename}</strong>
                                    <div class="quality-badge quality-${file.quality_hint}">
                                        ${this.getQualityIcon(file.quality_hint)} ${file.quality_hint.toUpperCase()}
                                        ${fileIndex === 0 ? ' (RECOMMENDED)' : ''}
                                    </div>
                                </div>
                                <div class="file-actions">
                                    <button class="btn btn-sm btn-outline-primary play-btn" data-filepath="${file.filepath}" title="Play">
                                        <i class="fas fa-play"></i>
                                    </button>
                                    <button class="btn btn-sm btn-outline-danger delete-btn" data-filepath="${file.filepath}" title="Mark for deletion">
                                        <i class="fas fa-trash"></i>
                                    </button>
                                </div>
                            </div>
                            <div class="file-details">
                                <div class="detail-row">
                                    <span><i class="fas fa-file"></i> ${file.filesize_formatted}</span>
                                    <span><i class="fas fa-clock"></i> ${file.duration_formatted || 'Unknown'}</span>
                                    <span><i class="fas fa-music"></i> ${file.format.toUpperCase()}</span>
                                </div>
                                <div class="file-path" title="${file.filepath}">${file.filepath}</div>
                            </div>
                            ${file.waveform && file.waveform.length > 0 ? `
                                <div class="waveform-container">
                                    <canvas class="waveform-canvas" data-waveform='${JSON.stringify(file.waveform)}'></canvas>
                                </div>
                            ` : ''}
                        </div>
                    `).join('')}
                </div>
                <div class="group-actions">
                    <button class="btn btn-outline-warning auto-resolve-btn" data-group-hash="${group.hash}">
                        <i class="fas fa-magic"></i> Auto-resolve (Keep Best)
                    </button>
                    <button class="btn btn-outline-info compare-all-btn" data-group-hash="${group.hash}">
                        <i class="fas fa-balance-scale"></i> Compare All
                    </button>
                </div>
            `;
            
            duplicateGroups.appendChild(groupDiv);
        });
        
        // Add event listeners after all groups are added
        this.addDuplicateEventListeners();
        
        // Render waveforms
        this.renderAllWaveforms();
        
        // Show unique files section if available
        if (scanResult.unique_file_paths && scanResult.unique_file_paths.length > 0) {
            this.showUniqueFilesSection(scanResult.unique_file_paths);
        }
    }

    getQualityIcon(quality) {
        const icons = {
            'best': '🏆',
            'good': '✅',
            'acceptable': '⚠️',
            'poor': '❌',
            'unknown': '❓'
        };
        return icons[quality] || '❓';
    }

    addDuplicateEventListeners() {
        // Add event listeners to all buttons in duplicate groups
        document.querySelectorAll('.duplicate-file .play-btn').forEach(btn => {
            btn.addEventListener('click', () => {
                const filepath = btn.getAttribute('data-filepath');
                this.playAudioFile(filepath);
            });
        });

        document.querySelectorAll('.duplicate-file .delete-btn').forEach(btn => {
            btn.addEventListener('click', () => {
                const filepath = btn.getAttribute('data-filepath');
                this.markForDeletion(filepath);
            });
        });

        document.querySelectorAll('.auto-resolve-btn').forEach(btn => {
            btn.addEventListener('click', () => {
                const groupHash = btn.getAttribute('data-group-hash');
                this.autoResolveGroup(groupHash);
            });
        });

        document.querySelectorAll('.compare-all-btn').forEach(btn => {
            btn.addEventListener('click', () => {
                const groupHash = btn.getAttribute('data-group-hash');
                this.compareAllInGroup(groupHash);
            });
        });
    }

    renderAllWaveforms() {
        document.querySelectorAll('.waveform-canvas').forEach(canvas => {
            const waveformData = JSON.parse(canvas.getAttribute('data-waveform'));
            this.renderWaveform(canvas, waveformData);
        });
    }

    renderWaveform(canvas, waveformData) {
        if (!waveformData || waveformData.length === 0) return;
        
        const ctx = canvas.getContext('2d');
        const width = canvas.width = 400;
        const height = canvas.height = 60;
        
        ctx.clearRect(0, 0, width, height);
        ctx.fillStyle = '#3498db';
        
        const barWidth = width / waveformData.length;
        const centerY = height / 2;
        
        waveformData.forEach((value, index) => {
            const barHeight = Math.abs(value) * 0.8; // Scale down a bit
            const x = index * barWidth;
            const y = centerY - barHeight / 2;
            
            ctx.fillRect(x, y, barWidth - 1, barHeight);
        });
    }

    showUniqueFilesSection(uniqueFilePaths) {
        let uniqueSection = document.getElementById('uniqueFilesSection');
        if (!uniqueSection) {
            uniqueSection = document.createElement('div');
            uniqueSection.id = 'uniqueFilesSection';
            uniqueSection.className = 'unique-files-section';
            document.getElementById('duplicateGroups').appendChild(uniqueSection);
        }
        
        uniqueSection.innerHTML = `
            <div class="unique-files-header">
                <h3>📊 Unique Files (${uniqueFilePaths.length})</h3>
                <p>These files have no duplicates and can be analyzed individually:</p>
                <button class="btn btn-primary analyze-unique-btn" id="analyzeUniqueBtn">
                    <i class="fas fa-chart-line"></i> Analyze All Unique Files
                </button>
            </div>
            <div class="unique-files-list" id="uniqueFilesList">
                <!-- Unique files will be populated here after analysis -->
            </div>
        `;
        
        // Add event listener for analyze unique button
        document.getElementById('analyzeUniqueBtn').addEventListener('click', () => {
            this.analyzeUniqueFiles(uniqueFilePaths);
        });
    }

    analyzeUniqueFiles(filePaths) {
        console.log('🔍 Analyzing unique files:', filePaths.length);
        
        const analyzeBtn = document.getElementById('analyzeUniqueBtn');
        analyzeBtn.disabled = true;
        analyzeBtn.innerHTML = '<i class="fas fa-spinner fa-spin"></i> Analyzing...';
        
        fetch('/api/analyze-unique', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ file_paths: filePaths })
        })
        .then(response => response.json())
        .then(data => {
            if (data.success) {
                this.displayUniqueFileResults(data.analyzed_files);
            } else {
                this.showError('Failed to analyze unique files: ' + (data.error || 'Unknown error'));
            }
        })
        .catch(error => {
            console.error('Error analyzing unique files:', error);
            this.showError('Error analyzing unique files: ' + error.message);
        })
        .finally(() => {
            analyzeBtn.disabled = false;
            analyzeBtn.innerHTML = '<i class="fas fa-chart-line"></i> Analyze All Unique Files';
        });
    }

    displayUniqueFileResults(analyzedFiles) {
        const uniqueFilesList = document.getElementById('uniqueFilesList');
        
        uniqueFilesList.innerHTML = analyzedFiles.map(file => `
            <div class="unique-file-card" data-filepath="${file.filepath}">
                <div class="file-header">
                    <div class="file-info">
                        <strong class="filename">${file.filename}</strong>
                        <div class="quality-badge quality-${file.classification.level}">
                            ${file.classification.label}
                        </div>
                    </div>
                    <div class="file-actions">
                        <button class="btn btn-sm btn-outline-primary play-btn" data-filepath="${file.filepath}">
                            <i class="fas fa-play"></i>
                        </button>
                        <button class="btn btn-sm btn-outline-info details-btn" data-filepath="${file.filepath}">
                            <i class="fas fa-info-circle"></i>
                        </button>
                    </div>
                </div>
                <div class="file-details">
                    <div class="detail-row">
                        <span><i class="fas fa-file"></i> ${file.filesize_formatted}</span>
                        <span><i class="fas fa-clock"></i> ${file.metrics.duration_formatted}</span>
                        <span><i class="fas fa-music"></i> ${file.format.toUpperCase()}</span>
                        <span><i class="fas fa-star"></i> Score: ${file.metrics.quality_score || 'N/A'}</span>
                    </div>
                </div>
                ${file.waveform && file.waveform.length > 0 ? `
                    <div class="waveform-container">
                        <canvas class="waveform-canvas" data-waveform='${JSON.stringify(file.waveform)}'></canvas>
                    </div>
                ` : ''}
                <div class="analysis-summary">
                    <div class="folder-suggestion">
                        <strong>📁 Suggested folder:</strong> ${file.analysis.suggested_folder}
                    </div>
                    <div class="action-recommendation">
                        <strong>⚡ Action:</strong> ${file.analysis.action}
                    </div>
                </div>
            </div>
        `).join('');
        
        // Render waveforms for unique files
        this.renderAllWaveforms();
        
        // Add event listeners for unique file actions
        document.querySelectorAll('.unique-file-card .play-btn').forEach(btn => {
            btn.addEventListener('click', () => {
                const filepath = btn.getAttribute('data-filepath');
                this.playAudioFile(filepath);
            });
        });
    }

    // Auto-resolve duplicate groups
    autoResolveGroup(groupHash) {
        console.log(`🎯 Auto-resolving duplicate group: ${groupHash}`);
        
        const groupElement = document.querySelector(`[data-group-hash="${groupHash}"]`);
        if (!groupElement) return;
        
        const files = groupElement.querySelectorAll('.duplicate-file');
        const recommendedFile = groupElement.querySelector('.duplicate-file.recommended');
        
        if (!recommendedFile) {
            this.showError('No recommended file found for auto-resolution');
            return;
        }
        
        // Mark all non-recommended files for deletion
        files.forEach(fileElement => {
            if (!fileElement.classList.contains('recommended')) {
                const filepath = fileElement.getAttribute('data-filepath');
                this.markForDeletion(filepath);
                fileElement.style.opacity = '0.5';
                fileElement.querySelector('.delete-btn').innerHTML = '<i class="fas fa-check"></i> Marked';
                fileElement.querySelector('.delete-btn').disabled = true;
            }
        });
        
        // Update group actions
        const autoResolveBtn = groupElement.querySelector('.auto-resolve-btn');
        autoResolveBtn.innerHTML = '<i class="fas fa-check"></i> Resolved';
        autoResolveBtn.disabled = true;
        autoResolveBtn.classList.replace('btn-outline-warning', 'btn-success');
        
        this.showSuccess(`Auto-resolved duplicate group - keeping best quality file`);
    }

    // Compare all files in a duplicate group
    compareAllInGroup(groupHash) {
        console.log(`⚖️ Comparing all files in group: ${groupHash}`);
        
        const groupElement = document.querySelector(`[data-group-hash="${groupHash}"]`);
        if (!groupElement) return;
        
        // Show detailed comparison modal or expand the group
        const files = Array.from(groupElement.querySelectorAll('.duplicate-file'));
        
        // For now, just highlight all waveforms for comparison
        files.forEach(fileElement => {
            const waveform = fileElement.querySelector('.waveform-canvas');
            if (waveform) {
                waveform.style.border = '2px solid #ffc107';
                waveform.style.boxShadow = '0 0 10px rgba(255, 193, 7, 0.5)';
            }
        });
        
        this.showInfo('Visual comparison mode activated - compare waveforms and quality badges to choose the best file');
    }

    // Play audio file from duplicates or unique files
    playAudioFile(filepath) {
        console.log(`🎵 Playing audio file: ${filepath}`);
        
        // Stop current audio if playing
        if (this.currentAudio && !this.currentAudio.paused) {
            this.currentAudio.pause();
            this.currentAudio.currentTime = 0;
        }
        
        // Request audio file from server
        fetch('/api/audio', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ filepath: filepath })
        })
        .then(response => {
            if (!response.ok) {
                throw new Error('Failed to load audio file');
            }
            return response.blob();
        })
        .then(blob => {
            const audioUrl = URL.createObjectURL(blob);
            this.currentAudio = new Audio(audioUrl);
            this.currentAudio.play();
            
            // Show currently playing indicator
            document.querySelectorAll('.play-btn').forEach(btn => {
                btn.innerHTML = '<i class="fas fa-play"></i>';
                btn.classList.remove('btn-success');
                btn.classList.add('btn-outline-primary');
            });
            
            const playBtn = document.querySelector(`[data-filepath="${filepath}"] .play-btn`);
            if (playBtn) {
                playBtn.innerHTML = '<i class="fas fa-pause"></i>';
                playBtn.classList.remove('btn-outline-primary');
                playBtn.classList.add('btn-success');
            }
            
            // Reset button when audio ends
            this.currentAudio.addEventListener('ended', () => {
                if (playBtn) {
                    playBtn.innerHTML = '<i class="fas fa-play"></i>';
                    playBtn.classList.remove('btn-success');
                    playBtn.classList.add('btn-outline-primary');
                }
            });
        })
        .catch(error => {
            console.error('Error playing audio:', error);
            this.showError('Failed to play audio file: ' + error.message);
        });
    }

    // Utility: Show success notification
    showSuccess(message) {
        this.showNotification(message, 'success');
    }

    // Utility: Show error notification
    showError(message) {
        this.showNotification(message, 'error');
    }

    // Utility: Show info notification
    showInfo(message) {
        this.showNotification(message, 'info');
    }

    // Utility: Show notification
    showNotification(message, type = 'info') {
        const notification = document.createElement('div');
        notification.className = `alert alert-${type === 'error' ? 'danger' : type === 'success' ? 'success' : 'info'} alert-dismissible fade show position-fixed`;
        notification.style.cssText = 'top: 20px; right: 20px; z-index: 9999; max-width: 400px;';
        
        notification.innerHTML = `
            ${message}
            <button type="button" class="btn-close" data-bs-dismiss="alert"></button>
        `;
        
        document.body.appendChild(notification);
        
        // Auto-remove after 5 seconds
        setTimeout(() => {
            if (notification.parentNode) {
                notification.remove();
            }
        }, 5000);
    }
}

// Initialize dashboard when DOM is loaded
document.addEventListener('DOMContentLoaded', () => {
    window.dashboard = new BeatOrganizerDashboard();
    console.log('🔥 Elemental Publishing Beat Organizer - Artist Liberation War');
    console.log('🎵 Loading the tool that values your beats');
    console.log('💸 Ready to organize files worth more than their entire payment history');
});

// Add some CSS animations
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
`;
document.head.appendChild(style);

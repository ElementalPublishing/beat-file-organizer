#!/usr/bin/env python3
"""
Beat File Organizer - Professional Web GUI

Born from the enemy's $5.53 insulting offer. 
A modern, professional web interface for the Beat File Organizer.
Features real-time audio analysis, waveform visualization, and smart organization.

Artist Liberation War - Empowering creators through better tools.
Every tool that helps artists create independently weakens platform dependency.
"""

import os
import json
import base64
import tempfile
from pathlib import Path
from datetime import datetime
from typing import Dict, List, Optional, Any

from flask import Flask, render_template, request, jsonify, send_file
from flask_cors import CORS

# Import our core modules
from beat_organizer import BeatOrganizer, AudioFile
from audio_metrics import AudioAnalyzer, AudioMetrics, MetricsDatabase, analyze_track_issues, classify_track_by_metrics

app = Flask(__name__)
CORS(app)

# Global instances
organizer = BeatOrganizer(enable_metrics=True)
audio_analyzer = AudioAnalyzer()
metrics_db = MetricsDatabase()

# Scan progress tracking
scan_progress = {
    'scanning': False,
    'progress': 0,
    'current_file': '',
    'total_files': 0,
    'completed_files': 0,
    'error': None,
    'result': None
}

import threading

class WebGUIError(Exception):
    """Custom exception for web GUI errors"""
    pass

def format_file_size(size_bytes: float) -> str:
    """Format file size in human-readable format"""
    for unit in ['B', 'KB', 'MB', 'GB']:
        if size_bytes < 1024.0:
            return f"{size_bytes:.1f} {unit}"
        size_bytes /= 1024.0
    return f"{size_bytes:.1f} TB"

def format_duration(seconds: Optional[float]) -> str:
    """Format duration in MM:SS format"""
    if seconds is None:
        return "Unknown"
    
    minutes = int(seconds // 60)
    seconds = int(seconds % 60)
    return f"{minutes:02d}:{seconds:02d}"

def classify_quality(metrics: AudioMetrics) -> Dict[str, Any]:
    """Classify audio quality and return detailed info"""
    classification = {
        'level': 'unknown',
        'color': '#666',
        'label': 'Unknown',
        'description': 'No metrics available',
        'recommendations': []
    }
    
    if not metrics or metrics.lufs is None:
        return classification
    
    lufs = metrics.lufs
    
    # Streaming-ready classification
    if -16 <= lufs <= -14:
        classification.update({
            'level': 'streaming_ready',
            'color': '#4CAF50',
            'label': 'Streaming Ready',
            'description': f'Perfect for streaming platforms ({lufs:.1f} LUFS)',
            'recommendations': ['Upload to streaming platforms', 'Professional standard']
        })
    elif -14 < lufs <= -12:
        classification.update({
            'level': 'loud',
            'color': '#FF9800',
            'label': 'Too Loud',
            'description': f'Louder than streaming standard ({lufs:.1f} LUFS)',
            'recommendations': ['Consider reducing loudness', 'May sound distorted on some platforms']
        })
    elif lufs > -12:
        classification.update({
            'level': 'very_loud',
            'color': '#F44336',
            'label': 'Very Loud',
            'description': f'Much louder than recommended ({lufs:.1f} LUFS)',
            'recommendations': ['Reduce loudness significantly', 'Risk of listener fatigue']
        })
    elif -23 <= lufs < -16:
        classification.update({
            'level': 'quiet',
            'color': '#2196F3',
            'label': 'Quiet',
            'description': f'Quieter than streaming standard ({lufs:.1f} LUFS)',
            'recommendations': ['Consider increasing loudness', 'May need mastering']
        })
    else:  # lufs < -23
        classification.update({
            'level': 'very_quiet',
            'color': '#9C27B0',
            'label': 'Very Quiet',
            'description': f'Much quieter than recommended ({lufs:.1f} LUFS)',
            'recommendations': ['Increase loudness significantly', 'Check gain staging']
        })
    
    # Add clipping warning
    if metrics.has_clipping:
        classification['label'] += ' (CLIPPED)'
        classification['color'] = '#F44336'
        classification['recommendations'].insert(0, 'CRITICAL: Fix clipping before distribution')
    
    return classification

@app.route('/')
def dashboard():
    """Main dashboard page"""
    return render_template('dashboard.html')

@app.route('/test')
def test_page():
    """Simple test page to verify Flask is working"""
    return render_template('test.html')

@app.route('/api/scan', methods=['POST'])
def scan_directory():
    """Scan a directory for audio files"""
    global scan_progress
    
    try:
        # Check if scan is already in progress
        if scan_progress.get('scanning', False):
            return jsonify({'error': 'Scan already in progress. Please wait for current scan to complete.'}), 409
        
        data = request.get_json()
        directory = data.get('directory', '')
        
        if not directory or not os.path.exists(directory):
            return jsonify({'error': 'Invalid directory path'}), 400
        
        print(f"🔍 Scanning directory: {directory}")
        
        # Convert directory string to Path object
        directory_path = Path(directory)
        
        # Initialize scan progress
        scan_progress.update({
            'scanning': True,
            'progress': 0,
            'current_file': 'Starting scan...',
            'total_files': 0,
            'completed_files': 0,
            'error': None,
            'result': None
        })
        
        # Start background scan
        def background_scan():
            global scan_progress
            try:
                print(f"📂 Starting comprehensive scan: {directory_path}")
                
                # PHASE 1: File Discovery
                scan_progress['current_file'] = '🔍 Phase 1: Discovering audio files...'
                scan_progress['progress'] = 5
                scan_progress['completed_files'] = 0
                
                print("🔍 Phase 1: Scanning for audio files...")
                discovered_files = organizer.scan_directory(directory_path)
                file_count = len(discovered_files)
                audio_files = discovered_files
                
                print(f"✅ Phase 1 complete: Found {file_count} audio files")
                scan_progress['total_files'] = file_count
                scan_progress['current_file'] = f'✅ Discovery complete! Found {file_count} files'
                scan_progress['progress'] = 15
                
                if not scan_progress['scanning'] or file_count == 0:
                    print("🛑 Scan cancelled or no files found")
                    return
                
                # PHASE 2: Fingerprint Generation (for duplicate detection)
                print("🔑 Phase 2: Generating audio fingerprints...")
                scan_progress['current_file'] = '🔑 Phase 2: Generating audio fingerprints for duplicate detection...'
                scan_progress['completed_files'] = 0
                scan_progress['progress'] = 20
                
                def fingerprint_progress(completed, total, current_file):
                    if not scan_progress['scanning']:
                        return
                    scan_progress['completed_files'] = completed
                    scan_progress['current_file'] = f'🔑 Fingerprinting: {current_file}'
                    scan_progress['progress'] = 20 + int((completed / total) * 25)  # 20-45%
                
                fingerprints = organizer.generate_fingerprints_bulk(audio_files, fingerprint_progress)
                print(f"✅ Phase 2 complete: Generated {len(fingerprints)} fingerprints")
                
                if not scan_progress['scanning']:
                    print("🛑 Scan cancelled during fingerprinting")
                    return
                
                # PHASE 3: Duplicate Detection
                print("🔍 Phase 3: Detecting duplicates...")
                scan_progress['current_file'] = '🔍 Phase 3: Analyzing fingerprints for duplicates...'
                scan_progress['completed_files'] = 0
                scan_progress['progress'] = 50
                
                # Find duplicates using fingerprints
                duplicates = organizer._find_duplicates_from_files(audio_files, fingerprints)
                duplicate_count = sum(len(group) - 1 for group in duplicates.values())
                
                print(f"✅ Phase 3 complete: Found {len(duplicates)} groups with {duplicate_count} duplicates")
                scan_progress['current_file'] = f'✅ Duplicate detection complete! Found {len(duplicates)} groups ({duplicate_count} duplicates)'
                scan_progress['progress'] = 65
                
                if not scan_progress['scanning']:
                    print("🛑 Scan cancelled during duplicate detection")
                    return
                
                # PHASE 4: Full Audio Analysis (only on unique files to save time)
                print("📊 Phase 4: Full audio analysis on unique files...")
                scan_progress['current_file'] = '📊 Phase 4: Full audio analysis (LUFS, peaks, quality)...'
                scan_progress['completed_files'] = 0
                
                # Get list of unique files (one from each duplicate group + all non-duplicates)
                unique_files = []
                duplicate_representatives = set()
                
                # Add one representative from each duplicate group
                for group_hash, files in duplicates.items():
                    if files:
                        unique_files.append(files[0])  # Take first file as representative
                        duplicate_representatives.add(str(files[0].filepath))
                
                # Add all non-duplicate files
                for audio_file in audio_files:
                    file_path_str = str(audio_file.filepath)
                    is_duplicate = any(file_path_str == str(f.filepath) for group in duplicates.values() for f in group)
                    if not is_duplicate:
                        unique_files.append(audio_file)
                
                # Analyze unique files only
                analyzed_files = []
                total_to_analyze = len(unique_files)
                
                for i, audio_file in enumerate(unique_files):
                    if not scan_progress['scanning']:
                        print("🛑 Scan cancelled during analysis phase")
                        return
                    
                    scan_progress['current_file'] = f'� Analyzing: {audio_file.filename}'
                    scan_progress['completed_files'] = i
                    scan_progress['progress'] = 65 + int((i / total_to_analyze) * 25)  # 65-90%
                    
                    try:
                        # Full analysis only for unique files
                        analyzed_file = organizer._analyze_file(audio_file.filepath)
                        if analyzed_file:
                            analyzed_files.append(analyzed_file)
                    except Exception as e:
                        print(f"Error analyzing {audio_file.filename}: {e}")
                        analyzed_files.append(audio_file)
                
                print(f"✅ Phase 4 complete: Analyzed {len(analyzed_files)} unique files")
                scan_progress['current_file'] = f'✅ Analysis complete! Processed {len(analyzed_files)} unique files'
                scan_progress['progress'] = 95
                
                # PHASE 5: Prepare Results
                print("📋 Phase 5: Preparing results...")
                scan_progress['current_file'] = '📋 Phase 5: Preparing scan results...'
                scan_progress['progress'] = 95
                
                # Step 4: Convert to serializable format with duplicate info
                files_data = []
                duplicate_map = {}
                
                # Create duplicate mapping for quick lookup
                for group_hash, files in duplicates.items():
                    for file in files:
                        duplicate_map[str(file.filepath)] = {
                            'is_duplicate': True,
                            'group_hash': group_hash,
                            'group_size': len(files),
                            'duplicate_count': len(files) - 1
                        }
                
                for i, audio_file in enumerate(analyzed_files):
                    if not scan_progress['scanning']:  # Check if cancelled
                        break
                    
                    scan_progress['completed_files'] = len(analyzed_files)
                    scan_progress['current_file'] = f'Processing file data: {audio_file.filename}'
                    scan_progress['progress'] = 85 + int((i / len(analyzed_files)) * 10)  # 85-95%
                    
                    file_path_str = str(audio_file.filepath)
                    duplicate_info = duplicate_map.get(file_path_str, {
                        'is_duplicate': False,
                        'group_hash': None,
                        'group_size': 1,
                        'duplicate_count': 0
                    })
                    
                    file_data = {
                        'filepath': file_path_str,
                        'filename': audio_file.filename,
                        'filesize': audio_file.filesize,
                        'filesize_formatted': format_file_size(audio_file.filesize),
                        'format': audio_file.format,
                        'file_hash': audio_file.file_hash,
                        'created_date': audio_file.created_date.isoformat() if audio_file.created_date else None,
                        'modified_date': audio_file.modified_date.isoformat() if audio_file.modified_date else None,
                        'estimated_duration': audio_file.estimated_duration,
                        'duration_formatted': format_duration(audio_file.estimated_duration),
                        'duplicate_info': duplicate_info
                    }
                    files_data.append(file_data)
                
                scan_progress['current_file'] = 'Finalizing results... Almost ready for your liberation army!'
                scan_progress['progress'] = 95
                
                # Calculate collection statistics
                total_size = sum(f['filesize'] for f in files_data)
                duplicate_files = [f for f in files_data if f['duplicate_info']['is_duplicate']]
                wasted_space = sum(f['filesize'] for f in duplicate_files)
                
                # Complete the scan
                result = {
                    'success': True,
                    'directory': directory,
                    'total_files': len(files_data),
                    'total_size': total_size,
                    'total_size_formatted': format_file_size(total_size),
                    'duplicate_groups': len(duplicates),
                    'duplicate_files': len(duplicate_files),
                    'wasted_space': wasted_space,
                    'wasted_space_formatted': format_file_size(wasted_space),
                    'files': files_data,
                    'scan_time': datetime.now().isoformat()
                }
                
                scan_progress.update({
                    'scanning': False,
                    'progress': 100,
                    'current_file': f'Scan complete! Found {len(files_data)} files, {len(duplicates)} duplicate groups',
                    'result': result
                })
                
                print(f"✅ Complete scan finished: {len(files_data)} files, {len(duplicates)} duplicate groups")
                
            except Exception as e:
                print(f"❌ Background scan error: {str(e)}")
                scan_progress.update({
                    'scanning': False,
                    'error': str(e),
                    'current_file': 'Scan failed'
                })
        
        # Start the background scan thread
        scan_thread = threading.Thread(target=background_scan, daemon=True)
        scan_thread.start()
        
        # Return immediate response
        return jsonify({
            'success': True,
            'message': 'Scan started',
            'directory': directory
        })
        
    except Exception as e:
        print(f"❌ Scan error: {str(e)}")
        return jsonify({'error': f'Scan failed: {str(e)}'}), 500

@app.route('/api/scan/progress', methods=['GET'])
def get_scan_progress():
    """Get current scan progress"""
    return jsonify(scan_progress)

@app.route('/api/scan/cancel', methods=['POST'])
def cancel_scan():
    """Cancel current scan"""
    global scan_progress
    print("🛑 Scan cancellation requested")
    scan_progress.update({
        'scanning': False,
        'progress': 0,
        'current_file': 'Scan cancelled by user',
        'error': 'Scan was cancelled',
        'result': None
    })
    return jsonify({'success': True, 'message': 'Scan cancelled'})

@app.route('/api/analyze', methods=['POST'])
def analyze_file():
    """Analyze a single audio file with full metrics"""
    try:
        data = request.get_json()
        filepath = data.get('filepath', '')
        
        print(f"🔍 Analyze request received for: {repr(filepath)}")
        
        if not filepath:
            print("❌ No filepath provided in request")
            return jsonify({'error': 'No file path provided'}), 400
            
        # Convert string to Path object
        filepath_obj = Path(filepath)
        
        if not filepath_obj.exists():
            print(f"❌ File does not exist: {filepath}")
            return jsonify({'error': f'File not found: {filepath}'}), 400
        
        print(f"🎵 Analyzing file: {filepath_obj.name}")
        
        # Get detailed audio metrics using Path object
        metrics = audio_analyzer.analyze_file(filepath_obj)
        
        if not metrics:
            print(f"❌ Audio analyzer returned no metrics for: {filepath}")
            return jsonify({'error': 'Failed to analyze audio file - no metrics returned'}), 500
        
        # Classify quality
        quality = classify_quality(metrics)
        
        # Prepare response
        result = {
            'success': True,
            'filepath': filepath,
            'filename': metrics.filename,
            'metrics': {
                'file_size': metrics.file_size,
                'file_size_formatted': format_file_size(metrics.file_size),
                'format': metrics.format,
                'bit_depth': metrics.bit_depth,
                'sample_rate': metrics.sample_rate,
                'duration': metrics.duration,
                'duration_formatted': format_duration(metrics.duration),
                'lufs': metrics.lufs,
                'true_peak': metrics.true_peak,
                'rms_energy': metrics.rms_energy,
                'dynamic_range': metrics.dynamic_range,
                'bpm': metrics.bpm,
                'key': metrics.key,
                'has_clipping': metrics.has_clipping,
                'quality_score': metrics.quality_score,
                'classification': metrics.classification
            },
            'quality': quality,
            'analysis_time': datetime.now().isoformat()
        }
        
        print(f"✅ Analysis complete: {quality['label']}")
        return jsonify(result)
        
    except Exception as e:
        print(f"❌ Analysis error: {str(e)}")
        print(f"❌ Error type: {type(e).__name__}")
        print(f"❌ Received filepath: {repr(filepath)}")
        return jsonify({'error': f'Analysis failed: {str(e)}'}), 500

@app.route('/api/waveform', methods=['POST'])
def generate_waveform():
    """Generate waveform visualization for an audio file"""
    try:
        data = request.get_json()
        filepath = data.get('filepath', '')
        width = data.get('width', 800)
        height = data.get('height', 200)
        
        if not filepath:
            return jsonify({'error': 'No file path provided'}), 400
            
        # Convert string to Path object
        filepath_obj = Path(filepath)
        
        if not filepath_obj.exists():
            return jsonify({'error': 'Invalid file path'}), 400
        
        print(f"📊 Generating waveform: {filepath_obj.name}")
        
        # Check if waveform generation is available
        if not hasattr(audio_analyzer, 'generate_waveform'):
            return jsonify({'error': 'Waveform generation not available yet'}), 501
        
        # Generate waveform data using audio analyzer
        waveform_data = audio_analyzer.generate_waveform(filepath_obj, width=width, height=height)
        
        if not waveform_data:
            return jsonify({'error': 'Failed to generate waveform'}), 500
        
        result = {
            'success': True,
            'filepath': filepath,
            'waveform': waveform_data,
            'width': width,
            'height': height,
            'generation_time': datetime.now().isoformat()
        }
        
        print("✅ Waveform generated successfully")
        return jsonify(result)
        
    except Exception as e:
        print(f"❌ Waveform error: {str(e)}")
        return jsonify({'error': f'Waveform generation failed: {str(e)}'}), 500

@app.route('/api/duplicates', methods=['POST'])
def find_duplicates():
    """Find duplicate files using advanced audio fingerprinting"""
    try:
        data = request.get_json()
        directory = data.get('directory', '')
        
        if not directory or not os.path.exists(directory):
            return jsonify({'error': 'Invalid directory path'}), 400
        
        print(f"🔍 Finding duplicates in: {directory}")
        
        # First, scan directory for audio files
        directory_path = Path(directory)
        audio_files = []
        
        for ext in ['.wav', '.mp3', '.flac', '.aif', '.aiff', '.m4a', '.ogg']:
            audio_files.extend(directory_path.rglob(f'*{ext}'))
            audio_files.extend(directory_path.rglob(f'*{ext.upper()}'))
        
        if not audio_files:
            return jsonify({
                'success': True,
                'directory': directory,
                'duplicate_groups': [],
                'total_groups': 0,
                'total_duplicates': 0,
                'wasted_space': 0,
                'wasted_space_formatted': '0 B',
                'message': 'No audio files found in directory'
            })
        
        print(f"📁 Found {len(audio_files)} audio files to analyze")
        
        # Use the comprehensive duplicate analysis workflow
        analysis_result = audio_analyzer.comprehensive_duplicate_analysis(
            audio_files,
            progress_callback=lambda progress, total, current: print(f"Progress: {progress}% - {current}")
        )
        
        if not analysis_result.get('success'):
            return jsonify({'error': 'Duplicate analysis failed'}), 500
        
        # Convert the analysis result to the format expected by the frontend
        duplicate_groups = []
        for group_key, group_data in analysis_result.get('duplicate_groups_data', {}).items():
            files_in_group = group_data.get('files', [])
            
            if len(files_in_group) > 1:  # Only actual duplicates
                group = {
                    'hash': group_data.get('group_id', group_key),
                    'count': len(files_in_group),
                    'total_size': sum(f.get('filesize', 0) for f in files_in_group),
                    'files': []
                }
                
                # Add quality comparison data if available
                quality_data = analysis_result.get('quality_comparisons', {}).get(group_key, {})
                
                for file_info in files_in_group:
                    file_data = {
                        'filepath': file_info.get('filepath', ''),
                        'filename': file_info.get('filename', ''),
                        'filesize': file_info.get('filesize', 0),
                        'filesize_formatted': file_info.get('filesize_formatted', ''),
                        'duration': file_info.get('duration'),
                        'duration_formatted': file_info.get('duration_formatted', ''),
                        'format': file_info.get('format', ''),
                        'waveform': file_info.get('waveform', []),
                        'quality_hint': quality_data.get(file_info.get('filepath', ''), {}).get('quality_recommendation', 'unknown')
                    }
                    group['files'].append(file_data)
                
                group['total_size_formatted'] = format_file_size(group['total_size'])
                duplicate_groups.append(group)
        
        # Sort by total size (largest first)
        duplicate_groups.sort(key=lambda x: x['total_size'], reverse=True)
        
        # Calculate wasted space (total size minus size of largest file in each group)
        wasted_space = 0
        for group in duplicate_groups:
            if group['files']:
                largest_file_size = max(f['filesize'] for f in group['files'])
                wasted_space += group['total_size'] - largest_file_size
        
        result = {
            'success': True,
            'directory': directory,
            'duplicate_groups': duplicate_groups,
            'total_groups': len(duplicate_groups),
            'total_duplicates': analysis_result.get('total_duplicates', 0),
            'total_files_scanned': analysis_result.get('total_files', 0),
            'unique_files': analysis_result.get('unique_files', 0),
            'unique_file_paths': analysis_result.get('unique_file_paths', []),
            'wasted_space': wasted_space,
            'wasted_space_formatted': format_file_size(wasted_space),
            'fingerprint_success_rate': analysis_result.get('fingerprint_success_rate', 0),
            'workflow_summary': analysis_result.get('workflow_summary', {}),
            'scan_time': datetime.now().isoformat()
        }
        
        print(f"✅ Advanced duplicate analysis complete:")
        print(f"   📁 {result['total_files_scanned']} files analyzed")
        print(f"   🔄 {result['total_groups']} duplicate groups found")
        print(f"   📊 {result['unique_files']} unique files identified")
        print(f"   💾 {result['wasted_space_formatted']} wasted space")
        
        return jsonify(result)
        
    except Exception as e:
        print(f"❌ Advanced duplicate search error: {str(e)}")
        import traceback
        traceback.print_exc()
        return jsonify({'error': f'Duplicate analysis failed: {str(e)}'}), 500

@app.route('/api/collection-stats', methods=['POST'])
def collection_statistics():
    """Get comprehensive statistics for an audio collection"""
    try:
        data = request.get_json()
        directory = data.get('directory', '')
        
        if not directory or not os.path.exists(directory):
            return jsonify({'error': 'Invalid directory path'}), 400
        
        print(f"📊 Analyzing collection: {directory}")
        
        # Get basic stats from organizer
        stats = organizer.get_collection_stats(directory)
        
        # Get detailed metrics stats from database
        metrics_stats = metrics_db.get_collection_stats(directory)
        
        # Combine and format results
        result = {
            'success': True,
            'directory': directory,
            'basic_stats': {
                'total_files': stats.get('total_files', 0),
                'total_size': stats.get('total_size', 0),
                'total_size_formatted': format_file_size(stats.get('total_size', 0)),
                'formats': stats.get('formats', {}),
                'oldest_file': stats.get('oldest_file'),
                'newest_file': stats.get('newest_file')
            },
            'quality_stats': metrics_stats.get('quality_distribution', {}),
            'loudness_stats': metrics_stats.get('loudness_stats', {}),
            'recommendations': [],
            'analysis_time': datetime.now().isoformat()
        }
        
        # Generate recommendations based on stats
        if metrics_stats.get('quality_distribution', {}).get('CLIPPED', 0) > 0:
            result['recommendations'].append({
                'type': 'critical',
                'message': f"{metrics_stats['quality_distribution']['CLIPPED']} files have clipping - fix before distribution"
            })
        
        if metrics_stats.get('quality_distribution', {}).get('TOO_LOUD', 0) > stats.get('total_files', 1) * 0.5:
            result['recommendations'].append({
                'type': 'warning',
                'message': "Over 50% of files are louder than streaming standards"
            })
        
        if stats.get('total_files', 0) == 0:
            result['recommendations'].append({
                'type': 'info',
                'message': "No audio files found in this directory"
            })
        
        print(f"✅ Collection stats complete: {result['basic_stats']['total_files']} files analyzed")
        return jsonify(result)
        
    except Exception as e:
        print(f"❌ Collection stats error: {str(e)}")
        return jsonify({'error': f'Collection analysis failed: {str(e)}'}), 500

@app.route('/api/health', methods=['GET'])
def health_check():
    """API health check endpoint"""
    try:
        # Check if core dependencies are working
        ffmpeg_available = audio_analyzer.check_ffmpeg()
        
        return jsonify({
            'success': True,
            'status': 'healthy',
            'version': '1.0.0',
            'dependencies': {
                'ffmpeg': ffmpeg_available,
                'audio_metrics': True,
                'database': metrics_db.is_healthy()
            },
            'timestamp': datetime.now().isoformat()
        })
    except Exception as e:
        return jsonify({
            'success': False,
            'status': 'unhealthy',
            'error': str(e),
            'timestamp': datetime.now().isoformat()
        }), 500

@app.errorhandler(404)
def not_found(error):
    """Handle 404 errors"""
    return jsonify({'error': 'Endpoint not found'}), 404

@app.errorhandler(500)
def internal_error(error):
    """Handle 500 errors"""
    return jsonify({'error': 'Internal server error'}), 500

@app.route('/api/browse', methods=['GET'])
def browse_directory():
    """Open a directory browser dialog"""
    try:
        import tkinter as tk
        from tkinter import filedialog
        
        # Create a root window and hide it
        root = tk.Tk()
        root.withdraw()
        root.attributes('-topmost', True)
        
        # Open directory dialog
        directory = filedialog.askdirectory(
            title="Select your beats directory",
            mustexist=True
        )
        
        root.destroy()
        
        if directory:
            return jsonify({
                'success': True,
                'directory': directory
            })
        else:
            return jsonify({
                'success': False,
                'error': 'No directory selected'
            })
            
    except ImportError:
        return jsonify({
            'success': False,
            'error': 'Directory browser not available - tkinter not installed'
        })
    except Exception as e:
        return jsonify({
            'success': False,
            'error': f'Browse error: {str(e)}'
        })

@app.route('/api/audio', methods=['POST'])
def serve_audio():
    """Serve audio file for playback"""
    try:
        data = request.get_json()
        filepath = data.get('filepath', '')
        
        if not filepath:
            return jsonify({'error': 'No file path provided'}), 400
            
        # Convert string to Path object
        filepath_obj = Path(filepath)
        
        if not filepath_obj.exists():
            return jsonify({'error': 'Audio file not found'}), 404
        
        # Check if it's an audio file
        audio_extensions = {'.mp3', '.wav', '.flac', '.m4a', '.aac', '.ogg', '.wma'}
        if filepath_obj.suffix.lower() not in audio_extensions:
            return jsonify({'error': 'Not an audio file'}), 400
        
        print(f"🎵 Serving audio: {filepath_obj.name}")
        
        # Serve the audio file
        return send_file(
            str(filepath_obj),
            as_attachment=False,
            mimetype='audio/mpeg'  # Default to mp3, browser will handle others
        )
        
    except Exception as e:
        print(f"❌ Audio serving error: {str(e)}")
        return jsonify({'error': f'Failed to serve audio: {str(e)}'}), 500

@app.route('/api/analyze-unique', methods=['POST'])
def analyze_unique_files():
    """Analyze a list of unique files (not duplicates) individually"""
    try:
        data = request.get_json()
        file_paths = data.get('file_paths', [])
        
        if not file_paths:
            return jsonify({'error': 'No file paths provided'}), 400
        
        print(f"🔍 Analyzing {len(file_paths)} unique files...")
        
        results = []
        for i, file_path in enumerate(file_paths):
            try:
                file_path_obj = Path(file_path)
                if not file_path_obj.exists():
                    print(f"⚠️ File not found: {file_path}")
                    continue
                
                # Perform full analysis on this unique file
                metrics = audio_analyzer.analyze_file(file_path_obj)
                
                # Generate waveform for visualization
                waveform = audio_analyzer.generate_waveform(file_path_obj, width=400, height=100)
                
                # Classify the track
                classification = classify_quality(metrics)
                
                # Get detailed analysis
                issues_analysis = analyze_track_issues(metrics)
                track_classification = classify_track_by_metrics(metrics)
                
                file_result = {
                    'filepath': file_path,
                    'filename': file_path_obj.name,
                    'filesize': file_path_obj.stat().st_size,
                    'filesize_formatted': format_file_size(file_path_obj.stat().st_size),
                    'format': file_path_obj.suffix.lower(),
                    'waveform': waveform,
                    'metrics': {
                        'duration': metrics.duration,
                        'duration_formatted': format_duration(metrics.duration),
                        'sample_rate': metrics.sample_rate,
                        'bit_depth': metrics.bit_depth,
                        'lufs': metrics.lufs,
                        'true_peak': metrics.true_peak,
                        'has_clipping': metrics.has_clipping,
                        'quality_score': metrics.quality_score
                    },
                    'classification': classification,
                    'analysis': {
                        'issues': issues_analysis.get('issues', []),
                        'recommendations': issues_analysis.get('recommendations', []),
                        'overall_score': issues_analysis.get('overall_score', 0),
                        'suggested_folder': track_classification.get('suggested_folder', ''),
                        'action': track_classification.get('action', '')
                    },
                    'analysis_date': datetime.now().isoformat()
                }
                
                results.append(file_result)
                
                if (i + 1) % 10 == 0:
                    print(f"  Analyzed {i + 1}/{len(file_paths)} files...")
                    
            except Exception as e:
                print(f"⚠️ Error analyzing {file_path}: {e}")
                continue
        
        print(f"✅ Analysis complete: {len(results)}/{len(file_paths)} files analyzed successfully")
        
        return jsonify({
            'success': True,
            'analyzed_files': results,
            'total_requested': len(file_paths),
            'total_analyzed': len(results),
            'analysis_time': datetime.now().isoformat()
        })
        
    except Exception as e:
        print(f"❌ Unique file analysis error: {str(e)}")
        import traceback
        traceback.print_exc()
        return jsonify({'error': f'Unique file analysis failed: {str(e)}'}), 500

def main():
    """Run the web GUI"""
    print("🎵 Beat File Organizer - Web GUI")
    print("🔥 Artist Liberation War - Empowering Creators")
    print("=" * 50)
    
    # Check dependencies
    if not audio_analyzer.check_ffmpeg():
        print("⚠️ WARNING: FFmpeg not found - some features may not work")
    
    print("🚀 Starting web server...")
    print("📱 Dashboard: http://localhost:5000")
    print("🛠️ API Health: http://localhost:5000/api/health")
    print("\n💡 Press Ctrl+C to stop\n")
    
    try:
        app.run(host='0.0.0.0', port=5000, debug=True)
    except KeyboardInterrupt:
        print("\n👋 Shutting down... Keep creating!")

if __name__ == '__main__':
    main()

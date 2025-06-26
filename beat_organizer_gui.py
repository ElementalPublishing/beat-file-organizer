#!/usr/bin/env python3
"""
Beat File Organizer - Web GUI Interface

A visual dashboard for organizing music production files.
Listen, compare, and organize with confidence.
"""

from flask import Flask, render_template, request, jsonify, send_file
import os
import json
import time
import threading
from pathlib import Path
from urllib.parse import unquote
from beat_organizer import BeatOrganizer

# Try to import numpy and librosa for waveform generation
NUMPY_AVAILABLE = False
LIBROSA_AVAILABLE = False

try:
    import numpy as np
    NUMPY_AVAILABLE = True
    print("✓ NumPy available for waveform generation")
except ImportError:
    print("⚠ NumPy not available - using basic math fallback")

try:
    import librosa
    LIBROSA_AVAILABLE = True
    print("✓ Librosa available for real audio analysis")
except ImportError:
    print("⚠ Librosa not available - using stylized waveforms")

app = Flask(__name__)
organizer = BeatOrganizer()

# Global state for current scan
current_scan_data = {
    'audio_files': [],
    'duplicates': {},
    'version_families': {},
    'scan_path': None
}

# Progress tracking
scan_progress = {
    'current': 0,
    'total': 0,
    'status': 'idle',
    'message': ''
}

@app.route('/')
def index():
    """Main dashboard page"""
    return render_template('dashboard.html')

@app.route('/api/progress')
def get_progress():
    """Get current scan progress"""
    return jsonify(scan_progress)

@app.route('/api/scan', methods=['POST'])
def scan_directory():
    """Scan a directory and return file analysis"""
    data = request.get_json()
    path = Path(data.get('path', ''))
    
    if not path.exists() or not path.is_dir():
        return jsonify({'error': 'Invalid directory path'}), 400
    
    # Start scan in background thread
    def scan_in_background():
        global scan_progress, current_scan_data
        try:
            scan_progress.update({
                'current': 0,
                'total': 100,
                'status': 'scanning',
                'message': 'Scanning directory...'
            })
            
            # Get all files first for progress tracking
            all_files = list(path.glob("**/*"))
            audio_extensions = {'.wav', '.mp3', '.flac', '.aif', '.aiff', '.m4a', '.ogg'}
            
            scan_progress['total'] = len(all_files)
            scan_progress['message'] = f'Found {len(all_files)} files, analyzing...'
            
            audio_files = []
            for i, filepath in enumerate(all_files):
                if filepath.is_file() and filepath.suffix.lower() in audio_extensions:
                    try:
                        audio_file = organizer._analyze_file(filepath, skip_hashing=False)
                        if audio_file:
                            audio_files.append(audio_file)
                    except:
                        pass  # Skip files that can't be analyzed
                
                scan_progress['current'] = i + 1
                if i % 10 == 0:  # Update message less frequently
                    scan_progress['message'] = f'Found {len(audio_files)} audio files...'
                time.sleep(0.001)  # Small delay for UI updates
            
            scan_progress['message'] = 'Finding duplicates and versions...'
            
            # Find duplicates and versions
            duplicates = organizer.find_duplicates(audio_files)
            version_families = organizer.find_version_families(audio_files)
            
            # Store in global state
            current_scan_data.update({
                'audio_files': [
                    {
                        'filepath': str(f.filepath),
                        'filename': f.filename,
                        'filesize': f.filesize,
                        'format': f.format,
                        'file_hash': f.file_hash,
                        'estimated_duration': f.estimated_duration
                    } for f in audio_files
                ],
                'duplicates': {k: [str(f.filepath) for f in v] for k, v in duplicates.items()},
                'version_families': {k: [str(f.filepath) for f in v] for k, v in version_families.items()},
                'scan_path': str(path)
            })
            
            scan_progress.update({
                'current': scan_progress['total'],
                'status': 'complete',
                'message': f'Complete! Found {len(audio_files)} audio files',
                'results': {
                    'total_files': len(audio_files),
                    'duplicates_count': len(duplicates),
                    'version_families_count': len(version_families)
                }
            })
            
        except Exception as e:
            scan_progress.update({
                'status': 'error',
                'message': f'Error: {str(e)}'
            })
    
    # Start background thread
    thread = threading.Thread(target=scan_in_background)
    thread.daemon = True
    thread.start()
    
    return jsonify({
        'success': True,
        'message': 'Scan started',
        'progress_endpoint': '/api/progress'
    })

@app.route('/api/results')
def get_results():
    """Get scan results after completion"""
    if scan_progress['status'] == 'complete':
        return jsonify({
            'success': True,
            'data': current_scan_data,
            **scan_progress.get('results', {})
        })
    else:
        return jsonify({'success': False, 'message': 'Scan not complete'})

@app.route('/api/audio/<path:filepath>')
def serve_audio(filepath):
    """Serve audio files for preview"""
    try:
        # Decode the filepath properly
        from urllib.parse import unquote
        decoded_path = unquote(filepath)
        file_path = Path(decoded_path)
        
        if not file_path.exists():
            return jsonify({'error': 'File not found'}), 404
            
        return send_file(str(file_path))
    except Exception as e:
        return jsonify({'error': str(e)}), 404

@app.route('/api/compare', methods=['POST'])
def compare_files():
    """Get comparison data for multiple files"""
    data = request.get_json()
    filepaths = data.get('files', [])
    
    comparison_data = []
    for filepath in filepaths:
        try:
            path = Path(filepath)
            stat = path.stat()
            comparison_data.append({
                'filepath': filepath,
                'filename': path.name,
                'filesize': stat.st_size,
                'modified': stat.st_mtime,
                'duration_estimate': organizer._estimate_duration(stat.st_size, path.suffix)
            })
        except Exception as e:
            comparison_data.append({
                'filepath': filepath,
                'error': str(e)
            })
    
    return jsonify(comparison_data)

@app.route('/api/organize', methods=['POST'])
def organize_files():
    """Execute file organization based on user decisions"""
    data = request.get_json()
    decisions = data.get('decisions', {})
    output_dir = Path(data.get('output_dir', ''))
    dry_run = data.get('dry_run', True)
    
    try:
        # TODO: Implement organization based on user decisions
        # For now, just return success
        return jsonify({
            'success': True,
            'message': f"Organization {'planned' if dry_run else 'completed'}"
        })
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/waveform/<path:filepath>')
def get_waveform(filepath):
    """Generate waveform data for an audio file"""
    try:
        decoded_path = unquote(filepath)
        file_path = Path(decoded_path)
        
        print(f"🔍 Waveform request for: {decoded_path}")
        print(f"🔍 File exists: {file_path.exists()}")
        
        if not file_path.exists():
            return jsonify({'error': 'File not found'}), 404
        
        if not LIBROSA_AVAILABLE:
            # Try to generate a simple waveform without librosa
            try:
                waveform_data = generate_simple_waveform(file_path)
                if waveform_data:
                    return jsonify({
                        'success': True,
                        'waveform': waveform_data['waveform'],
                        'duration': waveform_data['duration'],
                        'sample_rate': waveform_data['sample_rate'],
                        'mock': False,
                        'method': 'simple_audio_analysis'
                    })
                else:
                    raise Exception("Could not read audio file")
            except Exception as e:
                return jsonify({
                    'success': False,
                    'error': f'Simple audio analysis failed: {str(e)}',
                    'mock': True
                })
        
        try:
            # Load audio file and generate real waveform
            y, sr = librosa.load(str(file_path), duration=30, sr=None)  # Load up to 30 seconds
            
            # Downsample for visualization (we want ~400-800 points for the canvas)
            target_length = 400
            if len(y) > target_length:
                # Take every nth sample to get target length
                step = len(y) // target_length
                waveform = y[::step][:target_length]
            else:
                waveform = y
            
            # Normalize to -1 to 1 range
            if np.max(np.abs(waveform)) > 0:
                waveform = waveform / np.max(np.abs(waveform))
            
            return jsonify({
                'success': True,
                'waveform': waveform.tolist(),
                'duration': len(y) / sr,
                'sample_rate': sr,
                'mock': False
            })
            
        except Exception as e:
            # Return error if audio loading fails - no more fake waveforms!
            return jsonify({
                'success': False,
                'error': f'Could not load audio: {str(e)}',
                'mock': True
            })
            
    except Exception as e:
        return jsonify({'error': str(e)}), 500

def generate_mock_waveform(length=400):
    """Generate a mock waveform for when real audio analysis isn't available"""
    if not NUMPY_AVAILABLE:
        # Fallback to basic Python math when numpy isn't available
        import math
        import random
        waveform = []
        for i in range(length):
            x = i * 4 * math.pi / length
            # Create a more realistic looking waveform pattern
            value = (math.sin(x) * 0.3 + 
                    math.sin(x * 2.1) * 0.2 + 
                    math.sin(x * 0.5) * 0.4 + 
                    random.uniform(-0.1, 0.1))
            
            # Apply some envelope to make it more natural
            envelope = math.exp(-x / 8) * 0.8 + 0.2
            value *= envelope
            waveform.append(value)
        
        # Normalize
        max_val = max(abs(v) for v in waveform)
        if max_val > 0:
            waveform = [v / max_val for v in waveform]
        
        return waveform
    else:
        # Use numpy for better performance
        x = np.linspace(0, 4 * np.pi, length)
        # Create a more realistic looking waveform pattern
        waveform = (np.sin(x) * 0.3 + 
                   np.sin(x * 2.1) * 0.2 + 
                   np.sin(x * 0.5) * 0.4 + 
                   np.random.normal(0, 0.1, length))
        
        # Apply some envelope to make it more natural
        envelope = np.exp(-x / 8) * 0.8 + 0.2
        waveform *= envelope
        
        # Normalize
        if np.max(np.abs(waveform)) > 0:
            waveform = waveform / np.max(np.abs(waveform))
        
        return waveform.tolist()

def generate_simple_waveform(file_path):
    """Generate a real waveform from audio file using FFmpeg"""
    import subprocess
    import tempfile
    import struct
    
    try:
        # First, try FFmpeg approach for real audio analysis
        with tempfile.NamedTemporaryFile(suffix='.raw', delete=False) as temp_file:
            temp_path = temp_file.name
        
        try:
            # Use FFmpeg to extract raw audio data
            ffmpeg_cmd = [
                'ffmpeg', '-i', str(file_path),
                '-f', 's16le',  # 16-bit signed little-endian
                '-ac', '1',     # Mono
                '-ar', '44100', # 44.1kHz sample rate
                '-t', '30',     # Max 30 seconds
                '-y',           # Overwrite output
                temp_path
            ]
            
            print(f"🎵 Running FFmpeg: {' '.join(ffmpeg_cmd)}")
            result = subprocess.run(ffmpeg_cmd, 
                                  capture_output=True, 
                                  text=True, 
                                  timeout=30)
            
            if result.returncode != 0:
                print(f"❌ FFmpeg failed: {result.stderr}")
                raise Exception(f"FFmpeg failed: {result.stderr}")
            
            # Read the raw audio data
            with open(temp_path, 'rb') as f:
                raw_data = f.read()
            
            # Convert to amplitude values
            audio_samples = struct.unpack(f'<{len(raw_data)//2}h', raw_data)
            duration = len(audio_samples) / 44100
            
            # Downsample for visualization
            target_length = 400
            if len(audio_samples) > target_length:
                step = len(audio_samples) // target_length
                waveform = audio_samples[::step][:target_length]
            else:
                waveform = audio_samples
            
            # Normalize to -1 to 1 range
            max_val = max(abs(v) for v in waveform) if waveform else 1
            if max_val > 0:
                waveform = [v / max_val for v in waveform]
            
            print(f"✅ FFmpeg waveform generated: {len(waveform)} points, {duration:.2f}s")
            
            return {
                'waveform': waveform,
                'duration': duration,
                'sample_rate': 44100,
                'method': 'ffmpeg'
            }
            
        finally:
            # Clean up temp file
            try:
                os.unlink(temp_path)
            except:
                pass
                
    except (subprocess.TimeoutExpired, subprocess.CalledProcessError, FileNotFoundError) as e:
        print(f"⚠️ FFmpeg not available or failed: {e}")
        # Fallback to direct WAV reading
        return generate_wav_waveform(file_path)
    
    except Exception as e:
        print(f"❌ Waveform generation error: {e}")
        return None

def generate_wav_waveform(file_path):
    """Fallback: Generate waveform from WAV files using Python's wave module"""
    import wave
    import struct
    
    try:
        # Only works for WAV files
        if file_path.suffix.lower() != '.wav':
            raise Exception("Not a WAV file and FFmpeg not available")
            
        with wave.open(str(file_path), 'rb') as wav_file:
            frames = wav_file.getnframes()
            sample_rate = wav_file.getframerate()
            duration = frames / sample_rate
            
            # Read a subset of frames for visualization
            max_frames = min(frames, sample_rate * 30)  # Max 30 seconds
            wav_file.setpos(0)
            raw_audio = wav_file.readframes(max_frames)
            
            # Convert to amplitude values
            if wav_file.getsampwidth() == 2:  # 16-bit
                audio_data = struct.unpack(f'<{len(raw_audio)//2}h', raw_audio)
            elif wav_file.getsampwidth() == 4:  # 32-bit
                audio_data = struct.unpack(f'<{len(raw_audio)//4}i', raw_audio)
            else:
                raise Exception(f"Unsupported bit depth: {wav_file.getsampwidth() * 8}")
            
            # Downsample for visualization
            target_length = 400
            if len(audio_data) > target_length:
                step = len(audio_data) // target_length
                waveform = audio_data[::step][:target_length]
            else:
                waveform = audio_data
            
            # Normalize to -1 to 1 range
            max_val = max(abs(v) for v in waveform) if waveform else 1
            if max_val > 0:
                waveform = [v / max_val for v in waveform]
            
            print(f"✅ WAV waveform generated: {len(waveform)} points, {duration:.2f}s")
            
            return {
                'waveform': waveform,
                'duration': duration,
                'sample_rate': sample_rate,
                'method': 'wave_module'
            }
                
    except Exception as e:
        print(f"❌ WAV waveform generation failed: {e}")
        return None

if __name__ == '__main__':
    # Create templates directory if it doesn't exist
    templates_dir = Path(__file__).parent / 'templates'
    templates_dir.mkdir(exist_ok=True)
    
    print("Beat Organizer GUI Server")
    print("=" * 50)
    print("Starting web interface...")
    print("Open your browser to: http://localhost:5000")
    print("=" * 50)
    
    app.run(debug=True, host='localhost', port=5000)

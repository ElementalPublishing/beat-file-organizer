#!/usr/bin/env python3
"""
Audio Metrics Analysis Module

Provides audio analysis for the Beat File Organizer using FFmpeg.
Extracts LUFS, dynamic range, peaks, and quality metrics.
"""

import subprocess
import json
import tempfile
import sqlite3
import hashlib
import numpy as np
from pathlib import Path
from dataclasses import dataclass, asdict
from typing import Optional, Dict, Any, List
from datetime import datetime
from collections import defaultdict

@dataclass
class AudioMetrics:
    """Complete audio metrics for a file"""
    filepath: Path
    filename: str
    file_size: int
    format: str
    bit_depth: Optional[int] = None
    sample_rate: Optional[int] = None
    duration: Optional[float] = None
    
    # Loudness metrics
    lufs: Optional[float] = None
    true_peak: Optional[float] = None
    rms_energy: Optional[float] = None
    dynamic_range: Optional[float] = None
    
    # Musical metrics
    bpm: Optional[float] = None
    key: Optional[str] = None
    
    # Quality metrics
    has_clipping: bool = False
    quality_score: Optional[int] = None
    classification: Optional[str] = None
    
    # Audio fingerprinting
    audio_fingerprint: Optional[str] = None
    fingerprint_method: str = "ffmpeg_waveform"
    
    # Analysis metadata
    analysis_date: Optional[datetime] = None
    analysis_method: str = "ffmpeg"

class AudioAnalyzer:
    """Analyzes audio files using FFmpeg"""
    
    def __init__(self):
        self.ffmpeg_available = self._check_ffmpeg()
        
    def _check_ffmpeg(self) -> bool:
        """Check if FFmpeg is available"""
        try:
            result = subprocess.run(['ffmpeg', '-version'], 
                                  capture_output=True, timeout=5)
            return result.returncode == 0
        except (FileNotFoundError, subprocess.TimeoutExpired):
            return False
    
    def analyze_file(self, filepath: Path) -> AudioMetrics:
        """Perform comprehensive audio analysis"""
        print(f"🔍 Analyzing: {filepath.name}")
        
        # Initialize metrics object
        metrics = AudioMetrics(
            filepath=filepath,
            filename=filepath.name,
            file_size=filepath.stat().st_size,
            format=filepath.suffix.lower(),
            analysis_date=datetime.now()
        )
        
        if not self.ffmpeg_available:
            print("⚠️ FFmpeg not available - basic analysis only")
            metrics.classification = "NO_ANALYSIS"
            metrics.quality_score = 50
            return metrics
        
        try:
            # Get basic audio info
            self._analyze_format_info(metrics)
            
            # Generate audio fingerprint for duplicate detection
            self._generate_audio_fingerprint(metrics)
            
            # Analyze loudness and dynamics
            self._analyze_loudness(metrics)
            
            # Analyze quality issues
            self._analyze_quality(metrics)
            
            # Calculate overall quality score
            self._calculate_quality_score(metrics)
            
            # Classify track
            self._classify_track(metrics)
            
            print(f"✅ Analysis complete: {metrics.classification}")
            
        except Exception as e:
            print(f"❌ Analysis failed: {e}")
            metrics.classification = "analysis_failed"
        
        return metrics
    
    def generate_fingerprint_only(self, filepath: Path) -> Optional[str]:
        """Generate only audio fingerprint without full analysis - for efficient duplicate detection"""
        try:
            metrics = AudioMetrics(
                filepath=filepath,
                filename=filepath.name,
                file_size=filepath.stat().st_size,
                format=filepath.suffix.lower()
            )
            
            # Generate only the fingerprint
            self._generate_audio_fingerprint(metrics)
            return metrics.audio_fingerprint
            
        except Exception as e:
            print(f"⚠️ Fingerprint generation failed for {filepath.name}: {e}")
            return None

    def generate_fingerprints_bulk(self, filepaths: List[Path], progress_callback=None) -> Dict[str, Optional[str]]:
        """Generate fingerprints for multiple files efficiently for duplicate detection"""
        results = {}
        
        print(f"🔑 Generating fingerprints for {len(filepaths)} files...")
        
        for i, filepath in enumerate(filepaths):
            if progress_callback:
                progress_callback(i, len(filepaths), filepath.name)
            
            results[str(filepath)] = self.generate_fingerprint_only(filepath)
        
        successful = len([r for r in results.values() if r])
        print(f"✅ Fingerprint generation complete: {successful}/{len(filepaths)} successful")
        return results

    def find_duplicates_by_fingerprints(self, fingerprints: Dict[str, Optional[str]], similarity_threshold: float = 98.0) -> Dict[str, List[str]]:
        """Find duplicate groups based on audio fingerprints"""
        print(f"🔍 Analyzing {len(fingerprints)} fingerprints for duplicates...")
        
        # Group files by fingerprint similarity
        duplicate_groups = {}
        processed_files = set()
        
        filepaths = list(fingerprints.keys())
        
        for i, filepath1 in enumerate(filepaths):
            if filepath1 in processed_files:
                continue
                
            fp1 = fingerprints.get(filepath1)
            if not fp1:
                continue
            
            # Find all files similar to this one
            group = [filepath1]
            processed_files.add(filepath1)
            
            for j, filepath2 in enumerate(filepaths[i+1:], i+1):
                if filepath2 in processed_files:
                    continue
                    
                fp2 = fingerprints.get(filepath2)
                if not fp2:
                    continue
                
                similarity = self.compare_audio_fingerprints(fp1, fp2)
                if similarity >= similarity_threshold:
                    group.append(filepath2)
                    processed_files.add(filepath2)
            
            # Only keep groups with actual duplicates
            if len(group) > 1:
                # Use first file as group key
                duplicate_groups[filepath1] = group
        
        total_duplicates = sum(len(group) - 1 for group in duplicate_groups.values())
        print(f"✅ Found {len(duplicate_groups)} duplicate groups with {total_duplicates} duplicate files")
        
        return duplicate_groups

    def generate_duplicate_comparison_data(self, duplicate_groups: Dict[str, List[str]]) -> Dict[str, Dict]:
        """Generate waveform and metadata for duplicate comparison"""
        print(f"🌊 Generating waveform data for {len(duplicate_groups)} duplicate groups...")
        
        comparison_data = {}
        
        for group_key, filepaths in duplicate_groups.items():
            group_data = {
                'primary_file': group_key,
                'files': [],
                'group_id': hashlib.md5(group_key.encode()).hexdigest()[:8]
            }
            
            for filepath in filepaths:
                file_path = Path(filepath)
                
                # Generate waveform for comparison
                waveform = self.generate_waveform(file_path, width=400, height=100)
                
                # Get basic file info quickly
                try:
                    file_stat = file_path.stat()
                    file_data = {
                        'filepath': filepath,
                        'filename': file_path.name,
                        'filesize': file_stat.st_size,
                        'filesize_formatted': self._format_file_size(file_stat.st_size),
                        'modified_date': file_stat.st_mtime,
                        'waveform': waveform,
                        'duration': None,  # Will be filled by quick analysis if needed
                        'format': file_path.suffix.lower(),
                        'quality_hint': 'unknown'  # Will be determined by user analysis
                    }
                    
                    # Quick duration check using ffprobe (fast)
                    try:
                        cmd = ['ffprobe', '-v', 'quiet', '-show_format', '-print_format', 'json', str(file_path)]
                        result = subprocess.run(cmd, capture_output=True, text=True, timeout=10)
                        if result.returncode == 0:
                            data = json.loads(result.stdout)
                            duration = data.get('format', {}).get('duration')
                            if duration:
                                file_data['duration'] = float(duration)
                                file_data['duration_formatted'] = self._format_duration(float(duration))
                    except:
                        pass
                    
                    group_data['files'].append(file_data)
                    
                except Exception as e:
                    print(f"⚠️ Error processing {filepath}: {e}")
            
            comparison_data[group_key] = group_data
        
        return comparison_data

    def _format_file_size(self, size_bytes: int) -> str:
        """Format file size in human readable format"""
        size = float(size_bytes)
        for unit in ['B', 'KB', 'MB', 'GB']:
            if size < 1024.0:
                return f"{size:.1f} {unit}"
            size /= 1024.0
        return f"{size:.1f} TB"

    def _format_duration(self, duration: float) -> str:
        """Format duration in MM:SS format"""
        minutes = int(duration // 60)
        seconds = int(duration % 60)
        return f"{minutes:02d}:{seconds:02d}"

    def _analyze_format_info(self, metrics: AudioMetrics):
        """Extract basic format information"""
        cmd = [
            'ffprobe', '-v', 'quiet',
            '-print_format', 'json',
            '-show_format', '-show_streams',
            str(metrics.filepath)
        ]
        
        try:
            result = subprocess.run(cmd, capture_output=True, text=True, timeout=30)
            if result.returncode == 0:
                data = json.loads(result.stdout)
                
                # Get audio stream info
                for stream in data.get('streams', []):
                    if stream.get('codec_type') == 'audio':
                        metrics.sample_rate = int(stream.get('sample_rate', 0)) or None
                        metrics.bit_depth = self._parse_bit_depth(stream.get('bits_per_sample'))
                        break
                
                # Get duration
                format_info = data.get('format', {})
                duration_str = format_info.get('duration')
                if duration_str:
                    metrics.duration = float(duration_str)
                    
        except (subprocess.TimeoutExpired, json.JSONDecodeError, ValueError) as e:
            print(f"⚠️ Format analysis failed: {e}")
    
    def _analyze_loudness(self, metrics: AudioMetrics):
        """Analyze loudness using FFmpeg's ebur128 filter"""
        try:
            cmd = [
                'ffmpeg', '-i', str(metrics.filepath),
                '-af', 'ebur128=peak=true:framelog=verbose',
                '-f', 'null', '-',
                '-v', 'info'
            ]
            
            result = subprocess.run(cmd, capture_output=True, text=True, timeout=60)
            
            if result.returncode == 0:
                # Parse loudness information from stderr
                output = result.stderr
                
                # Extract LUFS
                if 'I:' in output:
                    for line in output.split('\n'):
                        if 'I:' in line and 'LUFS' in line:
                            try:
                                lufs_str = line.split('I:')[1].split('LUFS')[0].strip()
                                metrics.lufs = float(lufs_str)
                                break
                            except (ValueError, IndexError):
                                continue
                
                # Extract True Peak
                if 'Peak:' in output:
                    for line in output.split('\n'):
                        if 'Peak:' in line and 'dBFS' in line:
                            try:
                                peak_str = line.split('Peak:')[1].split('dBFS')[0].strip()
                                metrics.true_peak = float(peak_str)
                                break
                            except (ValueError, IndexError):
                                continue
                
                print(f"📊 LUFS: {metrics.lufs}, True Peak: {metrics.true_peak}")
                
        except subprocess.TimeoutExpired:
            print("⚠️ Loudness analysis timed out")
        except Exception as e:
            print(f"⚠️ Loudness analysis failed: {e}")
    
    def _analyze_quality(self, metrics: AudioMetrics):
        """Analyze quality issues like clipping"""
        if metrics.true_peak is not None:
            metrics.has_clipping = metrics.true_peak > 0.0
    
    def _calculate_quality_score(self, metrics: AudioMetrics):
        """Calculate overall quality score (0-100)"""
        score = 100
        
        # Penalize clipping heavily
        if metrics.has_clipping:
            score -= 40
        elif metrics.true_peak and metrics.true_peak > -0.5:
            score -= 20
        
        # Evaluate loudness compliance
        if metrics.lufs:
            if metrics.lufs < -23:  # Too quiet
                score -= 20
            elif metrics.lufs > -8:  # Too loud
                score -= 25
            elif -16 <= metrics.lufs <= -12:  # Sweet spot
                score += 10
        
        # Reward high technical quality
        if metrics.bit_depth and metrics.bit_depth >= 24:
            score += 5
        if metrics.sample_rate and metrics.sample_rate >= 48000:
            score += 5
        
        metrics.quality_score = max(0, min(100, score))
    
    def _classify_track(self, metrics: AudioMetrics):
        """Classify track based on metrics"""
        if metrics.has_clipping:
            metrics.classification = "CLIPPED"
        elif metrics.lufs and metrics.lufs > -8:
            metrics.classification = "TOO_LOUD"
        elif metrics.lufs and metrics.lufs < -23:
            metrics.classification = "TOO_QUIET"
        elif metrics.quality_score and metrics.quality_score >= 85:
            metrics.classification = "STREAMING_READY"
        elif metrics.quality_score and metrics.quality_score >= 70:
            metrics.classification = "GOOD_QUALITY"
        elif metrics.quality_score and metrics.quality_score >= 50:
            metrics.classification = "NEEDS_WORK"
        else:
            metrics.classification = "MAJOR_ISSUES"
    
    def _parse_bit_depth(self, bits_per_sample) -> Optional[int]:
        """Parse bit depth from FFprobe output"""
        if bits_per_sample:
            try:
                return int(bits_per_sample)
            except (ValueError, TypeError):
                pass
        return None

    def check_ffmpeg(self) -> bool:
        """Check if FFmpeg is available"""
        return self._check_ffmpeg()
    
    def generate_waveform(self, filepath: Path, width: int = 800, height: int = 200) -> Optional[List[float]]:
        """Generate waveform data for visualization"""
        try:
            import numpy as np
            
            # Use FFmpeg to extract audio data for waveform
            cmd = [
                'ffmpeg', '-i', str(filepath),
                '-ac', '1',  # Mono
                '-ar', '8000',  # Low sample rate for visualization
                '-f', 'f32le',  # Float32 little endian
                '-'
            ]
            
            result = subprocess.run(
                cmd, 
                stdout=subprocess.PIPE,
                stderr=subprocess.DEVNULL
            )
            
            if result.returncode != 0:
                return None
            
            # Convert bytes to float array
            audio_data = np.frombuffer(result.stdout, dtype=np.float32)
            
            if len(audio_data) == 0:
                return None
            
            # Downsample to target width
            if len(audio_data) > width:
                chunk_size = len(audio_data) // width
                downsampled = []
                for i in range(0, len(audio_data), chunk_size):
                    chunk = audio_data[i:i+chunk_size]
                    if len(chunk) > 0:
                        # Use RMS for better visual representation
                        rms = np.sqrt(np.mean(chunk**2))
                        downsampled.append(float(rms))
                audio_data = np.array(downsampled[:width])
            
            # Normalize to height
            if len(audio_data) > 0:
                max_val = np.max(np.abs(audio_data))
                if max_val > 0:
                    audio_data = (audio_data / max_val) * (height / 2)
            
            return audio_data.tolist()
            
        except Exception as e:
            print(f"Waveform generation error: {e}")
            return None

    def _generate_audio_fingerprint(self, metrics: AudioMetrics):
        """Generate perceptual hash of audio content for duplicate detection"""
        try:
            # Use FFmpeg to extract audio features for fingerprinting
            # Focus on vocal range and first 30 seconds for efficiency
            cmd = [
                'ffmpeg', '-i', str(metrics.filepath),
                '-af', 'highpass=f=200,lowpass=f=4000',  # Focus on vocal range
                '-f', 's16le', '-ac', '1', '-ar', '22050',  # Mono, 22kHz
                '-t', '30',  # First 30 seconds
                'pipe:'
            ]
            
            result = subprocess.run(
                cmd, 
                stdout=subprocess.PIPE,
                stderr=subprocess.DEVNULL,
                timeout=60
            )
            
            if result.returncode == 0 and result.stdout:
                # Create perceptual hash from audio data
                fingerprint = self._create_perceptual_hash(result.stdout)
                metrics.audio_fingerprint = fingerprint
                print(f"🔑 Generated fingerprint: {fingerprint[:16]}...")
            else:
                print(f"⚠️ Fingerprint generation failed for {metrics.filename}")
                
        except subprocess.TimeoutExpired:
            print(f"⚠️ Fingerprint generation timeout for {metrics.filename}")
        except Exception as e:
            print(f"⚠️ Fingerprint generation error: {e}")
    
    def _create_perceptual_hash(self, audio_data: bytes) -> str:
        """Create a perceptual hash from audio data"""
        try:
            # Convert bytes to numpy array
            audio_array = np.frombuffer(audio_data, dtype=np.int16)
            
            if len(audio_array) == 0:
                return ""
            
            # Calculate frequency domain features for perceptual hashing
            # 1. Divide into chunks for temporal analysis
            chunk_size = 2048
            chunks = [audio_array[i:i+chunk_size] for i in range(0, len(audio_array), chunk_size)]
            
            # 2. Calculate spectral features for each chunk
            spectral_features = []
            for chunk in chunks[:32]:  # Limit to first 32 chunks (~3 seconds)
                if len(chunk) < chunk_size:
                    chunk = np.pad(chunk, (0, chunk_size - len(chunk)))
                
                # Simple spectral analysis
                fft = np.fft.fft(chunk)
                magnitude = np.abs(fft[:chunk_size//2])
                
                # Focus on key frequency bands for music
                bands = [
                    magnitude[0:50],      # Low frequencies
                    magnitude[50:200],    # Mid-low
                    magnitude[200:800],   # Mid
                    magnitude[800:2000],  # Mid-high
                    magnitude[2000:]      # High
                ]
                
                # Calculate energy in each band
                band_energies = [np.mean(band) for band in bands]
                spectral_features.extend(band_energies)
            
            # 3. Create hash from spectral features
            if spectral_features:
                # Normalize features
                features = np.array(spectral_features)
                if np.std(features) > 0:
                    features = (features - np.mean(features)) / np.std(features)
                
                # Create binary hash based on feature relationships
                hash_bits = []
                for i in range(0, len(features)-1, 2):
                    if i+1 < len(features):
                        # Compare adjacent features
                        hash_bits.append('1' if features[i] > features[i+1] else '0')
                
                # Convert to hex string
                binary_str = ''.join(hash_bits)
                # Pad to multiple of 4 for hex conversion
                while len(binary_str) % 4 != 0:
                    binary_str += '0'
                
                hex_hash = hex(int(binary_str, 2))[2:].upper()
                return hex_hash
            
            return ""
            
        except Exception as e:
            print(f"⚠️ Perceptual hash creation error: {e}")
            return ""
    
    def compare_audio_fingerprints(self, fp1: str, fp2: str) -> float:
        """Compare audio fingerprints for similarity (0-100%)"""
        if not fp1 or not fp2 or fp1 == fp2:
            return 100.0 if fp1 == fp2 else 0.0
        
        try:
            # Convert hex fingerprints to binary for comparison
            bin1 = bin(int(fp1, 16))[2:].zfill(len(fp1) * 4)
            bin2 = bin(int(fp2, 16))[2:].zfill(len(fp2) * 4)
            
            # Align lengths
            max_len = max(len(bin1), len(bin2))
            bin1 = bin1.zfill(max_len)
            bin2 = bin2.zfill(max_len)
            
            # Calculate Hamming distance
            matches = sum(1 for a, b in zip(bin1, bin2) if a == b)
            similarity = (matches / len(bin1)) * 100
            
            return similarity
            
        except (ValueError, ZeroDivisionError):
            return 0.0
    
    def find_audio_duplicates(self, metrics_list: List[AudioMetrics], threshold: float = 99.0) -> Dict[str, List[AudioMetrics]]:
        """Find duplicate audio files based on fingerprints"""
        duplicates = {}
        processed = set()
        
        for i, metrics1 in enumerate(metrics_list):
            if i in processed or not metrics1.audio_fingerprint:
                continue
                
            group = [metrics1]
            processed.add(i)
            
            for j, metrics2 in enumerate(metrics_list[i+1:], i+1):
                if j in processed or not metrics2.audio_fingerprint:
                    continue
                    
                similarity = self.compare_audio_fingerprints(
                    metrics1.audio_fingerprint, 
                    metrics2.audio_fingerprint
                )
                
                if similarity >= threshold:
                    group.append(metrics2)
                    processed.add(j)
            
            if len(group) > 1:
                # Use the first file as the key
                key = str(metrics1.filepath)
                duplicates[key] = group
        
        return duplicates

    def get_unique_files(self, all_filepaths: List[Path], duplicate_groups: Dict[str, List[str]]) -> List[Path]:
        """Get list of unique files (not in any duplicate group) for individual analysis"""
        # Get all files that are in duplicate groups
        files_in_groups = set()
        for group in duplicate_groups.values():
            files_in_groups.update(group)
        
        # Return files that are NOT in any duplicate group
        unique_files = []
        for filepath in all_filepaths:
            if str(filepath) not in files_in_groups:
                unique_files.append(filepath)
        
        print(f"📊 Identified {len(unique_files)} unique files for individual analysis")
        return unique_files

    def compare_duplicate_audio_quality(self, filepaths: List[str]) -> Dict[str, Dict]:
        """Quick quality comparison for duplicate files to help user choose best version"""
        print(f"⚖️ Comparing audio quality for {len(filepaths)} duplicate files...")
        
        comparison_results = {}
        
        for filepath in filepaths:
            file_path = Path(filepath)
            result = {
                'filepath': filepath,
                'filename': file_path.name,
                'filesize': file_path.stat().st_size,
                'format': file_path.suffix.lower(),
                'estimated_quality': 'unknown',
                'technical_score': 0
            }
            
            # Quick technical assessment
            try:
                # Check file format (lossless vs lossy)
                if file_path.suffix.lower() in ['.wav', '.flac', '.aiff']:
                    result['estimated_quality'] = 'lossless'
                    result['technical_score'] += 30
                elif file_path.suffix.lower() in ['.mp3', '.m4a', '.ogg']:
                    result['estimated_quality'] = 'lossy'
                    result['technical_score'] += 10
                
                # Larger file usually means higher quality (for same format)
                size_mb = file_path.stat().st_size / (1024 * 1024)
                if size_mb > 50:
                    result['technical_score'] += 20
                elif size_mb > 20:
                    result['technical_score'] += 10
                
                # Get sample rate and bit depth with ffprobe
                cmd = ['ffprobe', '-v', 'quiet', '-show_streams', '-print_format', 'json', str(file_path)]
                ffprobe_result = subprocess.run(cmd, capture_output=True, text=True, timeout=15)
                
                if ffprobe_result.returncode == 0:
                    data = json.loads(ffprobe_result.stdout)
                    for stream in data.get('streams', []):
                        if stream.get('codec_type') == 'audio':
                            sample_rate = stream.get('sample_rate')
                            bit_rate = stream.get('bit_rate')
                            
                            if sample_rate:
                                sr = int(sample_rate)
                                if sr >= 96000:
                                    result['technical_score'] += 25
                                elif sr >= 48000:
                                    result['technical_score'] += 15
                                elif sr >= 44100:
                                    result['technical_score'] += 10
                                result['sample_rate'] = sr
                            
                            if bit_rate:
                                br = int(bit_rate)
                                if br >= 320000:  # 320 kbps or higher
                                    result['technical_score'] += 20
                                elif br >= 192000:  # 192 kbps
                                    result['technical_score'] += 10
                                result['bit_rate'] = br
                            
                            break
                
                # Classify overall quality
                if result['technical_score'] >= 60:
                    result['quality_recommendation'] = 'best'
                elif result['technical_score'] >= 40:
                    result['quality_recommendation'] = 'good'
                elif result['technical_score'] >= 20:
                    result['quality_recommendation'] = 'acceptable'
                else:
                    result['quality_recommendation'] = 'poor'
                
            except Exception as e:
                print(f"⚠️ Quality assessment failed for {filepath}: {e}")
                result['quality_recommendation'] = 'unknown'
            
            comparison_results[filepath] = result
        
        return comparison_results

    def comprehensive_duplicate_analysis(self, filepaths: List[Path], progress_callback=None) -> Dict[str, Any]:
        """Complete workflow: fingerprint → find duplicates → prepare comparison data → identify unique files"""
        print(f"🔄 Starting comprehensive duplicate analysis for {len(filepaths)} files...")
        
        # Step 1: Generate fingerprints for all files
        if progress_callback:
            progress_callback(0, 100, "Generating audio fingerprints...")
        
        fingerprints = self.generate_fingerprints_bulk(filepaths, 
            lambda completed, total, current_file: progress_callback(
                int((completed / total) * 40), 100, f"Fingerprinting: {current_file}"
            ) if progress_callback else None
        )
        
        # Step 2: Find duplicate groups
        if progress_callback:
            progress_callback(45, 100, "Analyzing fingerprints for duplicates...")
        
        duplicate_groups = self.find_duplicates_by_fingerprints(fingerprints, similarity_threshold=98.0)
        
        # Step 3: Generate comparison data for duplicates
        if progress_callback:
            progress_callback(60, 100, "Generating waveforms for duplicate comparison...")
        
        duplicate_comparison_data = self.generate_duplicate_comparison_data(duplicate_groups)
        
        # Step 4: Get unique files for separate analysis
        if progress_callback:
            progress_callback(80, 100, "Identifying unique files...")
        
        unique_files = self.get_unique_files(filepaths, duplicate_groups)
        
        # Step 5: Quality comparison for duplicates
        if progress_callback:
            progress_callback(90, 100, "Comparing duplicate quality...")
        
        quality_comparisons = {}
        for group_key, group_files in duplicate_groups.items():
            quality_comparisons[group_key] = self.compare_duplicate_audio_quality(group_files)
        
        if progress_callback:
            progress_callback(100, 100, "Analysis complete!")
        
        total_duplicates = sum(len(group) - 1 for group in duplicate_groups.values())
        
        result = {
            'success': True,
            'total_files': len(filepaths),
            'unique_files': len(unique_files),
            'duplicate_groups': len(duplicate_groups),
            'total_duplicates': total_duplicates,
            'fingerprint_success_rate': len([f for f in fingerprints.values() if f]) / len(filepaths) * 100,
            'unique_file_paths': [str(f) for f in unique_files],
            'duplicate_groups_data': duplicate_comparison_data,
            'quality_comparisons': quality_comparisons,
            'workflow_summary': {
                'phase_1': f"Generated {len([f for f in fingerprints.values() if f])} fingerprints",
                'phase_2': f"Found {len(duplicate_groups)} duplicate groups",
                'phase_3': f"Prepared comparison data for {len(duplicate_comparison_data)} groups",
                'phase_4': f"Identified {len(unique_files)} unique files for analysis",
                'phase_5': f"Quality assessment complete"
            }
        }
        
        print(f"✅ Comprehensive analysis complete:")
        print(f"   📁 {len(filepaths)} total files processed")
        print(f"   🔄 {len(duplicate_groups)} duplicate groups found")
        print(f"   📊 {len(unique_files)} unique files ready for analysis")
        print(f"   ⚖️ Quality comparison data prepared")
        
        return result

class MetricsDatabase:
    """SQLite database for caching audio metrics with audio fingerprint support"""
    
    def __init__(self, db_path: Optional[Path] = None):
        if db_path is None:
            db_path = Path.home() / '.beat_organizer' / 'metrics.db'
        
        self.db_path = db_path
        self.db_path.parent.mkdir(parents=True, exist_ok=True)
        self._init_database()
    
    def _init_database(self):
        """Initialize the database schema with audio fingerprint support"""
        with sqlite3.connect(self.db_path) as conn:
            conn.execute('''
                CREATE TABLE IF NOT EXISTS audio_metrics (
                    filepath TEXT PRIMARY KEY,
                    filename TEXT,
                    file_size INTEGER,
                    file_hash TEXT,
                    format TEXT,
                    bit_depth INTEGER,
                    sample_rate INTEGER,
                    duration REAL,
                    lufs REAL,
                    true_peak REAL,
                    rms_energy REAL,
                    dynamic_range REAL,
                    bpm REAL,
                    key TEXT,
                    has_clipping BOOLEAN,
                    quality_score INTEGER,
                    classification TEXT,
                    audio_fingerprint TEXT,
                    fingerprint_method TEXT,
                    analysis_date TEXT,
                    analysis_method TEXT
                )
            ''')
            
            # Add audio fingerprint columns if they don't exist (for existing databases)
            try:
                conn.execute('ALTER TABLE audio_metrics ADD COLUMN audio_fingerprint TEXT')
                conn.execute('ALTER TABLE audio_metrics ADD COLUMN fingerprint_method TEXT')
            except sqlite3.OperationalError:
                # Columns already exist
                pass
                
            conn.commit()
    
    def save_metrics(self, metrics: AudioMetrics):
        """Save metrics to database including audio fingerprint"""
        file_hash = self._calculate_file_hash(metrics.filepath)
        
        with sqlite3.connect(self.db_path) as conn:
            conn.execute('''
                INSERT OR REPLACE INTO audio_metrics VALUES (
                    ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?
                )
            ''', (
                str(metrics.filepath), metrics.filename, metrics.file_size,
                file_hash, metrics.format, metrics.bit_depth, metrics.sample_rate,
                metrics.duration, metrics.lufs, metrics.true_peak, metrics.rms_energy,
                metrics.dynamic_range, metrics.bpm, metrics.key, metrics.has_clipping,
                metrics.quality_score, metrics.classification,
                metrics.audio_fingerprint, metrics.fingerprint_method,
                metrics.analysis_date.isoformat() if metrics.analysis_date else None,
                metrics.analysis_method
            ))
            conn.commit()
    
    def get_metrics(self, filepath: Path) -> Optional[Dict]:
        """Get cached metrics for a file"""
        try:
            current_hash = self._calculate_file_hash(filepath)
        except:
            return None
            
        with sqlite3.connect(self.db_path) as conn:
            conn.row_factory = sqlite3.Row
            cursor = conn.execute(
                'SELECT * FROM audio_metrics WHERE filepath = ? AND file_hash = ?',
                (str(filepath), current_hash)
            )
            row = cursor.fetchone()
            
            if row:
                return dict(row)
        
        return None
    
    def _calculate_file_hash(self, filepath: Path) -> str:
        """Calculate a hash based on file size and modification time"""
        stat = filepath.stat()
        hash_input = f"{stat.st_size}_{stat.st_mtime}".encode()
        return hashlib.md5(hash_input).hexdigest()
    
    def is_healthy(self) -> bool:
        """Check if database is healthy and accessible"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                conn.execute('SELECT COUNT(*) FROM audio_metrics')
                return True
        except Exception:
            return False
    
    def get_collection_stats(self, directory: str) -> Dict[str, Any]:
        """Get statistics for a collection of files"""
        with sqlite3.connect(self.db_path) as conn:
            conn.row_factory = sqlite3.Row
            
            cursor = conn.execute('''
                SELECT 
                    COUNT(*) as total_files,
                    AVG(lufs) as avg_lufs,
                    AVG(dynamic_range) as avg_dynamic_range,
                    AVG(quality_score) as avg_quality,
                    SUM(CASE WHEN has_clipping = 1 THEN 1 ELSE 0 END) as clipped_files,
                    COUNT(DISTINCT audio_fingerprint) as unique_audio_fingerprints
                FROM audio_metrics 
                WHERE filepath LIKE ?
            ''', (f"{directory}%",))
            
            result = cursor.fetchone()
            if result:
                return dict(result)
            else:
                return {}

    def find_fingerprint_duplicates(self, threshold: float = 99.0) -> Dict[str, List[Dict]]:
        """Find duplicate audio fingerprints in the database"""
        with sqlite3.connect(self.db_path) as conn:
            conn.row_factory = sqlite3.Row
            
            # Get all files with fingerprints
            cursor = conn.execute('''
                SELECT filepath, filename, audio_fingerprint, quality_score
                FROM audio_metrics 
                WHERE audio_fingerprint IS NOT NULL AND audio_fingerprint != ""
                ORDER BY quality_score DESC
            ''')
            
            all_files = [dict(row) for row in cursor.fetchall()]
            
            # Group by exact fingerprint matches (for now - could implement similarity later)
            fingerprint_groups = defaultdict(list)
            for file_info in all_files:
                fp = file_info['audio_fingerprint']
                fingerprint_groups[fp].append(file_info)
            
            # Return only groups with duplicates
            duplicates = {fp: files for fp, files in fingerprint_groups.items() if len(files) > 1}
            
            return duplicates

def analyze_track_issues(metrics: AudioMetrics) -> Dict[str, Any]:
    """Analyze a track and return issues and recommendations"""
    issues = []
    recommendations = []
    
    # Volume Issues
    if metrics.lufs:
        if metrics.lufs < -23:
            issues.append("TOO QUIET - Needs significant level boost")
            recommendations.append("Increase gain by +6dB minimum before mastering")
        elif metrics.lufs < -20:
            issues.append("Quiet - May need mastering")
            recommendations.append("Apply gentle compression and limiting")
        elif metrics.lufs > -8:
            issues.append("TOO LOUD - Over-compressed")
            recommendations.append("Reduce limiting, increase dynamic range")
        elif metrics.lufs > -12:
            issues.append("Loud - May sound fatiguing")
            recommendations.append("Consider quieter master for streaming")
    
    # Clipping Issues
    if metrics.has_clipping:
        issues.append("CLIPPING - Digital distortion present")
        recommendations.append("URGENT: Apply true peak limiting below -1dBTP")
    elif metrics.true_peak and metrics.true_peak > -0.5:
        issues.append("Peak Warning - Close to clipping")
        recommendations.append("Apply stricter peak limiting for safety")
    
    # Technical Quality Issues
    if metrics.bit_depth and metrics.bit_depth < 24:
        issues.append("Low bit depth - May have noise floor issues")
        recommendations.append("Use 24-bit for production, 16-bit only for final delivery")
    
    if metrics.sample_rate and metrics.sample_rate < 44100:
        issues.append("Low sample rate - Frequency range limited")
        recommendations.append("Record/mix at 48kHz minimum")
    
    return {
        'issues': issues,
        'recommendations': recommendations,
        'overall_score': metrics.quality_score or 0
    }

def classify_track_by_metrics(metrics: AudioMetrics) -> Dict[str, Any]:
    """Classify track and suggest organization folder"""
    analysis = analyze_track_issues(metrics)
    
    # Determine primary classification and folder suggestion
    if metrics.has_clipping:
        classification = "CLIPPED"
        folder = "00_URGENT_CLIPPED"
        action = "Fix immediately - digital distortion present"
    elif metrics.quality_score and metrics.quality_score >= 85:
        classification = "STREAMING_READY"
        folder = "01_MASTERS_StreamingReady"
        action = "Ready for release"
    elif metrics.lufs and metrics.lufs < -23:
        classification = "TOO_QUIET"
        folder = "03_NEEDS_Mastering/too_quiet"
        action = "Apply gain/compression to reach -16 LUFS"
    elif metrics.lufs and metrics.lufs > -8:
        classification = "TOO_LOUD"
        folder = "04_NEEDS_Remaster/over_compressed"
        action = "Create quieter streaming master (-14 LUFS)"
    elif metrics.quality_score and metrics.quality_score >= 50:
        classification = "NEEDS_WORK"
        folder = "03_NEEDS_Mastering"
        action = "Apply mastering chain for consistency"
    else:
        classification = "MAJOR_ISSUES"
        folder = "05_DAMAGED_Issues"
        action = "Requires attention before use"
    
    return {
        'classification': classification,
        'suggested_folder': folder,
        'action': action,
        'issues': analysis['issues'],
        'recommendations': analysis['recommendations'],
        'quality_score': metrics.quality_score or 0
    }

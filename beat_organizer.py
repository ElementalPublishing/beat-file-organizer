#!/usr/bin/env python3
# type: ignore
"""
Beat File Organizer - The Producer's File Management Solution

A clean, focused tool for organizing music production files.
Finds duplicates, suggests organization, and helps clean up the chaos.

Usage:
    python beat_organizer.py scan "C:/path/to/beats" 
    python beat_organizer.py duplicates "C:/path/to/beats"
    python beat_organizer.py stats "C:/path/to/beats"
    python beat_organizer.py organize "C:/path/to/beats" --output "C:/Users/username/Music"
"""

import os
import re
import hashlib
import argparse
import sys
import threading
from pathlib import Path
from typing import List, Dict, Optional, Any
from dataclasses import dataclass
from collections import defaultdict
from datetime import datetime

# Import our audio metrics module
try:
    from audio_metrics import AudioAnalyzer, MetricsDatabase, AudioMetrics, classify_track_by_metrics, analyze_track_issues
    AUDIO_METRICS_AVAILABLE = True
except ImportError:
    AUDIO_METRICS_AVAILABLE = False
    print("⚠️ Audio metrics module not available - basic analysis only")

@dataclass
class AudioFile:
    """Represents an audio file with basic metadata"""
    filepath: Path
    filename: str
    filesize: int
    format: str
    file_hash: str
    created_date: datetime
    modified_date: datetime
    estimated_duration: Optional[float] = None

class BeatOrganizer:
    """Main Beat File Organizer class with audio metrics integration"""
    
    SUPPORTED_FORMATS = {'.wav', '.mp3', '.flac', '.aif', '.aiff', '.m4a', '.ogg'}
    
    def __init__(self, enable_metrics: bool = True):
        """Initialize the organizer"""
        self.enable_metrics = enable_metrics and AUDIO_METRICS_AVAILABLE
        
        if self.enable_metrics:
            self.audio_analyzer = AudioAnalyzer()
            self.metrics_db = MetricsDatabase()
            print("✅ Audio metrics analysis enabled")
        else:
            self.audio_analyzer = None
            self.metrics_db = None
            if enable_metrics:
                print("⚠️ Audio metrics requested but not available")
    
    def scan_directory(self, path: Path, recursive: bool = True) -> List[AudioFile]:
        """Scan directory for audio files"""
        print(f"Scanning {path}{'...' if recursive else ' (non-recursive)...'}")
        
        audio_files = []
        pattern = "**/*" if recursive else "*"
        
        try:
            # Pre-filter by extension for speed
            for filepath in path.glob(pattern):
                if filepath.is_file() and filepath.suffix.lower() in self.SUPPORTED_FORMATS:
                    audio_file = self._analyze_file(filepath)
                    if audio_file:
                        audio_files.append(audio_file)
                        if len(audio_files) % 100 == 0:
                            print(f"  Found {len(audio_files)} files...")
        except Exception as e:
            print(f"Error scanning: {e}")
        
        print(f"Scan complete: {len(audio_files)} audio files found")
        return audio_files
    
    def _analyze_file(self, filepath: Path) -> Optional[AudioFile]:
        """Analyze a single audio file"""
        try:
            stat = filepath.stat()
            filesize = stat.st_size
            created_date = datetime.fromtimestamp(stat.st_mtime)
            modified_date = datetime.fromtimestamp(stat.st_mtime)
            
            # Generate file hash for duplicate detection
            file_hash = self._generate_file_hash(filepath)
            
            # Rough duration estimate
            estimated_duration = self._estimate_duration(filesize, filepath.suffix)
            
            return AudioFile(
                filepath=filepath,
                filename=filepath.name,
                filesize=filesize,
                format=filepath.suffix.lower(),
                file_hash=file_hash,
                created_date=created_date,
                modified_date=modified_date,
                estimated_duration=estimated_duration
            )
        except Exception as e:
            print(f"Error analyzing {filepath.name}: {e}")
            return None
    
    def generate_fingerprints_bulk(self, audio_files: List[AudioFile], progress_callback=None) -> Dict[str, str]:
        """Generate fingerprints for multiple files efficiently"""
        fingerprints = {}
        total_files = len(audio_files)
        
        for i, audio_file in enumerate(audio_files):
            if progress_callback:
                progress_callback(i, total_files, f"Generating fingerprint: {audio_file.filename}")
            
            fingerprint = self.audio_analyzer.generate_fingerprint_only(audio_file.filepath)
            if fingerprint:
                fingerprints[str(audio_file.filepath)] = fingerprint
        
        return fingerprints

    def analyze_audio_metrics(self, filepath: Path) -> Optional[Dict[str, Any]]:
        """Analyze audio metrics for a single file"""
        if not self.enable_metrics:
            return None
            
        try:
            # Check if we already have cached metrics
            cached_metrics = self.metrics_db.get_metrics(filepath)
            if cached_metrics:
                print(f"📊 Using cached metrics for {filepath.name}")
                return cached_metrics
            
            # Perform new analysis
            print(f"🔍 Analyzing audio metrics for {filepath.name}")
            metrics = self.audio_analyzer.analyze_file(filepath)
            
            if not metrics:
                return None
            
            # Save to cache
            self.metrics_db.save_metrics(metrics)
            
            # Get classification and organization info
            classification_info = classify_track_by_metrics(metrics)
            
            # Convert to dict for JSON serialization with safe field access
            return {
                'filepath': str(metrics.filepath),
                'filename': metrics.filename,
                'file_size': getattr(metrics, 'file_size', 0),
                'format': getattr(metrics, 'format', ''),
                'bit_depth': getattr(metrics, 'bit_depth', None),
                'sample_rate': getattr(metrics, 'sample_rate', None),
                'duration': getattr(metrics, 'duration', None),
                'lufs': getattr(metrics, 'lufs', None),
                'true_peak': getattr(metrics, 'true_peak', None),
                'rms_energy': getattr(metrics, 'rms_energy', None),
                'dynamic_range': getattr(metrics, 'dynamic_range', None),
                'bpm': getattr(metrics, 'bpm', None),
                'key': getattr(metrics, 'key', None),
                'has_clipping': getattr(metrics, 'has_clipping', False),
                'quality_score': getattr(metrics, 'quality_score', None),
                'classification': getattr(metrics, 'classification', None),
                'suggested_folder': classification_info.get('suggested_folder', '06_NEEDS_Analysis'),
                'action': classification_info.get('action', 'Analyze manually'),
                'issues': classification_info.get('issues', []),
                'recommendations': classification_info.get('recommendations', [])
            }
            
        except Exception as e:
            print(f"❌ Audio metrics analysis failed for {filepath.name}: {e}")
            return None
    
    def get_collection_metrics_report(self) -> Dict:
        """Get comprehensive metrics report for the entire collection"""
        if not self.enable_metrics:
            return {'error': 'Audio metrics not enabled'}
        
        return self.metrics_db.get_collection_stats()
    
    def organize_by_metrics(self, audio_files: List[AudioFile], output_dir: Path) -> Dict:
        """Organize files based on audio metrics analysis"""
        if not self.enable_metrics:
            return {'error': 'Audio metrics not enabled'}
        
        organization_results = {
            'organized_files': {},
            'failed_files': [],
            'summary': {}
        }
        
        print(f"🎯 Organizing {len(audio_files)} files by audio metrics...")
        
        for i, audio_file in enumerate(audio_files):
            print(f"📁 Processing {i+1}/{len(audio_files)}: {audio_file.filename}")
            
            try:
                # Get or analyze metrics
                metrics_data = self.analyze_audio_metrics(audio_file.filepath)
                if not metrics_data:
                    organization_results['failed_files'].append(str(audio_file.filepath))
                    continue
                
                # Determine target folder
                suggested_folder = metrics_data.get('suggested_folder', '06_NEEDS_Analysis')
                target_dir = output_dir / suggested_folder
                target_dir.mkdir(parents=True, exist_ok=True)
                
                # Generate target filepath
                target_path = target_dir / audio_file.filename
                
                # Handle name conflicts
                counter = 1
                original_target = target_path
                while target_path.exists():
                    name_parts = original_target.stem, counter, original_target.suffix
                    target_path = original_target.parent / f"{name_parts[0]}_{name_parts[1]}{name_parts[2]}"
                    counter += 1
                
                # Record the organization decision
                classification = metrics_data.get('classification', 'UNKNOWN')
                if classification not in organization_results['organized_files']:
                    organization_results['organized_files'][classification] = []
                
                organization_results['organized_files'][classification].append({
                    'source': str(audio_file.filepath),
                    'target': str(target_path),
                    'metrics': metrics_data
                })
                
            except Exception as e:
                print(f"❌ Failed to process {audio_file.filename}: {e}")
                organization_results['failed_files'].append(str(audio_file.filepath))
        
        # Generate summary
        organization_results['summary'] = self.get_collection_metrics_report()
        
        return organization_results
    
    def _generate_file_hash(self, filepath: Path) -> str:
        """Generate hash of file contents"""
        try:
            hash_md5 = hashlib.md5()
            with open(filepath, 'rb') as f:
                for chunk in iter(lambda: f.read(65536), b""):  # 64KB chunks
                    hash_md5.update(chunk)
            return hash_md5.hexdigest()
        except Exception as e:
            print(f"Hash generation failed for {filepath.name}: {e}")
            return ""
    
    def _estimate_duration(self, filesize: int, format_ext: str) -> Optional[float]:
        """Rough duration estimate based on file size"""
        try:
            if format_ext.lower() == '.wav':
                return filesize / (1.4 * 1024 * 1024) * 10  # ~1.4MB per 10sec
            elif format_ext.lower() == '.mp3':
                return filesize / (1024 * 1024) * 60  # ~1MB per minute
            else:
                return filesize / (1024 * 1024) * 30  # Generic estimate
        except:
            return None
    
    def _find_duplicates_original(self, audio_files: List[AudioFile]) -> Dict[str, List[AudioFile]]:
        """Find exact duplicate files (same hash) - original implementation"""
        hash_groups = defaultdict(list)
        
        for file in audio_files:
            if file.file_hash:  # Only process files with hashes
                hash_groups[file.file_hash].append(file)
        
        # Only return groups with multiple files
        duplicates = {}
        for i, (file_hash, files) in enumerate(hash_groups.items()):
            if len(files) > 1:
                duplicates[f"duplicate_{i+1}"] = files
        
        return duplicates
    
    def find_version_families(self, audio_files: List[AudioFile]) -> Dict[str, List[AudioFile]]:
        """Find files that are versions of the same track"""
        base_groups = defaultdict(list)
        
        for file in audio_files:
            base_name = self._extract_base_name(file.filename)
            base_groups[base_name].append(file)
        
        # Only return groups with multiple versions
        families = {}
        for base_name, files in base_groups.items():
            if len(files) > 1 and self._validate_family(files):
                families[base_name] = files
        
        return families
    
    def _extract_base_name(self, filename: str) -> str:
        """Extract base name removing version indicators"""
        import re
        
        name = Path(filename).stem.lower()
        
        # Remove common version patterns
        patterns = [
            r'v\d+$', r'_v\d+$', r'\(v\d+\)$',  # v2, _v2, (v2)
            r'\d+$', r'_\d+$',  # trailing numbers
            r'\(remix\)$', r'\(final\)$', r'_final$',  # common suffixes
        ]
        
        for pattern in patterns:
            name = re.sub(pattern, '', name)
        
        return name.strip()
    
    def _validate_family(self, files: List[AudioFile]) -> bool:
        """Check if files are likely versions of same track"""
        if len(files) < 2:
            return False
        
        # Check file size similarity (within 50% variation)
        sizes = [f.filesize for f in files]
        size_range = max(sizes) - min(sizes)
        avg_size = sum(sizes) / len(sizes)
        
        return avg_size > 0 and size_range / avg_size <= 0.5
    
    def show_statistics(self, audio_files: List[AudioFile]) -> None:
        """Show basic statistics about the collection"""
        if not audio_files:
            print("No audio files to analyze")
            return
        
        total_size = sum(f.filesize for f in audio_files)
        total_duration = sum(f.estimated_duration or 0 for f in audio_files)
        
        print(f"\n{'='*50}")
        print("COLLECTION STATISTICS")
        print(f"{'='*50}")
        print(f"Total files: {len(audio_files)}")
        print(f"Total size: {total_size / (1024**3):.2f} GB")
        print(f"Estimated duration: {total_duration / 3600:.1f} hours")
        
        # Format breakdown
        formats = {}
        for file in audio_files:
            fmt = file.format
            formats[fmt] = formats.get(fmt, 0) + 1
        
        print(f"\nFormats:")
        for fmt, count in sorted(formats.items()):
            print(f"  {fmt}: {count} files")
        
        # Folder distribution
        folders = {}
        for file in audio_files:
            folder = file.filepath.parent.name
            folders[folder] = folders.get(folder, 0) + 1
        
        print(f"\nTop folders:")
        for folder, count in sorted(folders.items(), key=lambda x: x[1], reverse=True)[:5]:
            print(f"  {folder}: {count} files")
    
    def organize_files(self, audio_files: List[AudioFile], output_dir: Path, dry_run: bool = True, 
                      detect_duplicates: bool = True) -> None:
        """Organize files into a clean directory structure"""
        if not audio_files:
            print("No audio files to organize")
            return
        
        # Create base directories
        organized_dir = output_dir / "Organized_Beats"
        duplicates_dir = output_dir / "Duplicates" if detect_duplicates else None
        versions_dir = output_dir / "Versions_To_Review"
        
        print(f"\n{'='*50}")
        print("ORGANIZATION PLAN")
        print(f"{'='*50}")
        print(f"Output directory: {output_dir}")
        print(f"Organized beats: {organized_dir}")
        if detect_duplicates:
            print(f"True duplicates: {duplicates_dir}")
        print(f"Version families: {versions_dir}")
        
        if dry_run:
            print("\n*** DRY RUN MODE - No files will be moved ***")
            print("NOTE: Version families will be organized into subfolders by track name")
        
        # Only find duplicates if requested and files have hashes
        duplicates = {}
        version_families = {}
        
        if detect_duplicates and any(f.file_hash for f in audio_files):
            duplicates = self._find_duplicates_original(audio_files)
            version_families = self.find_version_families(audio_files)
        else:
            print("Skipping duplicate detection (no hashes or not requested)")
        
        # Separate files into categories
        true_duplicate_files = set()
        version_files = set()
        
        # True duplicates: identical hash
        for files in duplicates.values():
            for file in files[1:]:  # Keep first, mark rest as duplicates
                true_duplicate_files.add(file.filepath)
        
        # Version families: similar names but different content
        for files in version_families.values():
            for file in files:
                if file.filepath not in true_duplicate_files:
                    version_files.add(file.filepath)
        
        # Create organization plan
        move_plan = {
            'organized': {},
            'duplicates': [],
            'version_families': {}  # Track families with their base names
        }
        
        for file in audio_files:
            if file.filepath in true_duplicate_files:
                move_plan['duplicates'].append(file)
            elif file.filepath in version_files:
                # Find which family this file belongs to
                for family_name, family_files in version_families.items():
                    if file in family_files:
                        if family_name not in move_plan['version_families']:
                            move_plan['version_families'][family_name] = []
                        move_plan['version_families'][family_name].append(file)
                        break
            else:
                format_folder = file.format.upper().replace('.', '')
                if format_folder not in move_plan['organized']:
                    move_plan['organized'][format_folder] = []
                move_plan['organized'][format_folder].append(file)
        
        # Show the plan
        print(f"\nORGANIZATION SUMMARY:")
        total_to_move = sum(len(files) for files in move_plan['organized'].values())
        print(f"Files to organize: {total_to_move}")
        if detect_duplicates:
            print(f"True duplicates to move: {len(move_plan['duplicates'])}")
        total_version_files = sum(len(files) for files in move_plan['version_families'].values())
        print(f"Version families (organized by track): {len(move_plan['version_families'])} families, {total_version_files} files")
        
        for format_name, files in move_plan['organized'].items():
            print(f"  {format_name}: {len(files)} files")
        
        if move_plan['version_families']:
            print(f"\nVersion families found:")
            for family_name, files in list(move_plan['version_families'].items())[:5]:  # Show first 5
                print(f"  '{family_name}': {len(files)} versions")
            if len(move_plan['version_families']) > 5:
                print(f"  ... and {len(move_plan['version_families']) - 5} more families")
        
        if not dry_run:
            print(f"\nStarting file organization...")
            
            # Create directories
            organized_dir.mkdir(parents=True, exist_ok=True)
            if duplicates_dir and move_plan['duplicates']:
                duplicates_dir.mkdir(parents=True, exist_ok=True)
            if move_plan['version_families']:
                versions_dir.mkdir(parents=True, exist_ok=True)
            
            # Move organized files
            for format_name, files in move_plan['organized'].items():
                format_dir = organized_dir / format_name
                format_dir.mkdir(exist_ok=True)
                
                for file in files:
                    try:
                        new_path = format_dir / file.filename
                        # Handle filename conflicts
                        counter = 1
                        while new_path.exists():
                            name_part = file.filepath.stem
                            ext_part = file.filepath.suffix
                            new_path = format_dir / f"{name_part}_{counter}{ext_part}"
                            counter += 1
                        
                        import shutil
                        shutil.move(str(file.filepath), str(new_path))
                        print(f"Moved: {file.filename} -> {format_name}/")
                    except Exception as e:
                        print(f"Error moving {file.filename}: {e}")
            
            # Move duplicates if enabled
            if duplicates_dir:
                for file in move_plan['duplicates']:
                    try:
                        new_path = duplicates_dir / file.filename
                        counter = 1
                        while new_path.exists():
                            name_part = file.filepath.stem
                            ext_part = file.filepath.suffix
                            new_path = duplicates_dir / f"{name_part}_dup{counter}{ext_part}"
                            counter += 1
                        
                        import shutil
                        shutil.move(str(file.filepath), str(new_path))
                        print(f"Moved duplicate: {file.filename}")
                    except Exception as e:
                        print(f"Error moving duplicate {file.filename}: {e}")
            
            # Move version files to organized subfolders by family
            for family_name, files in move_plan['version_families'].items():
                # Create family directory under Versions_To_Review
                family_dir = versions_dir / family_name.replace('/', '_').replace('\\', '_')  # Safe folder name
                family_dir.mkdir(parents=True, exist_ok=True)
                
                for file in files:
                    try:
                        new_path = family_dir / file.filename
                        counter = 1
                        while new_path.exists():
                            name_part = file.filepath.stem
                            ext_part = file.filepath.suffix
                            new_path = family_dir / f"{name_part}_v{counter}{ext_part}"
                            counter += 1
                        
                        import shutil
                        shutil.move(str(file.filepath), str(new_path))
                        print(f"Moved version: {file.filename} -> {family_name}/")
                    except Exception as e:
                        print(f"Error moving version {file.filename}: {e}")
            
            print(f"\nOrganization complete!")
            print(f"Check: {output_dir}")
        else:
            print(f"\nTo actually move files, run again with --execute")
    
    def get_collection_stats(self, directory: str) -> Dict:
        """Get basic statistics for a collection of audio files"""
        try:
            path = Path(directory)
            if not path.exists():
                return {'error': 'Directory does not exist'}
            
            # Scan the directory for files
            audio_files = self.scan_directory(path)
            
            if not audio_files:
                return {
                    'total_files': 0,
                    'total_size': 0,
                    'formats': {},
                    'oldest_file': None,
                    'newest_file': None
                }
            
            # Calculate basic statistics
            total_size = sum(f.filesize for f in audio_files)
            formats = {}
            oldest_date = None
            newest_date = None
            oldest_file = None
            newest_file = None
            
            for audio_file in audio_files:
                # Format counts
                ext = audio_file.format.lower()
                formats[ext] = formats.get(ext, 0) + 1
                
                # Date tracking
                if audio_file.modified_date:
                    if oldest_date is None or audio_file.modified_date < oldest_date:
                        oldest_date = audio_file.modified_date
                        oldest_file = audio_file.filename
                    if newest_date is None or audio_file.modified_date > newest_date:
                        newest_date = audio_file.modified_date
                        newest_file = audio_file.filename
            
            return {
                'total_files': len(audio_files),
                'total_size': total_size,
                'formats': formats,
                'oldest_file': oldest_file,
                'newest_file': newest_file,
                'oldest_date': oldest_date.isoformat() if oldest_date else None,
                'newest_date': newest_date.isoformat() if newest_date else None
            }
            
        except Exception as e:
            return {'error': f'Failed to get collection stats: {str(e)}'}
    
    def find_duplicates(self, path_or_files) -> Dict[str, List[AudioFile]]:
        """Find duplicate files from a directory path or list of AudioFile objects"""
        try:
            if isinstance(path_or_files, str):
                # String path provided - scan directory first
                path = Path(path_or_files)
                if not path.exists():
                    return {}
                audio_files = self.scan_directory(path)
            elif isinstance(path_or_files, Path):
                # Path object provided - scan directory first
                if not path_or_files.exists():
                    return {}
                audio_files = self.scan_directory(path_or_files)
            else:
                # List of AudioFile objects provided
                audio_files = path_or_files
            
            return self._find_duplicates_from_files(audio_files)
            
        except Exception as e:
            print(f"Error finding duplicates: {e}")
            return {}
    
    def _find_duplicates_from_files(self, audio_files: List[AudioFile], fingerprints: Dict[str, str] = None) -> Dict[str, List[AudioFile]]:
        """Find duplicate files using audio fingerprints (when available) or fallback to file hashes"""
        if not self.enable_metrics:
            # Fallback to file hash-based duplicate detection
            duplicates = defaultdict(list)
            for audio_file in audio_files:
                duplicates[audio_file.file_hash].append(audio_file)
            return {k: v for k, v in duplicates.items() if len(v) > 1}
        
        # Use audio fingerprint-based duplicate detection
        print("🔍 Analyzing audio fingerprints for duplicate detection...")
        metrics_list = []
        
        # Use provided fingerprints or check cache
        for audio_file in audio_files:
            fingerprint = None
            file_path_str = str(audio_file.filepath)
            
            # Try provided fingerprints first
            if fingerprints and file_path_str in fingerprints:
                fingerprint = fingerprints[file_path_str]
            else:
                # Check if files already have cached fingerprints in database
                cached_metrics = self.metrics_db.get_metrics(audio_file.filepath)
                if cached_metrics and cached_metrics.get('audio_fingerprint'):
                    fingerprint = cached_metrics['audio_fingerprint']
            
            if fingerprint:
                audio_metrics = AudioMetrics(
                    filepath=audio_file.filepath,
                    filename=audio_file.filename,
                    file_size=audio_file.filesize,
                    format=audio_file.format,
                    audio_fingerprint=fingerprint
                )
                metrics_list.append(audio_metrics)
        
        if not metrics_list:
            print("⚠️ No audio fingerprints available, falling back to file hash detection")
            # Fallback to file hash method
            duplicates = defaultdict(list)
            for audio_file in audio_files:
                duplicates[audio_file.file_hash].append(audio_file)
            return {k: v for k, v in duplicates.items() if len(v) > 1}
        
        # Find audio fingerprint duplicates (100% matches only)
        fingerprint_duplicates = self.audio_analyzer.find_audio_duplicates(metrics_list, threshold=99.0)
        
        # Convert back to AudioFile format for compatibility
        converted_duplicates = {}
        for key, metrics_group in fingerprint_duplicates.items():
            audio_file_group = []
            for metrics in metrics_group:
                # Find corresponding AudioFile
                for audio_file in audio_files:
                    if audio_file.filepath == metrics.filepath:
                        audio_file_group.append(audio_file)
                        break
            if len(audio_file_group) > 1:
                converted_duplicates[key] = audio_file_group
        
        print(f"🎯 Found {len(converted_duplicates)} audio fingerprint duplicate groups")
        return converted_duplicates
    
def main():
    """Main CLI interface"""
    parser = argparse.ArgumentParser(
        description="Beat File Organizer - Clean up your music production files",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  %(prog)s scan "C:/Music/Beats"
  %(prog)s duplicates "C:/Music/Beats" 
  %(prog)s stats "C:/Music/Beats"
  %(prog)s organize "C:/Users/username/Desktop" --output "C:/Users/username/Music"
  %(prog)s organize "C:/Users/username/Desktop" --execute
        """
    )
    
    parser.add_argument('command', choices=['scan', 'duplicates', 'stats', 'organize'], 
                       help='Action to perform')
    parser.add_argument('path', help='Directory path to analyze')
    parser.add_argument('--output', help='Output directory for organization (default: current user Music folder)')
    parser.add_argument('--execute', action='store_true',
                       help='Actually move files (default is dry-run)')
    parser.add_argument('--no-recursive', action='store_true',
                       help='Do not scan subdirectories')
    
    args = parser.parse_args()
    
    # Validate path
    path = Path(args.path)
    if not path.exists():
        print(f"Error: Path '{args.path}' does not exist")
        return 1
    
    if not path.is_dir():
        print(f"Error: '{args.path}' is not a directory")
        return 1
    
    # Initialize organizer
    organizer = BeatOrganizer()
    
    try:
        print(f"Beat File Organizer")
        print(f"Command: {args.command}")
        print(f"Path: {path}")
        print(f"{'='*50}")
        
        # Scan files
        recursive = not args.no_recursive
        audio_files = organizer.scan_directory(path, recursive)
        
        if not audio_files:
            print("No audio files found!")
            return 0
        
        # Execute command
        if args.command == 'scan':
            organizer.show_statistics(audio_files)
        
        elif args.command == 'duplicates':
            print(f"\nAnalyzing duplicates...")
            
            # Find exact duplicates
            duplicates = organizer.find_duplicates(audio_files)
            
            if duplicates:
                total_duplicate_files = sum(len(files) for files in duplicates.values())
                space_savings = 0
                
                for files in duplicates.values():
                    max_size = max(f.filesize for f in files)
                    total_size = sum(f.filesize for f in files)
                    space_savings += total_size - max_size
                
                print(f"\nEXACT DUPLICATES FOUND:")
                print(f"Groups: {len(duplicates)}")
                print(f"Files: {total_duplicate_files}")
                print(f"Potential space savings: {space_savings / (1024**2):.1f} MB")
                
                for group_id, files in duplicates.items():
                    print(f"\n{group_id}: {len(files)} identical files")
                    for file in files:
                        size_mb = file.filesize / (1024**2)
                        print(f"  - {file.filename} ({size_mb:.1f} MB)")
                        print(f"    {file.filepath}")
            else:
                print("No exact duplicates found")
            
            # Find version families
            families = organizer.find_version_families(audio_files)
            
            if families:
                print(f"\nVERSION FAMILIES FOUND:")
                print(f"Families: {len(families)}")
                
                for family_name, files in list(families.items())[:10]:  # Show first 10
                    print(f"\n'{family_name}': {len(files)} versions")
                    for file in files:
                        print(f"  - {file.filename}")
                
                if len(families) > 10:
                    print(f"... and {len(families) - 10} more families")
        
        elif args.command == 'stats':
            organizer.show_statistics(audio_files)
        
        elif args.command == 'organize':
            # Determine output directory
            if args.output:
                output_dir = Path(args.output)
            else:
                # Default to user's Music folder
                music_dir = Path.home() / "Music"
                output_dir = music_dir
            
            print(f"Output directory: {output_dir}")
            
            # Check if output directory exists or can be created
            try:
                output_dir.mkdir(parents=True, exist_ok=True)
            except Exception as e:
                print(f"Error: Cannot create output directory {output_dir}: {e}")
                return 1
            
            # Organize files
            dry_run = not args.execute
            organizer.organize_files(audio_files, output_dir, dry_run, detect_duplicates=True)
        
        return 0
        
    except KeyboardInterrupt:
        print("\nOperation cancelled")
        return 1
    except Exception as e:
        print(f"Error: {e}")
        return 1

if __name__ == "__main__":
    sys.exit(main())

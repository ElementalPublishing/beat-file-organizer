#!/usr/bin/env python3
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
import hashlib
import argparse
import sys
from pathlib import Path
from typing import List, Dict, Optional
from dataclasses import dataclass
from collections import defaultdict
from datetime import datetime

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
    """Main Beat File Organizer class"""
    
    SUPPORTED_FORMATS = {'.wav', '.mp3', '.flac', '.aif', '.aiff', '.m4a', '.ogg'}
    
    def __init__(self):
        """Initialize the organizer"""
        self.has_fast_hash = self._check_fast_hash()
    
    def _check_fast_hash(self) -> bool:
        """Check if compiled Cython hash module is available"""
        try:
            import fast_hash
            return True
        except ImportError:
            return False
    
    def scan_directory(self, path: Path, recursive: bool = True, skip_hashing: bool = False) -> List[AudioFile]:
        """Scan directory for audio files"""
        print(f"Scanning {path}{'...' if recursive else ' (non-recursive)...'}")
        
        audio_files = []
        pattern = "**/*" if recursive else "*"
        
        try:
            # Pre-filter by extension for speed
            for filepath in path.glob(pattern):
                if filepath.is_file() and filepath.suffix.lower() in self.SUPPORTED_FORMATS:
                    audio_file = self._analyze_file(filepath, skip_hashing)
                    if audio_file:
                        audio_files.append(audio_file)
                        if len(audio_files) % 100 == 0:
                            print(f"  Found {len(audio_files)} files...")
        except Exception as e:
            print(f"Error scanning: {e}")
        
        print(f"Scan complete: {len(audio_files)} audio files found")
        return audio_files
    
    def _analyze_file(self, filepath: Path, skip_hashing: bool = False) -> Optional[AudioFile]:
        """Analyze a single audio file"""
        try:
            stat = filepath.stat()
            filesize = stat.st_size
            created_date = datetime.fromtimestamp(stat.st_mtime)
            modified_date = datetime.fromtimestamp(stat.st_mtime)
            
            # Skip hashing for basic organization (much faster)
            file_hash = "" if skip_hashing else self._generate_file_hash(filepath)
            
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
    
    def _generate_file_hash(self, filepath: Path) -> str:
        """Generate hash of file contents"""
        # Use fast Cython version if available
        if self.has_fast_hash:
            try:
                import fast_hash
                return fast_hash.fast_file_hash(str(filepath))
            except:
                pass
        
        # Fallback to regular Python
        try:
            hash_md5 = hashlib.md5()
            with open(filepath, 'rb') as f:
                for chunk in iter(lambda: f.read(65536), b""):  # 64KB chunks
                    hash_md5.update(chunk)
            return hash_md5.hexdigest()
        except:
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
    
    def find_duplicates(self, audio_files: List[AudioFile]) -> Dict[str, List[AudioFile]]:
        """Find exact duplicate files (same hash)"""
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
            duplicates = self.find_duplicates(audio_files)
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
  %(prog)s organize "C:/Users/username/Desktop" --execute --fast
        """
    )
    
    parser.add_argument('command', choices=['scan', 'duplicates', 'stats', 'organize'], 
                       help='Action to perform')
    parser.add_argument('path', help='Directory path to analyze')
    parser.add_argument('--output', help='Output directory for organization (default: current user Music folder)')
    parser.add_argument('--execute', action='store_true',
                       help='Actually move files (default is dry-run)')
    parser.add_argument('--fast', action='store_true',
                       help='Fast mode: skip duplicate detection for faster organization')
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
        if args.fast:
            print("Mode: FAST (skipping duplicate detection)")
        if organizer.has_fast_hash:
            print("Optimization: Cython fast hashing available")
        print(f"{'='*50}")
        
        # Scan files
        recursive = not args.no_recursive
        skip_hashing = args.fast and args.command == 'organize'
        audio_files = organizer.scan_directory(path, recursive, skip_hashing)
        
        if not audio_files:
            print("No audio files found!")
            return 0
        
        # Execute command
        if args.command == 'scan':
            organizer.show_statistics(audio_files)
        
        elif args.command == 'duplicates':
            if skip_hashing:
                print("Cannot detect duplicates in fast mode (no hashing)")
                return 1
                
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
            detect_duplicates = not args.fast
            organizer.organize_files(audio_files, output_dir, dry_run, detect_duplicates)
        
        return 0
        
    except KeyboardInterrupt:
        print("\nOperation cancelled")
        return 1
    except Exception as e:
        print(f"Error: {e}")
        return 1

if __name__ == "__main__":
    sys.exit(main())

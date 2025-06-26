# Beat File Organizer
## Installation and Setup

### Prerequisites
- Python 3.8 or higher
- pip (Python package installer)

### Installation

1. **Install Dependencies**
   ```bash
   cd beat-file-organizer
   pip install -r requirements.txt
   ```

2. **Test Installation**
   ```bash
   python test_installation.py
   ```

3. **Basic Usage**
   ```bash
   # Scan a directory
   python cli.py scan "C:/path/to/your/beats" --recursive
   
   # View statistics
   python cli.py stats
   
   # Find duplicates
   python cli.py duplicates
   
   # Search files
   python cli.py search --bpm 120-140 --format .wav
   
   # Export inventory
   python cli.py export my_beats_inventory.json
   ```

### Directory Structure
```
beat-file-organizer/
├── README.md
├── requirements.txt
├── cli.py                 # Command-line interface
├── test_installation.py   # Installation test
├── core/
│   ├── scanner.py         # Audio file scanning and analysis
│   ├── database.py        # Database management
│   └── __init__.py
└── beats.db              # SQLite database (created automatically)
```

### Features

**Current (MVP):**
- Audio file scanning and metadata extraction
- Duplicate detection using audio fingerprinting
- SQLite database for file inventory
- Command-line interface
- Basic search and filtering
- Statistics and reporting

**Planned:**
- GUI desktop application
- Advanced AI-powered organization
- Cloud sync capabilities
- Batch processing tools
- Integration with DAWs

### Supported Audio Formats
- WAV (.wav)
- MP3 (.mp3)  
- FLAC (.flac)
- AIFF (.aif, .aiff)
- M4A (.m4a)
- OGG (.ogg)

### System Requirements
- **Storage:** Minimum 100MB for program + database size depends on music library
- **RAM:** 2GB minimum, 4GB+ recommended for large libraries
- **CPU:** Any modern processor (multi-core recommended for faster analysis)

### Troubleshooting

**Import Errors:**
Make sure all dependencies are installed: `pip install -r requirements.txt`

**Slow Performance:**
- Use SSD storage for database
- Scan smaller directories first
- Consider reducing sample_duration in AudioAnalyzer

**Analysis Errors:**
- Check file permissions
- Ensure audio files are not corrupted
- Verify supported file formats

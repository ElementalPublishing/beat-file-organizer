# Audio Metrics Guide for Producers

This document explains audio analysis metrics from a producer's perspective - what they mean, why they matter, and how to use them in your workflow.

---

## 🔊 **LUFS (Loudness Units relative to Full Scale)**

### **What it is:**
LUFS measures **perceived loudness** - how loud your track actually sounds to human ears, not just peak levels.

### **Why producers care:**
- **Streaming platforms normalize to LUFS targets** - if your track is too loud, they turn it down
- **Spotify: -14 LUFS** - If you master at -10 LUFS, Spotify turns it down 4dB
- **Result:** Your "loud" master sounds quieter than properly mastered tracks

### **Producer reality:**
```
Your master: -8 LUFS (sounds loud in your studio)
Spotify plays it at: -14 LUFS (turned down 6dB!)
Competitor's track: -14 LUFS native
Result: Your track sounds 6dB quieter on Spotify
```

---

## 📊 **Peak vs RMS vs LUFS Comparison**

### **Peak Level (dBFS):**
- **What:** The loudest single sample in your track
- **Producer use:** Prevent digital clipping (keep under 0 dBFS)
- **Reality:** You can have -1 dBFS peak but still sound quiet

### **RMS (Root Mean Square):**
- **What:** Average loudness over time
- **Producer use:** Old-school loudness measurement
- **Problem:** Doesn't match how ears actually perceive loudness

### **LUFS:**
- **What:** Perceptual loudness that matches human hearing
- **Producer use:** Modern standard, matches streaming platforms
- **Why better:** Accounts for frequency weighting (mids sound louder than bass)

---

## 🎵 **Dynamic Range (DR)**

### **What it measures:**
The difference between loud and quiet parts of your track.

### **Producer implications:**
```
High DR (12+): Natural, punchy, musical dynamics
Medium DR (8-12): Commercial but still musical
Low DR (4-8): Compressed, loud but fatiguing
Very Low DR (<4): Brick-walled, lifeless
```

### **Genre context:**
- **Electronic/Pop:** 6-10 DR typical
- **Rock/Metal:** 5-8 DR common
- **Jazz/Classical:** 12+ DR expected
- **Lofi/Ambient:** 8-15 DR varies

---

## 🔊 **True Peak**

### **What it is:**
Peak level after digital-to-analog conversion (what actually comes out of speakers).

### **Why it matters:**
- **Digital peak:** -1 dBFS (looks safe)
- **True peak:** +0.5 dBFS (actually clips!)
- **Cause:** Intersample peaks during D/A conversion

### **Producer fix:**
Use true peak limiting, keep under -1 dBTP for streaming.

---

## 📱 **Streaming Platform Targets**

### **Spotify:** -14 LUFS
- Turns down louder tracks
- Quiet tracks stay quiet (no upward normalization)
- **Sweet spot:** -14 to -16 LUFS

### **Apple Music:** -16 LUFS  
- Similar to Spotify but slightly quieter target
- **Sweet spot:** -16 to -18 LUFS

### **YouTube:** -13 LUFS
- Slightly louder than Spotify
- **Sweet spot:** -13 to -15 LUFS

### **SoundCloud:** No normalization
- Loudness war still exists
- **Strategy:** Master for other platforms, upload loud version here if needed

---

## 🎯 **Practical Producer Workflow**

### **During Production:**
- Don't worry about loudness, focus on dynamics and musicality
- Keep peaks well below 0 dBFS to avoid clipping

### **During Mixing:**
- Peak levels around -6 to -12 dBFS (leave headroom for mastering)
- Check RMS for consistency between sections
- Focus on balance and frequency content

### **During Mastering:**
- Target -14 to -16 LUFS integrated
- Keep true peaks under -1 dBTP
- Maintain at least 8 DR if possible
- A/B test against reference tracks

### **Quality Check Examples:**
```
Good master: -15 LUFS, -0.8 dBTP, 9 DR
Loud but musical: -12 LUFS, -0.5 dBTP, 7 DR  
Over-compressed: -8 LUFS, 0 dBTP, 4 DR
Needs mastering: -20 LUFS, -6 dBFS, 15 DR
```

---

## 🛠️ **Tools & Measurement**

### **FFmpeg Analysis Commands:**
```bash
# LUFS analysis
ffmpeg -i track.wav -af loudnorm=print_format=json -f null -

# Peak/RMS analysis  
ffmpeg -i track.wav -af astats=metadata=1 -f null -

# Combined loudness analysis
ffmpeg -i track.wav -af loudnorm=print_format=json:dual_mono=true,astats -f null -

# Spectral analysis
ffmpeg -i track.wav -af "showspectrumpic=s=1024x512" spectrum.png

# Audio fingerprinting for duplicate detection
ffmpeg -i track.wav -af "chromaprint=algorithm=1" -f null -
```

### **Advanced Analysis Tools:**
```bash
# BPM detection (requires aubio)
aubiotempo track.wav

# Key detection (requires aubio)
aubiokey track.wav

# Comprehensive analysis (requires essentia)
essentia_streaming_extractor_music track.wav track_analysis.json
```

### **Professional Tools:**
- **LUFS meters:** TC Electronic Clarity M, Waves WLM Plus
- **DR meters:** TT Dynamic Range Meter, foobar2000 DR plugin
- **Analysis software:** iZotope Insight, MeldaProduction MAnalyzer

---

## 🎵 **Practical Applications**

### **File Organization:**
- **Masters:** -14 to -16 LUFS, 8+ DR, proper true peak limiting
- **Demos:** Wide LUFS range, often higher DR, may have clipping
- **Stems:** Quiet levels (-20 to -30 LUFS), high DR for mixing headroom

### **Quality Assessment:**
- **Professional:** Consistent LUFS, controlled true peaks, appropriate DR for genre
- **Amateur:** Inconsistent levels, digital clipping, over-compression
- **Needs work:** Too quiet, too loud, or inappropriate dynamic range

### **Workflow Optimization:**
- **Sort by LUFS:** Find tracks that need remastering
- **Group by DR:** Separate heavily compressed from dynamic tracks
- **Filter by true peak:** Identify tracks with potential clipping issues

---

## 🎵 **BPM (Beats Per Minute) Analysis**

### **What it is:**
The tempo of your track - how many beats occur per minute.

### **Why producers care:**
- **DJ mixing:** Essential for beatmatching and seamless transitions
- **Workflow organization:** Group tracks by energy level and mixing compatibility
- **Creative possibilities:** Find tracks that work together rhythmically
- **Genre classification:** Different genres have typical BPM ranges

### **Genre BPM Ranges:**
```
Trap/Hip-Hop: 60-90 BPM (feels slow but often double-time)
House: 120-130 BPM (classic four-on-the-floor)
Techno: 120-150 BPM (driving, hypnotic)
Drum & Bass: 160-180 BPM (fast breakbeats)
Dubstep: 140 BPM (half-time feel makes it sound slower)
```

### **Organization Strategy:**
- **Exact BPM:** For precise DJ mixing
- **BPM ranges:** Slow (<100), Medium (100-140), Fast (>140)
- **Half-time relationships:** 87 BPM hip-hop mixes with 174 BPM D&B

---

## 🎼 **Musical Key Detection**

### **What it is:**
The tonal center of your track (C major, A minor, F# minor, etc.).

### **Why producers care:**
- **Harmonic mixing:** Keys that work together sound more musical
- **DJ sets:** Smooth key transitions prevent jarring harmonic clashes
- **Remixing:** Find tracks in compatible keys for mashups
- **Playlist curation:** Create musically coherent collections

### **Key Compatibility (Camelot Wheel):**
```
Perfect matches: Same key (8A with 8A)
Safe transitions: Adjacent numbers (8A to 9A or 7A)
Energy changes: Same number, different letter (8A to 8B)
Creative jumps: +/- 5 semitones for tension/release
```

### **Practical Examples:**
- **C major (8B)** works with **A minor (8A)** - relative keys
- **F major (7B)** flows to **C major (8B)** - adjacent keys
- **G major (9B)** creates energy with **C major (8B)** - fifth relationship

---

## 📊 **Spectral Analysis Metrics**

### **Spectral Centroid (Brightness):**
- **What:** Where most energy sits in the frequency spectrum
- **High centroid:** Bright, crispy sounds (cymbals, synth leads)
- **Low centroid:** Dark, warm sounds (bass, pads, vocals)
- **Use:** Match tracks with similar tonal character

### **Spectral Rolloff:**
- **What:** Frequency below which 85% of energy exists
- **Producer use:** Identify bass-heavy vs. treble-heavy tracks
- **Organization:** Group tracks by frequency balance

### **Zero Crossing Rate:**
- **What:** How often the audio waveform crosses zero
- **High rate:** Percussive, noisy content (drums, distortion)
- **Low rate:** Tonal, melodic content (vocals, synths)
- **Use:** Distinguish between rhythmic and melodic elements

---

## 🔧 **Quality and Technical Metrics**

### **Bit Depth & Sample Rate:**
```
24-bit/48kHz: Professional production standard
16-bit/44.1kHz: CD quality, streaming ready
24-bit/96kHz: High-end recording, mixing
32-bit float: Digital mixing format
```

### **File Format Priority:**
1. **WAV/AIFF:** Uncompressed, perfect for production
2. **FLAC:** Lossless compression, good for archival
3. **MP3 320kbps:** Acceptable for reference, demos
4. **MP3 <320kbps:** Avoid for production use

### **Clipping Detection:**
- **Digital clipping:** Waveform hits 0 dBFS ceiling
- **Intersample peaks:** True peak clipping during playback
- **Producer impact:** Harsh distortion, loss of punch
- **Organization use:** Flag damaged files for remastering

---

## 📁 **Advanced Organization Strategies**

### **Multi-Dimensional Sorting:**
```
/organized_beats/
├── by_genre_and_bpm/
│   ├── house_120-130/
│   ├── trap_70-90/
│   └── dnb_160-180/
├── by_key_and_energy/
│   ├── c_major_high_energy/
│   ├── a_minor_chill/
│   └── unknown_key/
├── by_quality_tier/
│   ├── mastered_professional/
│   ├── mixed_needs_master/
│   ├── demo_rough/
│   └── damaged_remaster_needed/
└── by_compatibility/
    ├── dj_ready_keyed_bpm/
    ├── stems_production/
    └── reference_only/
```

### **Smart Duplicate Detection:**
Beyond filename matching:
- **Audio fingerprinting:** Identify same content, different names
- **Version detection:** Find different masters of same track
- **Stem relationships:** Connect stems to their full mixes
- **Quality comparison:** Keep highest quality version

### **Workflow Integration Scoring:**
```python
def calculate_workflow_score(metrics):
    score = 0
    
    # Technical quality (40%)
    if metrics['bit_depth'] >= 24: score += 20
    if metrics['sample_rate'] >= 48000: score += 20
    
    # Loudness compliance (30%)
    if -16 <= metrics['lufs'] <= -12: score += 30
    elif -20 <= metrics['lufs'] <= -10: score += 20
    
    # Dynamic range (20%)
    if metrics['dr'] >= 8: score += 20
    elif metrics['dr'] >= 6: score += 15
    
    # Metadata completeness (10%)
    if metrics['bpm_detected']: score += 5
    if metrics['key_detected']: score += 5
    
    return score  # 0-100 scale
```

---

## � **Implementation Roadmap**

### **Phase 1 - Current (v0.2.0): Core Metrics**
- ✅ LUFS measurement with FFmpeg
- ✅ Dynamic range calculation
- ✅ True peak detection
- ✅ Basic file quality assessment
- 🎯 **Next:** BPM detection integration

### **Phase 2 - v0.3.0: Musical Intelligence**
- 🔄 BPM detection with aubio/essentia
- 🔄 Musical key detection
- 🔄 Enhanced duplicate detection via audio fingerprinting
- 🔄 Harmonic compatibility matching

### **Phase 3 - v0.4.0: Advanced Analysis**
- ⏳ Spectral feature extraction
- ⏳ Energy level classification
- ⏳ Genre detection based on audio features
- ⏳ Smart quality scoring system

### **Phase 4 - v0.5.0: AI-Powered Organization**
- ⏳ Machine learning for style classification
- ⏳ Automatic playlist generation by compatibility
- ⏳ Predictive organization suggestions
- ⏳ Cloud-based analysis for large libraries

### **Performance Considerations:**
- **Caching:** Store computed metrics in SQLite database
- **Batch processing:** Analyze multiple files simultaneously
- **Progressive analysis:** Start with fast metrics, add detailed analysis on demand
- **Background processing:** Analyze during idle time

---

## �🔍 **Beat File Organizer Integration**

### **Automatic Classification:**
```python
def classify_track_comprehensive(metrics):
    # Quality assessment
    if (metrics['lufs'] between -16 and -12 and 
        metrics['true_peak'] < -1 and 
        metrics['dr'] >= 8 and
        metrics['bit_depth'] >= 24):
        quality = "professional_master"
    elif metrics['lufs'] < -20 or metrics['dr'] > 15:
        quality = "needs_mastering"
    elif metrics['true_peak'] > -0.5 or metrics['dr'] < 5:
        quality = "over_processed"
    else:
        quality = "good_mix"
    
    # Musical classification
    if metrics['bpm'] and metrics['key']:
        musical_class = "dj_ready"
    elif metrics['bpm']:
        musical_class = "tempo_known"
    else:
        musical_class = "analysis_needed"
    
    # Energy level
    if metrics['rms_energy'] > -12:
        energy = "high_energy"
    elif metrics['rms_energy'] > -18:
        energy = "medium_energy"
    else:
        energy = "low_energy"
    
    return {
        'quality': quality,
        'musical': musical_class,
        'energy': energy,
        'workflow_score': calculate_workflow_score(metrics)
    }
```

### **Smart Organization Examples:**
```
# Example 1: DJ-focused organization
track_128bpm_aminor_professional.wav → /dj_ready/a_minor/medium_tempo/
track_130bpm_cmajor_needs_master.wav → /needs_work/mastering_required/

# Example 2: Production workflow
stem_kick_24bit_clean.wav → /stems/drums/high_quality/
master_compressed_poor_dr.wav → /masters/needs_remaster/

# Example 3: Genre and compatibility
house_track_125bpm_gmajor.wav → /house/125bpm/g_major/
compatible_tracks: [124bpm_gmajor, 126bpm_dmajor, 125bpm_eminor]
```

### **Organization Suggestions:**
- **By Quality Tier:** 
  - `Masters/` (professional, streaming-ready)
  - `Mixes/` (good quality, may need mastering)
  - `Demos/` (rough, for reference only)
  - `Damaged/` (clipped, needs remastering)

- **By Musical Compatibility:**
  - `DJ_Ready/` (BPM + key detected, good quality)
  - `Production_Stems/` (high quality, analysis complete)
  - `Reference_Only/` (low quality or incomplete analysis)

- **By Workflow Stage:**
  - `Streaming_Ready/` (LUFS compliant, proper peaks)
  - `Mastering_Queue/` (mixed but needs loudness treatment)
  - `Mixing_Queue/` (stems or rough mixes)

### **Practical Workflow Integration:**
1. **Scan Phase:** Extract basic metrics (LUFS, peaks, format)
2. **Analyze Phase:** Add musical metrics (BPM, key) for priority files
3. **Organize Phase:** Sort based on combined quality and musical scores
4. **Preview Phase:** Display all metrics in dashboard for informed decisions

### **Real-World Example:**
```
File: "untitled_beat_final_v3.wav"
Analysis: -8 LUFS, 4 DR, 125 BPM, C major, 24-bit
Classification: "over_processed" (too loud, low DR)
Suggestion: Move to /needs_remaster/house_125bpm/
Action: Flag for quieter remaster, keep for DJ version
```

---

## 📊 **Metric Comparison & Analysis Tools**

### **Quality Assessment Matrix:**
```python
def analyze_track_issues(metrics):
    issues = []
    recommendations = []
    
    # Volume Issues
    if metrics['lufs'] < -23:
        issues.append("TOO QUIET - Needs significant level boost")
        recommendations.append("Increase gain by +6dB minimum before mastering")
    elif metrics['lufs'] < -20:
        issues.append("Quiet - May need mastering")
        recommendations.append("Apply gentle compression and limiting")
    elif metrics['lufs'] > -8:
        issues.append("TOO LOUD - Over-compressed")
        recommendations.append("Reduce limiting, increase dynamic range")
    elif metrics['lufs'] > -12:
        issues.append("Loud - May sound fatiguing")
        recommendations.append("Consider quieter master for streaming")
    
    # Clipping Issues
    if metrics['true_peak'] > 0:
        issues.append("CLIPPING - Digital distortion present")
        recommendations.append("URGENT: Apply true peak limiting below -1dBTP")
    elif metrics['true_peak'] > -0.5:
        issues.append("Peak Warning - Close to clipping")
        recommendations.append("Apply stricter peak limiting for safety")
    
    # Dynamic Range Issues
    if metrics['dr'] < 4:
        issues.append("BRICK-WALLED - No dynamics left")
        recommendations.append("Reduce compression/limiting significantly")
    elif metrics['dr'] < 6:
        issues.append("Over-compressed - Limited dynamics")
        recommendations.append("Back off compression, preserve transients")
    elif metrics['dr'] > 20:
        issues.append("Unmastered - Too much dynamic range")
        recommendations.append("Apply mastering chain for consistency")
    
    # Technical Quality Issues
    if metrics['bit_depth'] < 24:
        issues.append("Low bit depth - May have noise floor issues")
        recommendations.append("Use 24-bit for production, 16-bit only for final delivery")
    
    if metrics['sample_rate'] < 44100:
        issues.append("Low sample rate - Frequency range limited")
        recommendations.append("Record/mix at 48kHz minimum")
    
    return {
        'issues': issues,
        'recommendations': recommendations,
        'overall_score': calculate_overall_quality_score(metrics)
    }

def calculate_overall_quality_score(metrics):
    score = 100
    
    # Penalize volume issues
    if metrics['lufs'] < -23 or metrics['lufs'] > -8:
        score -= 30
    elif metrics['lufs'] < -20 or metrics['lufs'] > -12:
        score -= 15
    
    # Penalize clipping heavily
    if metrics['true_peak'] > 0:
        score -= 40
    elif metrics['true_peak'] > -0.5:
        score -= 20
    
    # Penalize dynamic range issues
    if metrics['dr'] < 4:
        score -= 25
    elif metrics['dr'] < 6:
        score -= 15
    elif metrics['dr'] > 20:
        score -= 10
    
    # Reward technical quality
    if metrics['bit_depth'] >= 24:
        score += 5
    if metrics['sample_rate'] >= 48000:
        score += 5
    
    return max(0, score)
```

### **Track Classification System:**
```python
def classify_track_by_metrics(metrics):
    analysis = analyze_track_issues(metrics)
    
    # Determine primary classification
    if analysis['overall_score'] >= 85:
        classification = "STREAMING_READY"
        folder = "masters/streaming_ready"
    elif analysis['overall_score'] >= 70:
        classification = "GOOD_QUALITY"
        folder = "masters/good_quality"
    elif analysis['overall_score'] >= 50:
        classification = "NEEDS_WORK"
        folder = "needs_mastering"
    else:
        classification = "MAJOR_ISSUES"
        folder = "damaged/needs_repair"
    
    # Specific issue-based classification
    if metrics['true_peak'] > 0:
        classification = "CLIPPED"
        folder = "damaged/clipped"
    elif metrics['lufs'] < -23:
        classification = "TOO_QUIET" 
        folder = "needs_mastering/too_quiet"
    elif metrics['lufs'] > -8:
        classification = "TOO_LOUD"
        folder = "needs_mastering/over_compressed"
    elif metrics['dr'] < 4:
        classification = "BRICK_WALLED"
        folder = "damaged/over_limited"
    
    return {
        'classification': classification,
        'suggested_folder': folder,
        'issues': analysis['issues'],
        'recommendations': analysis['recommendations']
    }
```

### **Batch Analysis for Large Collections:**
```python
def analyze_collection(file_list):
    results = {
        'streaming_ready': [],
        'too_quiet': [],
        'too_loud': [],
        'clipped': [],
        'over_compressed': [],
        'needs_mastering': [],
        'technical_issues': [],
        'summary_stats': {}
    }
    
    all_lufs = []
    all_dr = []
    
    for file_path in file_list:
        metrics = extract_audio_metrics(file_path)
        classification = classify_track_by_metrics(metrics)
        
        # Sort into categories
        if 'CLIPPED' in classification['classification']:
            results['clipped'].append(file_path)
        elif 'TOO_QUIET' in classification['classification']:
            results['too_quiet'].append(file_path)
        elif 'TOO_LOUD' in classification['classification']:
            results['too_loud'].append(file_path)
        elif 'BRICK_WALLED' in classification['classification']:
            results['over_compressed'].append(file_path)
        elif 'STREAMING_READY' in classification['classification']:
            results['streaming_ready'].append(file_path)
        else:
            results['needs_mastering'].append(file_path)
        
        # Collect stats
        all_lufs.append(metrics['lufs'])
        all_dr.append(metrics['dr'])
    
    # Generate summary statistics
    results['summary_stats'] = {
        'total_files': len(file_list),
        'streaming_ready_percent': len(results['streaming_ready']) / len(file_list) * 100,
        'clipped_percent': len(results['clipped']) / len(file_list) * 100,
        'average_lufs': sum(all_lufs) / len(all_lufs),
        'average_dr': sum(all_dr) / len(all_dr),
        'loudest_track': min(all_lufs),
        'quietest_track': max(all_lufs),
        'most_dynamic': max(all_dr),
        'least_dynamic': min(all_dr)
    }
    
    return results
```

---

## 🚨 **Problem Detection & Solutions**

### **Common Issues & Quick Fixes:**

#### **🔴 CLIPPED TRACKS (True Peak > 0 dBFS)**
```
Problem: Digital distortion, harsh sound
Detection: true_peak > 0
Priority: CRITICAL - Fix immediately
Solution: Re-master with proper peak limiting
Command: Apply -1dBTP limiting in mastering chain
```

#### **🟡 TOO LOUD (LUFS > -8)**
```
Problem: Over-compressed, fatiguing, turns down on streaming
Detection: lufs > -8 AND dr < 6
Priority: HIGH - Streaming platforms will turn down
Solution: Create quieter master with more dynamics
Target: -14 LUFS for streaming platforms
```

#### **🟡 TOO QUIET (LUFS < -23)**
```
Problem: Sounds weak compared to other tracks
Detection: lufs < -23
Priority: MEDIUM - Needs level increase
Solution: Apply gain/compression in mastering
Target: Bring to -16 to -14 LUFS range
```

#### **🟠 BRICK-WALLED (DR < 4)**
```
Problem: No dynamics, lifeless sound
Detection: dr < 4
Priority: MEDIUM - Musical quality affected
Solution: Re-mix with less compression/limiting
Target: Minimum 6 DR, ideally 8+ DR
```

#### **🟢 UNMASTERED (DR > 20, LUFS < -20)**
```
Problem: Inconsistent levels, needs polish
Detection: dr > 20 AND lufs < -20
Priority: LOW - Good source material
Solution: Apply mastering chain
Target: 8-12 DR, -16 to -14 LUFS
```

### **Metric Comparison Dashboard:**
```
TRACK QUALITY REPORT
====================

📊 VOLUME ANALYSIS:
   Streaming Ready (-16 to -12 LUFS): 45 files (32%)
   Too Loud (> -8 LUFS): 23 files (16%) ⚠️
   Too Quiet (< -23 LUFS): 12 files (8%) ⚠️
   
🔊 DYNAMIC RANGE:
   Musical (8+ DR): 67 files (48%)
   Compressed (4-8 DR): 52 files (37%)
   Brick-walled (< 4 DR): 21 files (15%) ⚠️
   
⚡ CLIPPING ISSUES:
   Clean (< -1 dBTP): 118 files (84%)
   Warning (-0.5 to -1 dBTP): 15 files (11%)
   CLIPPED (> 0 dBTP): 7 files (5%) 🚨
   
🎯 RECOMMENDED ACTIONS:
   1. Fix 7 clipped tracks immediately
   2. Remaster 23 over-loud tracks for streaming
   3. Master 12 quiet tracks for consistency
   4. Consider re-mixing 21 brick-walled tracks
```

### **Smart Organization Rules:**
```python
ORGANIZATION_RULES = {
    # Critical Issues First
    'URGENT_REPAIR': {
        'condition': lambda m: m['true_peak'] > 0,
        'folder': '00_URGENT_CLIPPED',
        'action': 'Fix immediately - digital distortion present'
    },
    
    # Quality Tiers
    'STREAMING_MASTERS': {
        'condition': lambda m: -16 <= m['lufs'] <= -12 and m['true_peak'] < -1 and m['dr'] >= 8,
        'folder': '01_MASTERS_StreamingReady',
        'action': 'Ready for release'
    },
    
    'LOUD_MASTERS': {
        'condition': lambda m: -12 <= m['lufs'] <= -8 and m['true_peak'] < -1,
        'folder': '02_MASTERS_Loud',
        'action': 'Good for DJ use, may need quiet version for streaming'
    },
    
    'NEEDS_MASTERING': {
        'condition': lambda m: m['lufs'] < -20 or m['dr'] > 15,
        'folder': '03_NEEDS_Mastering',
        'action': 'Apply mastering chain for consistency'
    },
    
    'OVER_COMPRESSED': {
        'condition': lambda m: m['dr'] < 6,
        'folder': '04_DAMAGED_OverCompressed',
        'action': 'Consider re-mixing with less compression'
    },
    
    # Technical Issues
    'LOW_QUALITY': {
        'condition': lambda m: m['bit_depth'] < 24 or m['sample_rate'] < 44100,
        'folder': '05_TECHNICAL_LowQuality',
        'action': 'Acceptable for reference only'
    }
}
```

### **Comparative Analysis Tools:**
```python
def compare_versions(file_list):
    """Compare different versions/masters of tracks"""
    for base_name in get_similar_filenames(file_list):
        versions = find_versions(base_name, file_list)
        
        if len(versions) > 1:
            print(f"\n🎵 VERSIONS FOUND: {base_name}")
            
            for version in versions:
                metrics = extract_audio_metrics(version)
                classification = classify_track_by_metrics(metrics)
                
                print(f"   📁 {version}")
                print(f"      LUFS: {metrics['lufs']:.1f} | DR: {metrics['dr']} | Peak: {metrics['true_peak']:.1f}")
                print(f"      Quality: {classification['classification']}")
                print(f"      Issues: {', '.join(classification['issues']) or 'None'}")
            
            # Recommend best version
            best_version = select_best_version(versions)
            print(f"   ✅ RECOMMENDED: {best_version}")

def find_outliers(metrics_list):
    """Find tracks that don't fit normal patterns"""
    lufs_values = [m['lufs'] for m in metrics_list]
    dr_values = [m['dr'] for m in metrics_list]
    
    # Statistical outliers
    lufs_mean = statistics.mean(lufs_values)
    lufs_std = statistics.stdev(lufs_values)
    
    outliers = []
    for i, metrics in enumerate(metrics_list):
        if abs(metrics['lufs'] - lufs_mean) > 2 * lufs_std:
            outliers.append({
                'file': metrics['filename'],
                'issue': 'LUFS outlier',
                'value': metrics['lufs'],
                'expected': f"{lufs_mean:.1f} ± {lufs_std:.1f}"
            })
    
    return outliers
```

---

## 📈 **Actionable Insights & Reports**

### **Weekly Collection Health Report:**
```
BEAT COLLECTION HEALTH REPORT
==============================
Analyzed: 140 files | Total Size: 2.3 GB

🎯 QUALITY SUMMARY:
   Ready for Release: 45 files (32%) ✅
   Needs Attention: 95 files (68%) ⚠️

🚨 CRITICAL ISSUES (Fix First):
   • 7 tracks are clipped (digital distortion)
   • 23 tracks too loud for streaming platforms
   • 21 tracks over-compressed (no dynamics)

📊 COLLECTION STATISTICS:
   Average LUFS: -15.2 (Good for streaming)
   Average DR: 7.8 (Acceptable compression)
   Clipping Rate: 5% (Industry standard: <1%)

🎵 RECOMMENDED WORKFLOW:
   1. Fix clipped tracks immediately
   2. Create streaming masters for over-loud tracks  
   3. Master quiet/unmastered tracks
   4. Archive low-quality duplicates

💡 NEXT ACTIONS:
   • Focus mastering session on 35 priority tracks
   • Set up streaming-ready folder system
   • Consider re-mixing 21 over-compressed tracks
```

This comprehensive analysis system transforms raw metrics into actionable insights, helping you quickly identify problem tracks, prioritize fixes, and maintain a high-quality beat collection.

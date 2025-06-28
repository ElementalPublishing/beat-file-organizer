#!/usr/bin/env python3
"""
🚀 BEAT ORGANIZER: THE PRODUCER'S LIBERATION ARMY
Revolutionary Web API - Async Architecture for Ultimate Performance

Born from the enemy's $5.53 insulting offer.
This is the NEW FastAPI backend that eliminates global state terrorism,
threading anarchy, and performance bottlenecks. Built for VICTORY!
"""

import asyncio
import json
import uuid
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional, Any, AsyncGenerator
from contextlib import asynccontextmanager

from fastapi import FastAPI, HTTPException, BackgroundTasks, WebSocket, WebSocketDisconnect, Request
from fastapi.staticfiles import StaticFiles
from fastapi.responses import HTMLResponse, FileResponse
from fastapi.middleware.cors import CORSMiddleware
from fastapi.templating import Jinja2Templates
from pydantic import BaseModel
# import redis.asyncio as redis  # Optional - for future advanced features

# Import our revolutionary core modules
from beat_organizer import BeatOrganizer, AudioFile
from audio_metrics import AudioAnalyzer, AudioMetrics, MetricsDatabase

# 🎯 REQUEST/RESPONSE MODELS (No more global chaos!)
class ScanRequest(BaseModel):
    directory: str

class AnalyzeRequest(BaseModel):
    filepath: str

class WaveformRequest(BaseModel):
    filepath: str
    width: int = 800
    height: int = 120

class TaskStatus(BaseModel):
    task_id: str
    status: str  # "pending", "running", "completed", "failed"
    progress: float = 0.0
    current_file: str = ""
    total_files: int = 0
    completed_files: int = 0
    result: Optional[Dict] = None
    error: Optional[str] = None

# 🛡️ REVOLUTIONARY TASK MANAGER (Destroys global state terrorism!)
class TaskManager:
    def __init__(self):
        self.tasks: Dict[str, TaskStatus] = {}
        self.organizer = BeatOrganizer(enable_metrics=True)
        self.audio_analyzer = AudioAnalyzer()
        self.metrics_db = MetricsDatabase()
        
    async def create_task(self, task_type: str) -> str:
        """Create a new task with unique ID - NO GLOBAL STATE!"""
        task_id = str(uuid.uuid4())
        self.tasks[task_id] = TaskStatus(
            task_id=task_id,
            status="pending"
        )
        return task_id
    
    def get_task(self, task_id: str) -> Optional[TaskStatus]:
        """Get task status safely"""
        return self.tasks.get(task_id)
    
    async def update_task_progress(self, task_id: str, progress: float, current_file: str = "", 
                                   completed_files: int = 0, total_files: int = 0):
        """Thread-safe task progress updates"""
        if task_id in self.tasks:
            task = self.tasks[task_id]
            task.progress = progress
            task.current_file = current_file
            task.completed_files = completed_files
            task.total_files = total_files
            task.status = "running"
            
            # Debug logging
            print(f"📊 Task {task_id}: {progress:.1f}% - {current_file}")
        else:
            print(f"⚠️ Task {task_id} not found for progress update")
    
    async def complete_task(self, task_id: str, result: Dict):
        """Mark task as completed with results"""
        if task_id in self.tasks:
            task = self.tasks[task_id]
            task.status = "completed"
            task.progress = 100.0
            task.result = result
    
    async def fail_task(self, task_id: str, error: str):
        """Mark task as failed with error"""
        if task_id in self.tasks:
            task = self.tasks[task_id]
            task.status = "failed"
            task.error = error

# 🚀 WEBSOCKET CONNECTION MANAGER (Real-time liberation!)
class ConnectionManager:
    def __init__(self):
        self.active_connections: List[WebSocket] = []
    
    async def connect(self, websocket: WebSocket):
        await websocket.accept()
        self.active_connections.append(websocket)
    
    def disconnect(self, websocket: WebSocket):
        if websocket in self.active_connections:
            self.active_connections.remove(websocket)
    
    async def broadcast_progress(self, task_id: str, progress_data: Dict):
        """Broadcast real-time progress to all connected clients"""
        message = {
            "type": "progress_update",
            "task_id": task_id,
            "data": progress_data
        }
        
        # Remove disconnected clients
        disconnected = []
        for connection in self.active_connections:
            try:
                await connection.send_json(message)
            except:
                disconnected.append(connection)
        
        for conn in disconnected:
            self.disconnect(conn)

# 🏗️ INITIALIZE THE LIBERATION ARMY
task_manager = TaskManager()
connection_manager = ConnectionManager()

# 🎯 FASTAPI APP WITH REVOLUTIONARY ARCHITECTURE
app = FastAPI(
    title="Beat Organizer: Producer's Liberation Army",
    description="Revolutionary audio organization for the war against mediocrity",
    version="2.0.0"
)

# Enable CORS for cross-origin requests
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# 🎯 WEBSOCKET FOR REAL-TIME COMMUNICATION
@app.websocket("/ws/progress")
async def websocket_endpoint(websocket: WebSocket):
    await connection_manager.connect(websocket)
    try:
        while True:
            # Keep connection alive and listen for client messages
            data = await websocket.receive_text()
            # Echo back or handle client requests
            await websocket.send_text(f"Echo: {data}")
    except WebSocketDisconnect:
        connection_manager.disconnect(websocket)

# 🏥 HEALTH CHECK ENDPOINT
@app.get("/api/health")
async def health_check():
    """Check system health and dependencies"""
    try:
        ffmpeg_available = task_manager.audio_analyzer.check_ffmpeg()
        db_healthy = task_manager.metrics_db.is_healthy()
        
        return {
            "success": True,
            "status": "healthy",
            "dependencies": {
                "ffmpeg": ffmpeg_available,
                "database": db_healthy
            },
            "message": "🎵 Producer's Liberation Army ready for battle!"
        }
    except Exception as e:
        return {
            "success": False,
            "status": "unhealthy", 
            "error": str(e),
            "message": "⚠️ System check failed"
        }

# 🎯 DIRECTORY SCANNING WITH ASYNC BACKGROUND PROCESSING
@app.post("/api/scan")
async def start_scan(request: ScanRequest, background_tasks: BackgroundTasks):
    """Start directory scan as background task"""
    try:
        task_id = await task_manager.create_task("scan")
        
        # Start background scan
        background_tasks.add_task(
            background_scan_task,
            task_id,
            request.directory
        )
        
        return {
            "success": True,
            "task_id": task_id,
            "message": f"🔍 Scan started for {request.directory}"
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

async def background_scan_task(task_id: str, directory: str):
    """Background task for directory scanning - NO GLOBAL STATE!"""
    try:
        # Create a progress update queue to handle async updates safely
        progress_queue = asyncio.Queue()
        
        # Progress callback for real-time updates (synchronous version)
        def progress_callback(phase: str, progress: float, current_file: str = "", 
                              completed: int = 0, total: int = 0):
            # Put progress update in queue (thread-safe)
            try:
                progress_queue.put_nowait({
                    "phase": phase,
                    "progress": progress,
                    "current_file": current_file,
                    "completed_files": completed,
                    "total_files": total
                })
            except asyncio.QueueFull:
                pass  # Skip if queue is full to avoid blocking
        
        # Start progress processor task
        progress_processor = asyncio.create_task(
            process_progress_updates(task_id, progress_queue)
        )
        
        # Execute the scan with our revolutionary architecture
        result = await asyncio.to_thread(
            execute_comprehensive_scan,
            directory,
            progress_callback
        )
        
        # Signal end of progress updates
        await progress_queue.put({"end": True})
        await progress_processor
        
        await task_manager.complete_task(task_id, result)
        
        # Final broadcast
        await connection_manager.broadcast_progress(task_id, {
            "phase": "completed",
            "progress": 100.0,
            "result": result
        })
        
    except Exception as e:
        await task_manager.fail_task(task_id, str(e))
        await connection_manager.broadcast_progress(task_id, {
            "phase": "failed",
            "error": str(e)
        })

def execute_comprehensive_scan(directory: str, progress_callback) -> Dict:
    """Execute the 7-phase comprehensive scan with progress tracking"""
    
    print(f"🚀 Starting comprehensive scan of {directory}")
    
    # Phase 1: Discovery (0-12%)
    progress_callback("discovery", 5.0, "Phase 1: Discovering audio files...")
    audio_files = task_manager.organizer.scan_directory(Path(directory))
    total_files = len(audio_files)
    
    if total_files == 0:
        return {
            "success": True,
            "directory": directory,
            "total_files": 0,
            "files": [],
            "duplicate_groups": [],
            "message": "No audio files found"
        }
    
    progress_callback("discovery", 12.0, f"Found {total_files} audio files", 0, total_files)
    
    # Phase 2: Fingerprinting (12-25%)
    progress_callback("fingerprinting", 15.0, "Phase 2: Generating audio fingerprints...")
    
    file_paths = [Path(f.filepath) for f in audio_files]
    fingerprints = task_manager.audio_analyzer.generate_fingerprints_bulk(
        file_paths,
        lambda i, total, current: progress_callback(
            "fingerprinting", 
            12.0 + (i / total) * 13.0,
            f"🔑 Fingerprinting: {current}",
            i, total
        )
    )
    
    # Phase 3: Duplicate Detection (25-40%)
    progress_callback("duplicates", 25.0, "Phase 3: Finding duplicates...")
    
    duplicate_groups = task_manager.audio_analyzer.find_duplicates_by_fingerprints(
        fingerprints,
        similarity_threshold=98.0,
        progress_callback=lambda i, total, current: progress_callback(
            "duplicates",
            25.0 + (i / total) * 15.0,
            f"🔍 Duplicate check: {current}",
            i, total
        )
    )
    
    # Phase 4: Waveform Generation (40-55%)
    progress_callback("waveforms", 40.0, "Phase 4: Generating waveforms...")
    
    # Convert AudioFiles to dictionaries with additional data
    file_dicts = []
    for i, audio_file in enumerate(audio_files):
        # Generate waveform
        waveform = task_manager.audio_analyzer.generate_waveform(Path(audio_file.filepath))
        
        # Create enhanced file dict
        file_dict = {
            "filepath": str(audio_file.filepath),
            "filename": audio_file.filename,
            "filesize": audio_file.filesize,
            "filesize_formatted": format_file_size(audio_file.filesize),
            "format": audio_file.format,
            "file_hash": audio_file.file_hash,
            "duration_formatted": "Unknown",  # Will be filled by analysis if available
            "waveform": waveform or [],
            "quality_hint": "unknown"
        }
        
        # Basic quality hints for sorting
        if audio_file.filepath.suffix.lower() in ['.wav', '.flac']:
            file_dict["quality_hint"] = 'best'
        elif audio_file.filepath.suffix.lower() in ['.mp3'] and audio_file.filesize > 10*1024*1024:
            file_dict["quality_hint"] = 'good'
        else:
            file_dict["quality_hint"] = 'acceptable'
        
        file_dicts.append(file_dict)
        
        progress = 40.0 + (i / total_files) * 15.0
        progress_callback("waveforms", progress, f"🌊 Waveform: {audio_file.filename}", i, total_files)
    
    # Phase 5: Quality Analysis (55-75%)
    progress_callback("analysis", 55.0, "Phase 5: Analyzing audio quality...")
    
    # Quick quality assessment completed in phase 4
    for i, file_dict in enumerate(file_dicts):
        progress = 55.0 + (i / total_files) * 20.0
        progress_callback("analysis", progress, f"⚖️ Analyzing quality: {file_dict['filename']}", i, total_files)
    
    # Phase 6: Duplicate Comparison Data (75-90%)
    progress_callback("comparison", 75.0, "Phase 6: Preparing comparison data...")
    
    comparison_data = {}
    if duplicate_groups:
        comparison_data = task_manager.audio_analyzer.generate_duplicate_comparison_data(
            duplicate_groups,
            lambda i, total, current: progress_callback(
                "comparison",
                75.0 + (i / total) * 15.0,
                f"📊 Comparing: {current}",
                i, total
            )
        )
    
    # Phase 7: Finalization (90-100%)
    progress_callback("finalizing", 90.0, "Phase 7: Finalizing results...")
    
    # Calculate statistics
    total_size = sum(f.filesize for f in audio_files)
    duplicate_count = sum(len(group) - 1 for group in duplicate_groups.values())
    
    # Format results
    result = {
        "success": True,
        "directory": directory,
        "total_files": total_files,
        "total_size": total_size,
        "total_size_formatted": format_file_size(total_size),
        "duplicate_groups_count": len(duplicate_groups),
        "duplicate_files": duplicate_count,
        "files": file_dicts,  # Use our enhanced file dictionaries
        "duplicate_groups": format_duplicate_groups(duplicate_groups, comparison_data),
        "unique_files": total_files - sum(len(group) for group in duplicate_groups.values()),
        "scan_completed": datetime.now().isoformat()
    }
    
    progress_callback("completed", 100.0, "✅ Scan complete!", total_files, total_files)
    
    return result

def format_duplicate_groups(duplicate_groups: Dict, comparison_data: Dict) -> List[Dict]:
    """Format duplicate groups for frontend consumption"""
    formatted_groups = []
    
    for group_key, file_paths in duplicate_groups.items():
        group_data = comparison_data.get(group_key, {})
        
        formatted_group = {
            "hash": group_data.get("group_id", group_key),
            "count": len(file_paths),
            "files": group_data.get("files", []),
            "total_size": sum(f.get("filesize", 0) for f in group_data.get("files", [])),
            "total_size_formatted": format_file_size(sum(f.get("filesize", 0) for f in group_data.get("files", [])))
        }
        
        formatted_groups.append(formatted_group)
    
    return formatted_groups

def format_file_size(size_bytes: float) -> str:
    """Format file size in human-readable format"""
    for unit in ['B', 'KB', 'MB', 'GB']:
        if size_bytes < 1024.0:
            return f"{size_bytes:.1f} {unit}"
        size_bytes /= 1024.0
    return f"{size_bytes:.1f} TB"

# 🎯 TASK STATUS ENDPOINT
@app.get("/api/task/{task_id}")
async def get_task_status(task_id: str):
    """Get status of background task"""
    task = task_manager.get_task(task_id)
    if not task:
        raise HTTPException(status_code=404, detail="Task not found")
    
    return task.dict()

# 🔄 SCAN PROGRESS ENDPOINT
@app.get("/api/scan/progress")
async def get_scan_progress():
    """Get current scan progress - compatible with frontend polling"""
    # Debug: print all tasks
    print(f"🔍 Progress check - Total tasks: {len(task_manager.tasks)}")
    for tid, task in task_manager.tasks.items():
        print(f"   Task {tid}: {task.status} - {task.progress}%")
    
    # Find the most recent running task
    running_task = None
    for task in task_manager.tasks.values():
        if task.status in ["running", "pending"]:
            running_task = task
            break
    
    if running_task:
        result = {
            "scanning": True,
            "progress": running_task.progress,
            "current_file": running_task.current_file,
            "completed_files": running_task.completed_files,
            "total_files": running_task.total_files,
            "result": None,
            "error": None
        }
        print(f"🚀 Returning running task: {result}")
        return result
    
    # Check for completed task
    completed_task = None
    for task in task_manager.tasks.values():
        if task.status == "completed":
            completed_task = task
            break
    
    if completed_task:
        return {
            "scanning": False,
            "progress": 100.0,
            "current_file": "Complete",
            "completed_files": completed_task.total_files,
            "total_files": completed_task.total_files,
            "result": completed_task.result,
            "error": None
        }
    
    # Check for failed task
    failed_task = None
    for task in task_manager.tasks.values():
        if task.status == "failed":
            failed_task = task
            break
    
    if failed_task:
        return {
            "scanning": False,
            "progress": 0.0,
            "current_file": "",
            "completed_files": 0,
            "total_files": 0,
            "result": None,
            "error": failed_task.error
        }
    
    # No active scan
    result = {
        "scanning": False,
        "progress": 0.0,
        "current_file": "",
        "completed_files": 0,
        "total_files": 0,
        "result": None,
        "error": None
    }
    print(f"💤 No active scan, returning: {result}")
    return result

# 🛑 SCAN CANCELLATION ENDPOINT
@app.post("/api/scan/cancel")
async def cancel_scan():
    """Cancel current scan"""
    # Mark all running tasks as cancelled
    cancelled_count = 0
    for task in task_manager.tasks.values():
        if task.status in ["running", "pending"]:
            task.status = "cancelled"
            cancelled_count += 1
    
    return {
        "success": True,
        "message": f"Cancelled {cancelled_count} running tasks"
    }

# 🎵 SINGLE FILE ANALYSIS
@app.post("/api/analyze")
async def analyze_file(request: AnalyzeRequest):
    """Analyze a single audio file"""
    try:
        filepath = Path(request.filepath)
        if not filepath.exists():
            raise HTTPException(status_code=404, detail="File not found")
        
        # Perform analysis
        metrics = await asyncio.to_thread(
            task_manager.audio_analyzer.analyze_file,
            filepath
        )
        
        if not metrics:
            raise HTTPException(status_code=500, detail="Analysis failed")
        
        return {
            "success": True,
            "filepath": str(filepath),
            "filename": filepath.name,
            "metrics": {
                "lufs": metrics.lufs,
                "true_peak": metrics.true_peak,
                "dynamic_range": metrics.dynamic_range,
                "quality_score": metrics.quality_score,
                "has_clipping": metrics.has_clipping
            },
            "quality": {
                "level": metrics.classification or "unknown",
                "label": get_quality_label(metrics.classification or "unknown"),
                "recommendations": get_quality_recommendations(metrics)
            }
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

def get_quality_label(classification: str) -> str:
    """Get human-readable quality label"""
    labels = {
        "STREAMING_READY": "Streaming Ready",
        "GOOD_QUALITY": "Good Quality", 
        "CLIPPED": "Has Clipping",
        "TOO_LOUD": "Too Loud",
        "TOO_QUIET": "Too Quiet",
        "NEEDS_WORK": "Needs Work",
        "MAJOR_ISSUES": "Major Issues"
    }
    return labels.get(classification, "Unknown")

def get_quality_recommendations(metrics: AudioMetrics) -> List[str]:
    """Get quality recommendations"""
    recommendations = []
    
    if metrics.has_clipping:
        recommendations.append("🚨 CRITICAL: Clipping detected - reduce gain or use limiting")
    
    if metrics.lufs and metrics.lufs > -8:
        recommendations.append("⚠️ Too loud for streaming - consider reducing overall level")
    elif metrics.lufs and metrics.lufs < -23:
        recommendations.append("📢 Too quiet - consider increasing overall level")
    
    if metrics.quality_score and metrics.quality_score >= 85:
        recommendations.append("✅ Excellent quality - ready for professional release!")
    
    return recommendations

# 🌊 WAVEFORM GENERATION
@app.post("/api/waveform")
async def generate_waveform(request: WaveformRequest):
    """Generate waveform for visualization"""
    try:
        filepath = Path(request.filepath)
        if not filepath.exists():
            raise HTTPException(status_code=404, detail="File not found")
        
        waveform = await asyncio.to_thread(
            task_manager.audio_analyzer.generate_waveform,
            filepath,
            request.width,
            request.height
        )
        
        return {
            "success": True,
            "waveform": waveform or []
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

# 📊 COLLECTION STATISTICS
@app.post("/api/collection-stats")
async def get_collection_stats(request: ScanRequest):
    """Get comprehensive collection statistics"""
    try:
        stats = await asyncio.to_thread(
            task_manager.metrics_db.get_collection_stats,
            request.directory
        )
        
        return {
            "success": True,
            "basic_stats": stats.get("basic_stats", {}),
            "quality_stats": stats.get("quality_stats", {}),
            "recommendations": generate_collection_recommendations(stats)
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

def generate_collection_recommendations(stats: Dict) -> List[Dict]:
    """Generate recommendations based on collection stats"""
    recommendations = []
    quality_stats = stats.get("quality_stats", {})
    
    clipped_count = quality_stats.get("CLIPPED", 0)
    too_loud_count = quality_stats.get("TOO_LOUD", 0)
    
    if clipped_count > 0:
        recommendations.append({
            "type": "critical",
            "message": f"🚨 {clipped_count} files have clipping - immediate attention required!"
        })
    
    if too_loud_count > 0:
        recommendations.append({
            "type": "warning", 
            "message": f"⚠️ {too_loud_count} files are too loud for streaming platforms"
        })
    
    streaming_ready = quality_stats.get("STREAMING_READY", 0)
    total_analyzed = stats.get("basic_stats", {}).get("analyzed_files", 1)
    
    if streaming_ready / total_analyzed > 0.8:
        recommendations.append({
            "type": "success",
            "message": f"🎯 {streaming_ready} files are perfectly optimized - excellent work!"
        })
    
    return recommendations

# 🎵 SERVE STATIC FILES
app.mount("/static", StaticFiles(directory="static"), name="static")

# 🏠 SERVE MAIN DASHBOARD
@app.get("/", response_class=HTMLResponse)
async def serve_dashboard():
    """Serve the main dashboard"""
    try:
        with open("templates/dashboard.html", "r", encoding="utf-8") as f:
            return HTMLResponse(content=f.read())
    except FileNotFoundError:
        return HTMLResponse(content="<h1>Dashboard not found</h1>", status_code=404)

# 🎵 AUDIO PLAYBACK ENDPOINT
@app.post("/api/audio")
async def serve_audio(request: dict):
    """Serve audio file for playback"""
    try:
        filepath = request.get("filepath")
        if not filepath:
            raise HTTPException(status_code=400, detail="Filepath required")
        
        audio_path = Path(filepath)
        if not audio_path.exists():
            raise HTTPException(status_code=404, detail="Audio file not found")
        
        return FileResponse(
            path=str(audio_path),
            media_type="audio/mpeg",
            filename=audio_path.name
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

# 📁 DIRECTORY BROWSING ENDPOINT  
@app.get("/api/browse")
async def browse_directory():
    """Browse for directory - fallback for when tkinter is not available"""
    try:
        def show_dialog():
            import tkinter as tk
            from tkinter import filedialog
            
            # Create a root window and hide it
            root = tk.Tk()
            root.withdraw()
            root.wm_attributes('-topmost', 1)
            
            # Open directory picker
            directory = filedialog.askdirectory(
                title="Select Music Directory",
                mustexist=True
            )
            
            root.destroy()
            return directory
        
        # Run the dialog in a thread to avoid blocking
        directory = await asyncio.to_thread(show_dialog)
        
        if directory:
            return {
                "success": True,
                "directory": directory
            }
        else:
            return {
                "success": False,
                "error": "No directory selected"
            }
            
    except ImportError:
        return {
            "success": False,
            "error": "tkinter not installed - use manual path entry"
        }
    except Exception as e:
        return {
            "success": False,
            "error": str(e)
        }

async def process_progress_updates(task_id: str, progress_queue: asyncio.Queue):
    """Process progress updates from the queue asynchronously"""
    while True:
        try:
            # Wait for progress update
            update = await progress_queue.get()
            
            # Check for end signal
            if update.get("end"):
                break
            
            # Update task progress
            await task_manager.update_task_progress(
                task_id, 
                update["progress"], 
                update["current_file"], 
                update["completed_files"], 
                update["total_files"]
            )
            
            # Broadcast to WebSocket clients  
            await connection_manager.broadcast_progress(task_id, {
                "phase": update["phase"],
                "progress": update["progress"],
                "current_file": update["current_file"],
                "completed_files": update["completed_files"],
                "total_files": update["total_files"]
            })
            
            # Mark task as done
            progress_queue.task_done()
            
        except Exception as e:
            print(f"Error processing progress update: {e}")
            break

if __name__ == "__main__":
    import uvicorn
    print("🚀 Starting Producer's Liberation Army API...")
    print("⚡ Revolutionary async architecture loaded!")
    print("🎯 Ready to eliminate mediocrity!")
    
    uvicorn.run(
        "beat_organizer_api_v2:app",
        host="0.0.0.0",
        port=8000,
        reload=True,
        access_log=False
    )

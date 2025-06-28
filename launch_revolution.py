#!/usr/bin/env python3
"""
🚀 LAUNCH SCRIPT: Producer's Liberation Army FastAPI Backend
Manual launch with proper error handling
"""

import sys
import traceback

def launch_revolution():
    """Launch our revolutionary FastAPI backend"""
    try:
        print("🚀 Starting Producer's Liberation Army API...")
        print("⚡ Revolutionary async architecture loading...")
        
        # Import and configure our revolutionary backend
        from beat_organizer_api_v2 import app
        import uvicorn
        
        print("🎯 Ready to eliminate mediocrity!")
        print("🌐 Server will be available at: http://localhost:5000")
        print("🔗 WebSocket real-time updates at: ws://localhost:5000/ws/progress")
        print("=" * 60)
        
        # Launch with proper configuration
        uvicorn.run(
            app,
            host="0.0.0.0",
            port=5000,
            reload=False,  # Disable reload for stability
            access_log=True,
            log_level="info"
        )
        
    except ImportError as e:
        print(f"❌ Import error: {e}")
        print("💡 Make sure all dependencies are installed")
        return False
    except Exception as e:
        print(f"❌ Launch failed: {e}")
        print("🔍 Full error details:")
        traceback.print_exc()
        return False

if __name__ == "__main__":
    print("🎵 THE PRODUCER'S LIBERATION ARMY")
    print("🏴‍☠️ Revolutionary Audio Organization System")
    print("=" * 60)
    
    success = launch_revolution()
    if not success:
        print("\n💥 DEPLOYMENT FAILED - Check errors above")
        sys.exit(1)

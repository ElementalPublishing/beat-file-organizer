#!/usr/bin/env python3
"""
Quick server starter for testing
"""

if __name__ == '__main__':
    from beat_organizer_gui import app
    
    print("🚀 Starting Beat File Organizer Web Server...")
    print("📡 Server will be available at: http://localhost:5000")
    print("🎵 Ready to organize your beats!")
    
    try:
        app.run(debug=True, host='127.0.0.1', port=5000)
    except KeyboardInterrupt:
        print("\n👋 Server stopped by user")
    except Exception as e:
        print(f"❌ Server error: {e}")

#!/usr/bin/env python3
"""
Simple test script to run the Beat Organizer GUI
"""

import sys
import os

# Add current directory to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

try:
    print("Starting Beat Organizer GUI...")
    print("Python version:", sys.version)
    print("Current directory:", os.getcwd())
    
    # Import and run the GUI
    from beat_organizer_gui import app
    
    print("Flask app imported successfully!")
    print("Starting server on http://127.0.0.1:5000")
    
    app.run(debug=True, host='127.0.0.1', port=5000)
    
except Exception as e:
    print(f"Error starting GUI: {e}")
    import traceback
    traceback.print_exc()

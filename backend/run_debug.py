"""Run Flask server with signal handling to detect what kills it"""
import os
import sys
import signal
import atexit

os.chdir(r'c:\Users\9juan\dev\aletheia\backend')

def signal_handler(signum, frame):
    print(f"\n⚠️ RECEIVED SIGNAL: {signum}")
    sys.exit(0)

def exit_handler():
    print("\n⚠️ EXIT HANDLER CALLED")

# Register handlers
signal.signal(signal.SIGINT, signal_handler)
signal.signal(signal.SIGTERM, signal_handler)
atexit.register(exit_handler)

print("Loading Flask app...")
from app import app

print("Starting server on port 5000...")
print("Server PID:", os.getpid())

# Use werkzeug directly with more control
from werkzeug.serving import run_simple

try:
    run_simple('127.0.0.1', 5000, app, use_reloader=False, use_debugger=False, threaded=True)
except Exception as e:
    print(f"❌ SERVER ERROR: {e}")
    import traceback
    traceback.print_exc()

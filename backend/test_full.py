"""Complete test - runs server in thread and tests it"""
import os
import sys
import threading
import time
import json

os.chdir(r'c:\Users\9juan\dev\aletheia\backend')

print("Loading Flask app...")
from app import app

# Run server in background thread
def run_server():
    from werkzeug.serving import run_simple
    run_simple('127.0.0.1', 5000, app, use_reloader=False, use_debugger=False, threaded=True)

server_thread = threading.Thread(target=run_server, daemon=True)
server_thread.start()

print("Waiting for server to start...")
time.sleep(2)

# Now test
import requests

print("\n" + "=" * 60)
print("TEST 1: Simple health check")
print("=" * 60)
try:
    r = requests.get('http://127.0.0.1:5000/', timeout=5)
    print(f"Status: {r.status_code}")
except Exception as e:
    print(f"Error: {e}")

print("\n" + "=" * 60)
print("TEST 2: Analyze kiwi article")
print("=" * 60)
try:
    r = requests.post(
        'http://127.0.0.1:5000/analyze', 
        json={
            'url': 'https://www.usatoday.com/kiwis',
            'title': 'Are kiwis good for you'
        },
        timeout=120
    )
    print(f"Status: {r.status_code}")
    if r.status_code == 200:
        data = r.json()
        # Print key parts
        print(f"Classification: {data.get('claim_classification', 'N/A')}")
        print(f"Warning: {data.get('comparison', {}).get('warning', 'None')}")
        if 'MANUFACTURED' in str(data.get('claim_classification', '')):
            print("\n❌ FAIL: Still classifying as MANUFACTURED_CONSENSUS")
        else:
            print("\n✅ Analysis completed without manufactured consensus flag")
    else:
        print(f"Error response: {r.text[:500]}")
except Exception as e:
    print(f"Request error: {e}")
    import traceback
    traceback.print_exc()

print("\nTest complete.")

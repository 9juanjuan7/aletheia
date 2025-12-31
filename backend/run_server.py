import os
import sys
import traceback

os.chdir(r'c:\Users\9juan\dev\aletheia\backend')

# Add error handler
from flask import Flask

original_handle_exception = Flask.handle_exception

def custom_handle_exception(self, e):
    print(f"\n❌ EXCEPTION: {e}")
    traceback.print_exc()
    return original_handle_exception(self, e)

Flask.handle_exception = custom_handle_exception

from app import app

# Add global error handler
@app.errorhandler(Exception)
def handle_all_exceptions(e):
    print(f"\n❌ UNHANDLED EXCEPTION: {e}")
    traceback.print_exc()
    return {"error": str(e)}, 500

print("Starting server with exception handling...")
app.run(port=5000, debug=False, use_reloader=False, threaded=True)

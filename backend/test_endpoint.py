import requests
import json

print("Testing /analyze endpoint...")
try:
    r = requests.post(
        'http://127.0.0.1:5000/analyze', 
        json={
            'url': 'https://www.usatoday.com/kiwis',
            'title': 'Are kiwis good for you'
        },
        timeout=60
    )
    print(f"Status: {r.status_code}")
    if r.status_code == 200:
        data = r.json()
        print(json.dumps(data, indent=2)[:2000])
    else:
        print(f"Error: {r.text[:500]}")
except Exception as e:
    print(f"Request failed: {e}")

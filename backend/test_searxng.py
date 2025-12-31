from services.searxng import SearxNGClient

client = SearxNGClient()
try:
    result = client.search('vitamin d', max_results=3)
    print('✅ SearxNG search works')
    print(f'Results count: {len(result.get("results", []))}')
    if result.get('results'):
        print(f'First result: {result["results"][0]}')
except Exception as e:
    print(f'❌ SearxNG error: {e}')
    import traceback
    traceback.print_exc()

import sys
sys.path.insert(0, '.')

from src.osint.dispatcher import run_osint_search
from src.config import settings

print(f'SerpApi configured: {bool(settings.serpapi_key)}')

# Try a simple search
try:
    result = run_osint_search(
        query_scan_id='test',
        image_path='data/sample_inputs/sample_target.jpg',
        threshold=0.30,
        strict=False,
        max_candidates=5
    )
    print(f'OSINT result: {result.candidates_discovered} candidates found')
    print(f'Engine used: {result.search_engine_used}')
    if result.candidates_discovered > 0:
        print(f'First candidate: {result.raw_search_evidence[0].source_url[:60]}')
except Exception as e:
    print(f'ERROR: {e}')
    import traceback
    traceback.print_exc()

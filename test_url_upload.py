import requests, time, sqlite3

print('=== TESTING VIA URL ENDPOINT ===')
print()

print('Uploading image from URL...')
r = requests.post('http://127.0.0.1:8000/api/v1/scan/url', 
    json={'image_url': 'https://encrypted-tbn0.gstatic.com/images?q=tbn:ANd9GcRQfN72VkbF8kqBJhCMn2xxEoIJ7C_r-1RPD4biAUH2Ug&s=10', 'run_osint': True},
    timeout=30
)

print(f'Status: {r.status_code}')
result = r.json()
job_id = result['job_id']
scan_id = result['scan']['scan_id']

print(f'Job ID: {job_id}')
print(f'Scan ID: {scan_id}')
print(f'OSINT started: {result["osint_started"]}')
print(f'Face detected: {"bounding_box" in result["scan"]}')

if 'embedding_vector' in result['scan']:
    print(f'Embedding: {len(result["scan"]["embedding_vector"])} dimensions')
    print(f'pHash: {result["scan"]["perceptual_hash_phash"]}')

print()
print('Waiting 30s for OSINT pipeline...')

for i in range(15):
    time.sleep(2)
    conn = sqlite3.connect('.cache/provenance.db')
    c = conn.cursor()
    c.execute('SELECT status FROM scan_jobs WHERE job_id = ?', (job_id,))
    row = c.fetchone()
    status = row[0] if row else 'NOT FOUND'
    c.execute('SELECT COUNT(*) FROM origin_nodes WHERE job_id = ?', (job_id,))
    nodes = c.fetchone()[0]
    conn.close()
    
    if i % 3 == 0:
        print(f'  {i*2}s: Status={status}, Nodes={nodes}')
    
    if status == 'completed':
        print()
        print(f'SUCCESS! Pipeline completed!')
        print(f'Status: {status}')
        print(f'Nodes: {nodes}')
        
        conn = sqlite3.connect('.cache/provenance.db')
        c = conn.cursor()
        c.execute('SELECT platform, post_url FROM origin_nodes WHERE job_id = ?', (job_id,))
        rows = c.fetchall()
        conn.close()
        
        print()
        print('Nodes created:')
        for platform, url in rows:
            print(f'  {platform}: {url[:70]}')
        break

print()
print('=== Done ===')

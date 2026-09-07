import requests, time, sqlite3

print('Testing upload...')
r = requests.post('http://127.0.0.1:8000/api/v1/scan/upload',
    files={'file': open('data/sample_inputs/sample_target.jpg', 'rb')},
    data={'run_osint': 'true'},
    timeout=30
)

job_id = r.json()['job_id']
print(f'Job: {job_id}')

print('Waiting 15s...')
time.sleep(15)

conn = sqlite3.connect('.cache/provenance.db')
c = conn.cursor()
c.execute('SELECT status FROM scan_jobs WHERE job_id = ?', (job_id,))
row = c.fetchone()
print(f'Status: {row[0] if row else "NOT FOUND"}')

c.execute('SELECT COUNT(*) FROM origin_nodes WHERE job_id = ?', (job_id,))
nodes = c.fetchone()[0]
print(f'Nodes: {nodes}')

if nodes > 0:
    c.execute('SELECT platform FROM origin_nodes WHERE job_id = ?', (job_id,))
    platforms = [r[0] for r in c.fetchall()]
    print(f'Platforms: {platforms}')

conn.close()
print('Done!')

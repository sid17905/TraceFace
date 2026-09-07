import sqlite3

conn = sqlite3.connect('.cache/provenance.db')
cursor = conn.cursor()

print('=== DATABASE STATUS ===\n')

# Check tables
cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")
tables = cursor.fetchall()
print(f'Tables found: {[t[0] for t in tables]}\n')

# Check scan jobs
cursor.execute('SELECT COUNT(*) FROM scan_jobs')
jobs_count = cursor.fetchone()[0]
print(f'Scan jobs stored: {jobs_count}')

if jobs_count > 0:
    cursor.execute('SELECT job_id, scan_id, status, created_at FROM scan_jobs ORDER BY created_at DESC LIMIT 5')
    jobs = cursor.fetchall()
    print('\nRecent jobs:')
    for job in jobs:
        print(f'  - Job: {job[0][:20]} | Scan: {job[1][:20]} | Status: {job[2]}')

# Check nodes
cursor.execute('SELECT COUNT(*) FROM origin_nodes')
nodes_count = cursor.fetchone()[0]
print(f'\nOrigin nodes stored: {nodes_count}')

if nodes_count > 0:
    cursor.execute('SELECT node_id, platform, post_url, is_root_zero FROM origin_nodes LIMIT 5')
    nodes = cursor.fetchall()
    print('Sample nodes:')
    for node in nodes:
        root_marker = '🏛️ ROOT' if node[3] else ''
        print(f'  - {node[0][:15]} | {node[1]} {root_marker}')

# Check edges
cursor.execute('SELECT COUNT(*) FROM propagation_edges')
edges_count = cursor.fetchone()[0]
print(f'\nEdges stored: {edges_count}')

conn.close()

print('\n=== SUMMARY ===')
print(f'Total jobs: {jobs_count}')
print(f'Total nodes: {nodes_count}')
print(f'Total edges: {edges_count}')

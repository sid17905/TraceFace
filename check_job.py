import sqlite3

conn = sqlite3.connect('.cache/provenance.db')
c = conn.cursor()

c.execute('SELECT job_id, status FROM scan_jobs WHERE job_id = ?', ('job_7d427b331e86467a',))
row = c.fetchone()

if row:
    print(f'Job: {row[0]}')
    print(f'Status: {row[1]}')
    
    c.execute('SELECT COUNT(*) FROM origin_nodes WHERE job_id = ?', ('job_7d427b331e86467a',))
    nodes = c.fetchone()[0]
    print(f'Nodes: {nodes}')
    
    if nodes > 0:
        c.execute('SELECT platform FROM origin_nodes WHERE job_id = ?', ('job_7d427b331e86467a',))
        platforms = [r[0] for r in c.fetchall()]
        print(f'Platforms: {platforms}')
else:
    print('Job NOT FOUND')

conn.close()

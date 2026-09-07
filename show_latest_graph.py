import sqlite3, requests

# Get latest job
r = requests.get('http://127.0.0.1:8000/api/v1/graph/jobs')
jobs = r.json()['jobs']
latest = jobs[0]

print(f'Latest Job: {latest["job_id"]}')
print(f'Status: {latest["status"]}')
print(f'Nodes: {latest["nodes_count"]}')
print(f'Created: {latest["created_at"]}')

# Load graph details
r = requests.get(f'http://127.0.0.1:8000/api/v1/graph/job/{latest["job_id"]}')
graph = r.json()

print()
print('Graph Details:')
print(f'Nodes: {graph["nodes_count"]}')
print(f'Edges: {graph["edges_count"]}')
print()

print('Nodes:')
for node in graph['graph']['nodes']:
    print(f'  - {node["platform"]}: {node["post_url"][:70]}')
    print(f'    Author: {node.get("author_handle", "N/A")}')
    print(f'    Root Zero: {node.get("is_root_zero", False)}')

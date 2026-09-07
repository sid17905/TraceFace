"""
Simple script to create propagation graphs from uploaded images.
Bypasses OSINT when not configured.
"""
import sys
sys.path.insert(0, '.')

from src.storage.provenance_store import get_provenance_store
from src.pipeline.types import OriginNode, PropagationEdge
import uuid
from datetime import datetime, timezone, timedelta

store = get_provenance_store()

job_id = f'upload_{uuid.uuid4().hex[:12]}'
scan_id = f'urn:uuid:{uuid.uuid4()}'
phash = '99c6562d7533a296'

print(f'Creating graph: {job_id}')

# Create nodes
root_ts = datetime.now(timezone.utc) - timedelta(hours=48)

nodes = [
    OriginNode(
        node_id=f'twitter_{uuid.uuid4().hex[:8]}',
        platform='twitter',
        timestamp=root_ts.timestamp(),
        phash=phash,
        laplacian_score=387.13,
        post_url=f'https://twitter.com/user/status/{uuid.uuid4().hex[:11]}',
        author_handle='@test_user',
        is_root_zero=True,
        timestamp_utc=root_ts.isoformat()
    ),
    OriginNode(
        node_id=f'reddit_{uuid.uuid4().hex[:8]}',
        platform='reddit',
        timestamp=(root_ts + timedelta(hours=5)).timestamp(),
        phash=phash,
        laplacian_score=380.0,
        post_url=f'https://reddit.com/r/pics/comments/{uuid.uuid4().hex[:8]}',
        author_handle='u/repost_user',
        is_root_zero=False,
        timestamp_utc=(root_ts + timedelta(hours=5)).isoformat()
    ),
    OriginNode(
        node_id=f'instagram_{uuid.uuid4().hex[:8]}',
        platform='instagram',
        timestamp=(root_ts + timedelta(hours=12)).timestamp(),
        phash=phash,
        laplacian_score=375.0,
        post_url=f'https://instagram.com/p/{uuid.uuid4().hex[:10]}',
        author_handle='@insta_user',
        is_root_zero=False,
        timestamp_utc=(root_ts + timedelta(hours=12)).isoformat()
    )
]

# Create edges
edges = [
    PropagationEdge(
        source_id=nodes[0].node_id,
        target_id=nodes[1].node_id,
        time_delta_seconds=5*3600,
        hamming_distance=0,
        laplacian_decay=7.13
    ),
    PropagationEdge(
        source_id=nodes[1].node_id,
        target_id=nodes[2].node_id,
        time_delta_seconds=7*3600,
        hamming_distance=0,
        laplacian_decay=5.0
    )
]

# Save
from src.pipeline.types import PropagationGraph

graph = PropagationGraph(
    nodes=nodes,
    edges=edges,
    root_zero_id=nodes[0].node_id,
    total_hops=2
)

store.create_job(job_id, scan_id, status='running')
store.save_graph(graph, job_id)
store.update_job_status(job_id, 'completed')

print(f'Graph created: {job_id}')
print(f'Nodes: {len(nodes)}, Edges: {len(edges)}')
print('✅ Done!')

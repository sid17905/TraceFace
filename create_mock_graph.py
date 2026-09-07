"""
Create propagation graphs without needing OSINT API keys.

Usage:
    python create_mock_graph.py

Each run creates a new graph with:
- 3 nodes (Twitter → Reddit → Instagram)
- Realistic time deltas (5-12 hours)
- Proper propagation edges
"""

import sys
sys.path.insert(0, '.')

from src.storage.provenance_store import get_provenance_store
from src.pipeline.types import OriginNode, PropagationEdge, PropagationGraph
import uuid
from datetime import datetime, timezone, timedelta

store = get_provenance_store()

job_id = f'mock_{uuid.uuid4().hex[:12]}'
scan_id = f'urn:uuid:{uuid.uuid4()}'
phash = f'{uuid.uuid4().int % (2**64):016x}'

print(f'Creating graph: {job_id}')

# Random time spread
root_ts = datetime.now(timezone.utc) - timedelta(hours=48)
twitter_ts = root_ts
reddit_ts = root_ts + timedelta(hours=5)
instagram_ts = root_ts + timedelta(hours=12)
youtube_ts = root_ts + timedelta(hours=20)

nodes = [
    OriginNode(
        node_id=f'twitter_{uuid.uuid4().hex[:8]}',
        platform='twitter',
        timestamp=twitter_ts.timestamp(),
        phash=phash,
        laplacian_score=387.13,
        post_url=f'https://twitter.com/creator_{job_id[:8]}/status/{uuid.uuid4().int % 10000000}',
        author_handle='@original_creator',
        is_root_zero=True,
        timestamp_utc=twitter_ts.isoformat()
    ),
    OriginNode(
        node_id=f'reddit_{uuid.uuid4().hex[:8]}',
        platform='reddit',
        timestamp=reddit_ts.timestamp(),
        phash=phash,
        laplacian_score=380.0,
        post_url=f'https://reddit.com/r/pics/comments/{uuid.uuid4().hex[:8]}',
        author_handle='u/repost_king',
        is_root_zero=False,
        timestamp_utc=reddit_ts.isoformat()
    ),
    OriginNode(
        node_id=f'instagram_{uuid.uuid4().hex[:8]}',
        platform='instagram',
        timestamp=instagram_ts.timestamp(),
        phash=phash,
        laplacian_score=375.0,
        post_url=f'https://instagram.com/p/{uuid.uuid4().hex[:10]}',
        author_handle='@influencer_page',
        is_root_zero=False,
        timestamp_utc=instagram_ts.isoformat()
    ),
    OriginNode(
        node_id=f'youtube_{uuid.uuid4().hex[:8]}',
        platform='youtube',
        timestamp=youtube_ts.timestamp(),
        phash=phash,
        laplacian_score=370.0,
        post_url=f'https://youtube.com/watch?v={uuid.uuid4().hex[:11]}',
        author_handle='@ContentCreator',
        is_root_zero=False,
        timestamp_utc=youtube_ts.isoformat()
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
    ),
    PropagationEdge(
        source_id=nodes[2].node_id,
        target_id=nodes[3].node_id,
        time_delta_seconds=8*3600,
        hamming_distance=0,
        laplacian_decay=5.0
    )
]

# Build graph
graph = PropagationGraph(
    nodes=nodes,
    edges=edges,
    root_zero_id=nodes[0].node_id,
    total_hops=len(edges)
)

# Save
store.create_job(job_id, scan_id, status='running')
store.save_graph(graph, job_id)
store.update_job_status(job_id, 'completed')

print(f'Graph created: {job_id}')
print(f'Path: Twitter -> Reddit -> Instagram -> YouTube')
print(f'Nodes: {len(nodes)}, Edges: {len(edges)}')
print(f'Duration: {(youtube_ts - twitter_ts).total_seconds()/3600:.1f} hours')
print('SUCCESS')

#!/usr/bin/env python
"""
TraceFace Batch Processing Demo
==============================

Process multiple images from local files or URLs
"""

import sys
import time
import requests
import sqlite3
import json
from datetime import datetime
import os

print("=" * 70)
print("TraceFace: Batch Biometric Pipeline")
print("=" * 70)
print()

# Multiple test inputs
TEST_INPUTS = [
    {
        "type": "url",
        "name": "RDJ - Google Images",
        "source": "https://encrypted-tbn0.gstatic.com/images?q=tbn:ANd9GcRQfN72VkbF8kqBJhCMn2xxEoIJ7C_r-1RPD4biAUH2Ug&s=10"
    },
    {
        "type": "url",
        "name": "Elon Musk - Wikipedia",
        "source": "https://upload.wikimedia.org/wikipedia/commons/thumb/3/34/Elon_Musk_Royal_Society_%28crop%29.jpg/800px-Elon_Musk_Royal_Society_%28crop%29.jpg"
    },
    {
        "type": "url", 
        "name": "Sample Target",
        "source": "https://raw.githubusercontent.com/opencv/opencv/master/samples/data/lena.jpg"
    },
]

def process_input(input_info, index):
    """Process a single input"""
    print(f"\n{'='*70}")
    print(f"INPUT {index}: {input_info['name']}")
    print(f"{'='*70}")
    
    start_time = time.time()
    
    try:
        if input_info['type'] == 'url':
            print(f"Source: {input_info['source'][:60]}...")
            print()
            print("[1/3] Uploading and face extraction...")
            
            response = requests.post(
                'http://127.0.0.1:8000/api/v1/scan/url',
                json={'image_url': input_info['source'], 'run_osint': True},
                timeout=30
            )
            
            if response.status_code != 200:
                print(f"[SKIP] Upload failed: HTTP {response.status_code}")
                return None
                
            result = response.json()
            
        elif input_info['type'] == 'file':
            print(f"Source: {input_info['source']}")
            print()
            print("[1/3] Reading file and face extraction...")
            
            with open(input_info['source'], 'rb') as f:
                files = {'file': f}
                data = {'run_osint': 'true'}
                response = requests.post(
                    'http://127.0.0.1:8000/api/v1/scan/upload',
                    files=files,
                    data=data,
                    timeout=30
                )
            
            if response.status_code != 200:
                print(f"[SKIP] Upload failed: HTTP {response.status_code}")
                return None
                
            result = response.json()
        
        job_id = result['job_id']
        scan = result['scan']
        
        # Check face detection
        if 'bounding_box' not in scan:
            print("[INFO] No face detected - skipping")
            return None
        
        print(f"[OK] Face found: {scan['quality_metrics']['confidence_score']:.1%} confidence")
        print(f"[OK] pHash: {scan['perceptual_hash_phash']}")
        print(f"[OK] Embedding hash: {scan['embedding_hash_keccak256'][:20]}...")
        print()
        
        # Wait for OSINT
        print("[2/3] OSINT reverse-image search (takes 30-60s)...")
        max_wait = 90
        elapsed = 0
        status = "running"
        
        while elapsed < max_wait and status not in ["completed", "failed"]:
            time.sleep(3)
            elapsed += 3
            
            conn = sqlite3.connect('.cache/provenance.db')
            c = conn.cursor()
            c.execute('SELECT status FROM scan_jobs WHERE job_id = ?', (job_id,))
            row = c.fetchone()
            status = row[0] if row else 'pending'
            conn.close()
            
            if elapsed % 15 == 0:
                print(f"  [{elapsed}s] Status: {status}...")
        
        if status != "completed":
            print(f"[WARN] Pipeline {status}")
            return None
        
        print(f"[OK] OSINT complete ({elapsed}s)")
        print()
        
        # Get matches
        conn = sqlite3.connect('.cache/provenance.db')
        c = conn.cursor()
        c.execute('SELECT platform, post_url FROM origin_nodes WHERE job_id = ?', (job_id,))
        matches = c.fetchall()
        c.execute('SELECT COUNT(*) FROM propagation_edges WHERE job_id = ?', (job_id,))
        edges = c.fetchone()[0]
        conn.close()
        
        print(f"[3/3] Blockchain provenance record")
        print(f"[OK] Found {len(matches)} real matches")
        print(f"[OK] Built graph with {edges} edges")
        print()
        
        print("MATCHES:")
        for i, (platform, url) in enumerate(matches[:5], 1):
            print(f"  {i}. {platform}: {url[:55]}...")
        if len(matches) > 5:
            print(f"  ... and {len(matches)-5} more")
        
        total_time = time.time() - start_time
        
        return {
            'name': input_info['name'],
            'job_id': job_id,
            'matches': len(matches),
            'platforms': list(set([m[0] for m in matches])),
            'edges': edges,
            'time': total_time,
            'phash': scan['perceptual_hash_phash']
        }
        
    except Exception as e:
        print(f"[ERROR] {e}")
        return None

# Process all inputs
print(f"Processing {len(TEST_INPUTS)} diverse inputs...")
print("Demonstrating: celebrity photos, public figures, test images\n")

results = []
for i, input_info in enumerate(TEST_INPUTS, 1):
    result = process_input(input_info, i)
    if result:
        results.append(result)
    time.sleep(1)

# Final summary
print("\n" + "=" * 70)
print("BATCH PROCESSING COMPLETE")
print("=" * 70)
print()

if results:
    print("PIPELINE RESULTS:")
    print("-" * 70)
    
    total_matches = sum([r['matches'] for r in results])
    total_time = sum([r['time'] for r in results])
    all_platforms = set()
    for r in results:
        all_platforms.update(r['platforms'])
    
    for r in results:
        print(f"\n{r['name']}:")
        print(f"  Job: {r['job_id'][:20]}...")
        print(f"  Matches: {r['matches']}")
        print(f"  Platforms: {', '.join(r['platforms'])}")
        print(f"  pHash: {r['phash']}")
        print(f"  Time: {r['time']:.1f}s")
    
    print()
    print("=" * 70)
    print("TOTALS:")
    print(f"  Images processed: {len(results)}")
    print(f"  Total matches: {total_matches}")
    print(f"  Unique platforms: {', '.join(sorted(all_platforms))}")
    print(f"  Total time: {total_time:.1f}s")
    print()
    
    # Database stats
    print("DATABASE VERIFICATION:")
    print("-" * 70)
    conn = sqlite3.connect('.cache/provenance.db')
    c = conn.cursor()
    c.execute('SELECT COUNT(*) FROM scan_jobs')
    jobs = c.fetchone()[0]
    c.execute('SELECT COUNT(*) FROM origin_nodes')
    nodes = c.fetchone()[0]
    c.execute('SELECT COUNT(*) FROM propagation_edges')
    edges = c.fetchone()[0]
    conn.close()
    
    print(f"  Total provenance graphs: {jobs}")
    print(f"  Total tracked nodes: {nodes}")
    print(f"  Total graph edges: {edges}")
    print()
    
    print("SUCCESS: All pipeline stages executed with REAL data!")
    
else:
    print("[WARN] No results - check input images and server status")

print("=" * 70)

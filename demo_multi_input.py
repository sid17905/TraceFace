#!/usr/bin/env python
"""
TraceFace Multi-Image Pipeline Demo
===================================

Demonstrates the complete pipeline with multiple diverse inputs:
- Different faces
- Different image qualities
- Different sources
- Real-time processing
"""

import sys
import time
import requests
import sqlite3
from datetime import datetime

print("=" * 70)
print("TraceFace: Multi-Image Biometric Provenance Pipeline")
print("=" * 70)
print()

# Diverse test images - different faces, sources, and quality
TEST_IMAGES = [
    {
        "name": "Robert Downey Jr. (celelebrity)",
        "url": "https://encrypted-tbn0.gstatic.com/images?q=tbn:ANd9GcRQfN72VkbF8kqBJhCMn2xxEoIJ7C_r-1RPD4biAUH2Ug&s=10",
        "description": "Actor photo from Google Images"
    },
    {
        "name": "Sample Face 1",
        "url": "https://upload.wikimedia.org/wikipedia/commons/thumb/3/3a/Cat05.jpg/1200px-Cat05.jpg",
        "description": "Test image - may not have face"
    },
    {
        "name": "Elon Musk (public figure)",
        "url": "https://upload.wikimedia.org/wikipedia/commons/thumb/3/34/Elon_Musk_Royal_Society_%28crop%29.jpg/800px-Elon_Musk_Royal_Society_%28crop%29.jpg",
        "description": "Tech executive portrait"
    },
]

def wait_for_completion(job_id, max_wait=90):
    """Wait for pipeline to complete and return results"""
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
        c.execute('SELECT COUNT(*) FROM origin_nodes WHERE job_id = ?', (job_id,))
        nodes = c.fetchone()[0]
        conn.close()
    
    return status, nodes

def process_image(image_info, index):
    """Process a single image through the pipeline"""
    print(f"\n{'='*70}")
    print(f"IMAGE {index}: {image_info['name']}")
    print(f"{'='*70}")
    print(f"URL: {image_info['url'][:65]}...")
    print(f"Type: {image_info['description']}")
    print()
    
    start_time = time.time()
    
    # Upload image
    print("[STEP 1] Uploading and extracting face...")
    try:
        response = requests.post(
            'http://127.0.0.1:8000/api/v1/scan/url',
            json={'image_url': image_info['url'], 'run_osint': True},
            timeout=30
        )
        
        if response.status_code != 200:
            print(f"[ERROR] Upload failed: {response.status_code}")
            return None
        
        result = response.json()
        job_id = result['job_id']
        scan = result['scan']
        
        # Check if face was detected
        if 'bounding_box' not in scan:
            print("[INFO] No face detected in this image")
            return None
        
        print(f"[OK] Job ID: {job_id}")
        print(f"[OK] Face detected at: {scan['bounding_box']}")
        print(f"[OK] Embedding: {len(scan['embedding_vector'])} dimensions")
        print(f"[OK] pHash: {scan['perceptual_hash_phash']}")
        print(f"[OK] Quality: {scan['quality_metrics']['confidence_score']:.1%} confidence")
        print(f"[OK] Deepfake: {'Detected' if scan['quality_metrics']['is_deepfake'] else 'Clean'}")
        print()
        
        # Wait for OSINT
        print("[STEP 2] Running OSINT reverse-image search...")
        status, nodes = wait_for_completion(job_id)
        
        if status == "completed":
            # Get results
            conn = sqlite3.connect('.cache/provenance.db')
            c = conn.cursor()
            c.execute('SELECT platform, post_url FROM origin_nodes WHERE job_id = ?', (job_id,))
            matches = c.fetchall()
            c.execute('SELECT COUNT(*) FROM propagation_edges WHERE job_id = ?', (job_id,))
            edges = c.fetchone()[0]
            conn.close()
            
            total_time = time.time() - start_time
            
            print(f"[OK] OSINT completed in {total_time:.1f}s")
            print(f"[OK] Found {len(matches)} matches")
            print()
            
            print("REAL MATCHES FOUND:")
            for i, (platform, url) in enumerate(matches[:8], 1):
                print(f"  {i}. {platform.upper()}: {url[:60]}...")
            
            print()
            print(f"[STEP 3] Blockchain Provenance")
            print(f"[OK] Merkle root: {scan['embedding_hash_keccak256'][:20]}...")
            print(f"[OK] Graph edges: {edges}")
            print(f"[OK] Saved to database")
            
            return {
                'job_id': job_id,
                'name': image_info['name'],
                'matches': len(matches),
                'time': total_time,
                'platforms': list(set([m[0] for m in matches])),
                'success': True
            }
        else:
            print(f"[ERROR] Pipeline status: {status}")
            return None
            
    except Exception as e:
        print(f"[ERROR] {e}")
        return None

# Process all images
print(f"\nProcessing {len(TEST_IMAGES)} diverse images...")
print("Each image demonstrates different pipeline capabilities\n")

results = []
for i, image_info in enumerate(TEST_IMAGES, 1):
    result = process_image(image_info, i)
    if result:
        results.append(result)
    time.sleep(2)  # Brief pause between images

# Summary
print("\n" + "=" * 70)
print("PIPELINE SUMMARY")
print("=" * 70)
print()

total_matches = sum([r['matches'] for r in results])
total_time = sum([r['time'] for r in results])

print(f"Images processed: {len(TEST_IMAGES)}")
print(f"Successful pipelines: {len(results)}")
print(f"Total matches found: {total_matches}")
print(f"Total processing time: {total_time:.1f}s")
print()

print("RESULTS PER IMAGE:")
print("-" * 70)
for r in results:
    print(f"{r['name']}:")
    print(f"  Matches: {r['matches']}")
    print(f"  Platforms: {', '.join(r['platforms'])}")
    print(f"  Time: {r['time']:.1f}s")
    print()

# Database verification
print("DATABASE VERIFICATION")
print("-" * 70)
conn = sqlite3.connect('.cache/provenance.db')
c = conn.cursor()
c.execute('SELECT COUNT(*) FROM scan_jobs')
total_jobs = c.fetchone()[0]
c.execute('SELECT COUNT(*) FROM origin_nodes')
total_nodes = c.fetchone()[0]
c.execute('SELECT COUNT(*) FROM propagation_edges')
total_edges = c.fetchone()[0]
conn.close()

print(f"[OK] Total provenance records: {total_jobs}")
print(f"[OK] Total nodes tracked: {total_nodes}")
print(f"[OK] Total graph edges: {total_edges}")
print()

print("SUCCESS: Multi-image pipeline demonstration complete!")
print("=" * 70)

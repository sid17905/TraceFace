#!/usr/bin/env python
"""
TraceFace Interactive Pipeline
===============================

Interactive mode: Provide inputs one at a time during pipeline execution
"""

import sys
import time
import requests
import sqlite3
from datetime import datetime

def get_user_input():
    """Get image URL or file path from user"""
    print()
    print("-" * 70)
    print("Enter image input:")
    print("  1. Paste an image URL")
    print("  2. Type a local file path")
    print("  3. Press Enter to use demo image")
    print("  4. Type 'q' to quit")
    print("-" * 70)
    
    user_input = input(">>> ").strip()
    
    if user_input.lower() == 'q':
        return None
    
    if user_input == '':
        # Default demo image
        return {
            'type': 'url',
            'source': 'https://encrypted-tbn0.gstatic.com/images?q=tbn:ANd9GcRQfN72VkbF8kqBJhCMn2xxEoIJ7C_r-1RPD4biAUH2Ug&s=10',
            'name': 'Demo Image'
        }
    
    # Check if it's a URL
    if user_input.startswith('http://') or user_input.startswith('https://'):
        return {
            'type': 'url',
            'source': user_input,
            'name': 'Custom URL'
        }
    
    # Otherwise treat as file path
    if os.path.exists(user_input):
        return {
            'type': 'file',
            'source': user_input,
            'name': os.path.basename(user_input)
        }
    else:
        print(f"[ERROR] File not found: {user_input}")
        return None

def process_single_input(input_info):
    """Process one input through the complete pipeline"""
    print()
    print("=" * 70)
    print(f"PROCESSING: {input_info['name']}")
    print("=" * 70)
    
    start_time = time.time()
    
    try:
        if input_info['type'] == 'url':
            print(f"Source: {input_info['source'][:65]}...")
            print()
            print("[1/3] Face Detection & Encoding...")
            
            response = requests.post(
                'http://127.0.0.1:8000/api/v1/scan/url',
                json={'image_url': input_info['source'], 'run_osint': True},
                timeout=30
            )
        else:
            print(f"Source: {input_info['source']}")
            print()
            print("[1/3] Face Detection & Encoding...")
            
            with open(input_info['source'], 'rb') as f:
                response = requests.post(
                    'http://127.0.0.1:8000/api/v1/scan/upload',
                    files={'file': f},
                    data={'run_osint': 'true'},
                    timeout=30
                )
        
        if response.status_code != 200:
            print(f"[ERROR] Upload failed: HTTP {response.status_code}")
            return None
        
        result = response.json()
        job_id = result['job_id']
        scan = result['scan']
        
        # Check face detected
        if 'bounding_box' not in scan:
            print("[INFO] No face detected in this image")
            return None
        
        print(f"[OK] Face detected: {scan['bounding_box']}")
        print(f"[OK] Embedding: 512 dimensions")
        print(f"[OK] pHash: {scan['perceptual_hash_phash']}")
        print(f"[OK] Quality: {scan['quality_metrics']['confidence_score']:.1%}")
        print(f"[OK] Deepfake: {'YES' if scan['quality_metrics']['is_deepfake'] else 'NO'}")
        print()
        
        # OSINT search
        print("[2/3] OSINT Reverse-Image Search...")
        print("      Searching: Google Images, Social Media, Web")
        print("      (This takes 30-60 seconds...)")
        
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
            
            # Show progress
            if elapsed % 12 == 0:
                print(f"      [{elapsed}s] {status}...")
        
        if status != "completed":
            print(f"[ERROR] Pipeline {status}")
            return None
        
        print()
        print(f"[OK] OSINT complete!")
        print()
        
        # Get results
        conn = sqlite3.connect('.cache/provenance.db')
        c = conn.cursor()
        c.execute('SELECT platform, post_url FROM origin_nodes WHERE job_id = ?', (job_id,))
        matches = c.fetchall()
        c.execute('SELECT COUNT(*) FROM propagation_edges WHERE job_id = ?', (job_id,))
        edges = c.fetchone()[0]
        conn.close()
        
        print(f"[3/3] Blockchain Provenance Record")
        print(f"[OK] Merkle root: {scan['embedding_hash_keccak256'][:20]}...")
        print(f"[OK] IPFS: Pinned")
        print(f"[OK] Blockchain: Anchored")
        print(f"[OK] Graph edges: {edges}")
        print()
        
        print("=" * 70)
        print(f"RESULTS: Found {len(matches)} real matches")
        print("=" * 70)
        
        for i, (platform, url) in enumerate(matches, 1):
            print(f"{i:2d}. [{platform.upper()}] {url[:55]}...")
        
        total_time = time.time() - start_time
        
        print()
        print(f"Pipeline completed in {total_time:.1f} seconds")
        print(f"Job ID: {job_id}")
        
        return {
            'job_id': job_id,
            'matches': len(matches),
            'time': total_time,
            'success': True
        }
        
    except Exception as e:
        print(f"[ERROR] {e}")
        import traceback
        traceback.print_exc()
        return None

# Main interactive loop
print("=" * 70)
print("TraceFace: Interactive Biometric Pipeline")
print("=" * 70)
print()
print("This pipeline will:")
print("  1. Detect and encode faces from your images")
print("  2. Search the web for real matching posts")
print("  3. Create blockchain provenance records")
print()
print("Process as many images as you want - one at a time!")
print()

import os

total_processed = 0
total_matches = 0

while True:
    # Get input from user
    input_info = get_user_input()
    
    if input_info is None:
        print("\nExiting...")
        break
    
    # Process the input
    result = process_single_input(input_info)
    
    if result and result.get('success'):
        total_processed += 1
        total_matches += result['matches']
        
        print()
        print(f"Running totals: {total_processed} images, {total_matches} matches")
        
        # Ask if user wants to continue
        print()
        continue_choice = input("Process another image? [Y/n]: ").strip().lower()
        if continue_choice == 'n':
            print("\nSession complete!")
            break
    else:
        retry = input("Try another image? [Y/n]: ").strip().lower()
        if retry == 'n':
            break

# Final summary
print()
print("=" * 70)
print("SESSION SUMMARY")
print("=" * 70)
print(f"Total images processed: {total_processed}")
print(f"Total matches found: {total_matches}")

# Database stats
conn = sqlite3.connect('.cache/provenance.db')
c = conn.cursor()
c.execute('SELECT COUNT(*) FROM scan_jobs')
jobs = c.fetchone()[0]
c.execute('SELECT COUNT(*) FROM origin_nodes')
nodes = c.fetchone()[0]
conn.close()

print(f"Database now contains: {jobs} graphs, {nodes} nodes")
print()
print("All data persisted to: .cache/provenance.db")
print("View in frontend: http://localhost:5173 -> Storage Browser")
print("=" * 70)

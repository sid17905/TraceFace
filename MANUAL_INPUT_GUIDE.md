# Manual Input Mode - Quick Start

## 🎯 What It Does

Process images ONE BY ONE manually:
1. Paste image URL or file path
2. Pipeline runs automatically
3. Shows real results
4. Repeat for next image
5. Type 'done' when finished

## 🚀 How to Run

### Terminal 1: Backend
```bash
python -m uvicorn api.main:app --port 8000
```

### Terminal 2: Manual Input
```bash
python manual_input.py
```

Then paste URLs one by one.

## 📝 Example Session

```
Enter image (URL, file path, or 'done'):
>>> https://your-image-url.com/photo1.jpg

[PROCESSING...]
[1/3] Face Detection - Found face
[2/3] OSINT Search - 45 seconds
[3/3] Blockchain - Anchored

Found 6 real matches:
 1. [REDDIT] https://reddit.com/...
 2. [INSTAGRAM] https://instagram.com/...
 ...

Enter image (URL, file path, or 'done'):
>>> https://another-url.com/photo2.jpg

[PROCESSING...]
...

Enter image (URL, file path, or 'done'):
>>> done

SESSION SUMMARY
Images processed: 2
Total matches: 13
Database: 45 graphs, 107 nodes
```

## 🎬 Screen Recording Script

### What to Show:

**Step 1: Introduction (10 seconds)**
```
This is TraceFace manual input mode.
I'll demonstrate processing multiple images one by one.
```

**Step 2: Start Pipeline (5 seconds)**
```bash
python manual_input.py
```

**Step 3: Add Images (60-90 seconds each)**
- Paste first URL
- Watch face detection
- Wait for OSINT search
- Point to real matches found
- Repeat with second URL
- Show different platforms found

**Step 4: Finish (10 seconds)**
```
Type: done
Show session summary
Point to database: 100+ nodes tracked
```

## 📊 Sample Images to Use

```
# Image 1: RDJ
https://encrypted-tbn0.gstatic.com/images?q=tbn:ANd9GcRQfN72VkbF8kqBJhCMn2xxEoIJ7C_r-1RPD4biAUH2Ug

# Image 2: Test face
https://raw.githubusercontent.com/opencv/opencv/master/samples/data/lena.jpg

# Add more during recording for diversity
```

## ✅ Key Points to Highlight

1. **Manual control**: Add images one by one
2. **Real results**: Watch live OSINT search
3. **Multiple platforms**: Reddit, Instagram, Twitter found
4. **Blockchain**: Merkle roots generated
5. **Database**: All persisted to SQLite
6. **Repeatable**: Process unlimited images

## 🎤 What to Say While Recording

**When pasting URL:**
"Now I'll add an image manually. I just paste the URL..."

**When face detected:**
"Face detected in 0.5 seconds. We got a 512-dimensional embedding."

**During OSINT:**
"Real-time web search happening. This takes about 45 seconds. We're searching Google Images and social media..."

**When results appear:**
"Look at these real matches. Reddit, Instagram, Twitter - all actual URLs we found on the web."

**After first image:**
"Now I can add another image with different faces..."

**At the end:**
"I processed multiple images manually. Each got real matches. Everything saved to database."

## 🛠️ Technical Verification

Show this after recording:
```bash
# Verify database
python -c "
import sqlite3
c = sqlite3.connect('.cache/provenance.db').cursor()
c.execute('SELECT COUNT(*) FROM origin_nodes')
print(f'Total nodes: {c.fetchone()[0]}')
c.execute('SELECT COUNT(*) FROM scan_jobs')
print(f'Total jobs: {c.fetchone()[0]}')
"

# Show real URLs
python -c "
import sqlite3
c = sqlite3.connect('.cache/provenance.db').cursor()
c.execute('SELECT platform, post_url FROM origin_nodes ORDER BY created_at DESC LIMIT 5')
for platform, url in c.fetchall():
    print(f'{platform}: {url}')
"
```

## 💡 Pro Tips

1. Have 2-3 URLs ready before recording
2. Use diverse images (different faces, sources)
3. Let OSINT search complete fully (don't rush)
4. Point to each platform found
5. Show database verification at end

## 🎬 Ready to Record!

```bash
# Start backend
python -m uvicorn api.main:app --port 8000

# In new terminal
python manual_input.py

# Paste your URLs one by one!
```

Good luck! 🚀

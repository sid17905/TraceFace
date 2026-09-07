import requests

# Test with demo image
r = requests.post('http://127.0.0.1:8000/api/v1/scan/url',
    json={'image_url': 'https://upload.wikimedia.org/wikipedia/commons/thumb/3/34/Elon_Musk_Royal_Society_%28crop%29.jpg/800px-Elon_Musk_Royal_Society_%28crop%29.jpg', 'run_osint': True},
    timeout=30
)

result = r.json()
print(f'Status: {r.status_code}')
print(f'Job ID: {result["job_id"]}')
print(f'Face detected: {"bounding_box" in result["scan"]}')
print()
print('Pipeline started! Takes 30-60 seconds for OSINT...')
print('Run this to check: python check_job.py')

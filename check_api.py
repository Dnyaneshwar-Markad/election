import os, requests
BASE = os.getenv('API_URL', 'https://election-are-near-backend.onrender.com/')
print('BASE_URL =', BASE)
try:
    r = requests.get(BASE, timeout=10)
    print('GET / status:', r.status_code)
    print('Body preview:', r.text[:200])
except Exception as e:
    print('GET / failed:', repr(e))

# test login endpoint existence
try:
    r = requests.get(BASE.rstrip('/') + '/docs', timeout=10)
    print('GET /docs status:', r.status_code)
except Exception as e:
    print('GET /docs failed:', repr(e))

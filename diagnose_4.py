import requests
import time
time.sleep(3) # Wait for server to start
try:
    r = requests.get('http://127.0.0.1:8000/')
    print(f"Status Code: {r.status_code}")
    if r.status_code == 500:
        with open('debug_output_4.html', 'w', encoding='utf-8') as f:
            f.write(r.text)
        print("Detailed error saved to debug_output_4.html")
    else:
        print("No 500 error detected by requests.")
except Exception as e:
    print(f"Request failed: {e}")

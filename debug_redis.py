import os
import redis
import sys
from dotenv import load_dotenv

load_dotenv()

HOST = os.getenv('REDIS_HOST')
PORT = os.getenv('REDIS_PORT', 6379)
PASSWORD = os.getenv('REDIS_PASSWORD')

print(f"🕵️ DEBUGGING CONNECTION...")
print(f"Target: {HOST}:{PORT}")

try:
    # Force SSL=True because we know it's Upstash
    r = redis.Redis(
        host=HOST, 
        port=PORT, 
        password=PASSWORD, 
        ssl=True, 
        ssl_cert_reqs=None, 
        socket_connect_timeout=5
    )
    print("⏳ Pinging...")
    r.ping()
    print("✅ SUCCESS! Redis is reachable.")
except Exception as e:
    print(f"\n❌ FAILED. Error details:")
    print(e)
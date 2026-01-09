import redis
import time
import boto3
import json
import os
import sys
from dotenv import load_dotenv

# --- CONFIGURATION ---
load_dotenv()

# Get values securely
REDIS_HOST = os.getenv('REDIS_HOST')
REDIS_PORT = int(os.getenv('REDIS_PORT', 6379))
REDIS_PASSWORD = os.getenv('REDIS_PASSWORD')
SQS_QUEUE_URL = os.getenv('SQS_QUEUE_URL')
AWS_REGION = os.getenv('AWS_REGION', 'ap-south-1')
DYNAMODB_TABLE = os.getenv('DYNAMODB_TABLE')

# --- CONNECT TO RESOURCES ---

# 1. Connect to Redis (With "Smart SSL" for Cloud)
# If the host is just "redis" (local), we don't use SSL. 
# If it's a cloud URL (Upstash), we turn SSL on.
use_ssl = (REDIS_HOST != 'redis')

try:
    r = redis.Redis(
        host=REDIS_HOST,
        port=REDIS_PORT,
        password=REDIS_PASSWORD,
        decode_responses=True,
        ssl=use_ssl,
        ssl_cert_reqs=None # Trust Upstash certificates
    )
    r.ping() # Test connection immediately
    print(f" Connected to Redis at {REDIS_HOST} (SSL={use_ssl})")
except Exception as e:
    print(f" Redis Connection Failed: {e}")
    sys.exit(1) # Crash the worker if Redis is dead

# 2. Connect to AWS SQS
try:
    sqs = boto3.client('sqs', region_name=AWS_REGION)
except Exception as e:
    print(f" AWS SQS Connection Failed: {e}")

# 3. Connect to DynamoDB
try:
    dynamodb = boto3.resource('dynamodb', region_name=AWS_REGION)
    table = dynamodb.Table(DYNAMODB_TABLE)
except Exception as e:
    print(f" DynamoDB Connection Failed: {e}")

# --- LOGIC ---

def process_order(user_id, item_id, receipt_handle):
    lock_key = f"lock:{item_id}"

    # 1. ACQUIRE LOCK (The "Traffic Cop")
    if r.set(lock_key, "LOCKED", nx=True, ex=5):
        print(f" LOCK ACQUIRED: Checking inventory for {item_id}...")

        try:
            # 2. CHECK DATABASE (The "Ledger")
            response = table.get_item(Key={'item_id': item_id})

            if 'Item' in response:
                # ALREADY SOLD
                print(f" REJECTED: {user_id} wants {item_id}, but it is SOLD to {response['Item']['user_id']}")
                # Delete invalid message to stop reprocessing
                sqs.delete_message(QueueUrl=SQS_QUEUE_URL, ReceiptHandle=receipt_handle)

            else:
                # 3. SELL IT
                print(f" SELLING: Item {item_id} to {user_id}...")
                table.put_item(
                    Item={
                        'item_id': item_id,
                        'user_id': user_id,
                        'status': 'SOLD',
                        'timestamp': str(time.time())
                    }
                )
                print(f" SUCCESS: Saved to Database.")

                # 4. CLEANUP
                sqs.delete_message(QueueUrl=SQS_QUEUE_URL, ReceiptHandle=receipt_handle)

        except Exception as e:
            print(f" ERROR: {e}")

        finally:
            # Always release lock
            r.delete(lock_key)

    else:
        print(f" BUSY: {item_id} is locked. Retrying...")
        # Do NOT delete message. SQS will retry automatically.

def poll_queue():
    print(f"Worker listening on {SQS_QUEUE_URL}...")
    while True:
        try:
            # Long Polling (Wait up to 20s for a message)
            response = sqs.receive_message(
                QueueUrl=SQS_QUEUE_URL,
                MaxNumberOfMessages=1,
                WaitTimeSeconds=20
            )

            if 'Messages' in response:
                for msg in response['Messages']:
                    body = json.loads(msg['Body'])
                    receipt_handle = msg['ReceiptHandle']

                    user = body.get('user_id')
                    item = body.get('item_id')

                    print(f" Received: {user} wants {item}")
                    process_order(user, item, receipt_handle)
            else:
                # No messages? Just wait a tiny bit to save CPU
                pass 

        except Exception as e:
            print(f" Polling Error: {e}")
            time.sleep(5) # Wait before retrying if AWS is down

if __name__ == "__main__":
    poll_queue()
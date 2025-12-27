import redis
import time
import boto3
import json
import os
from dotenv import load_dotenv 

# Load secrets from the .env file
load_dotenv() 

# Get values securely
REDIS_HOST = os.getenv('REDIS_HOST')
REDIS_PORT = os.getenv('REDIS_PORT')
REDIS_PASSWORD = os.getenv('REDIS_PASSWORD')
SQS_QUEUE_URL = os.getenv('SQS_QUEUE_URL')


# Connect to Redis
r = redis.Redis(
    host=REDIS_HOST, port=REDIS_PORT, password=REDIS_PASSWORD, decode_responses=True
)

# Connect to SQS
sqs = boto3.client('sqs', region_name='ap-south-1')

# Initialize DynamoDB Resource
dynamodb = boto3.resource('dynamodb', region_name='ap-south-1')
table = dynamodb.Table('FluxOrders')

def process_order(user_id, item_id, receipt_handle):
    lock_key = f"lock:{item_id}"
    
    # 1. ACQUIRE LOCK (The "Traffic Cop")
    # This stops 2 people from checking the database at the exact same moment
    if r.set(lock_key, "LOCKED", nx=True, ex=5):
        print(f"LOCK ACQUIRED: Checking inventory for {item_id}...")
        
        try:
            # 2. CHECK DATABASE (The "Ledger")
            # Does this item already exist in the sold table?
            response = table.get_item(Key={'item_id': item_id})
            
            if 'Item' in response:
                # IT IS ALREADY SOLD
                print(f" REJECTED: {user_id} wants {item_id}, but it is ALREADY SOLD to {response['Item']['user_id']}")
                # We still delete the message because the order is invalid/done
                sqs.delete_message(QueueUrl=SQS_QUEUE_URL, ReceiptHandle=receipt_handle)
                
            else:
                # 3. SELL IT (Save to DB)
                print(f"SELLING: Item {item_id} to {user_id}...")
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
            # Always release the lock so others can check (and get rejected)
            r.delete(lock_key)
        
    else:
        print(f" BUSY: {item_id} is currently being processed. Leaving in queue for retry.")
        # We DO NOT delete the message. SQS will retry it later

def poll_queue():
    print("Worker is listening for orders...")
    while True:
        # Ask SQS for messages (Long Polling for 10 seconds)
        response = sqs.receive_message(
            QueueUrl=SQS_QUEUE_URL,
            MaxNumberOfMessages=1,
            WaitTimeSeconds=10
        )
        
        if 'Messages' in response:
            for msg in response['Messages']:
                body = json.loads(msg['Body'])
                receipt_handle = msg['ReceiptHandle']
                
                user = body.get('user_id')
                item = body.get('item_id')
                
                print(f"Received Order: {user} wants {item}")
                process_order(user, item, receipt_handle)
        else:
            print(".", end="", flush=True) # Print a dot to show it's alive

if __name__ == "__main__":
    poll_queue()
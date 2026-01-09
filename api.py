from flask import Flask, request, jsonify
import boto3
import os
import json
from dotenv import load_dotenv

load_dotenv()

app = Flask(__name__)

# Config
AWS_REGION = os.getenv("AWS_REGION", "ap-south-1")
SQS_QUEUE_URL = os.getenv("SQS_QUEUE_URL")

try:
    sqs = boto3.client('sqs', region_name=AWS_REGION)
except Exception as e:
    print(f"Warning: AWS Connection failed. {e}")
    sqs = None

@app.route('/buy', methods=['POST', 'OPTIONS']) # <--- ALLOW OPTIONS EXPLICITLY
def buy():
    # 1. MANUAL CORS HANDSHAKE
    # If the browser asks "Can I come in?", we say YES immediately.
    if request.method == 'OPTIONS':
        response = jsonify({'status': 'CORS OK'})
        response.headers.add('Access-Control-Allow-Origin', '*')
        response.headers.add('Access-Control-Allow-Headers', 'Content-Type,Authorization')
        response.headers.add('Access-Control-Allow-Methods', 'POST,OPTIONS')
        return response

    # 2. STANDARD POST LOGIC
    # We also add the headers to the main response so the browser accepts the data.
    
    # Validation
    data = request.json
    if not data or 'user_id' not in data or 'item_id' not in data:
        response = jsonify({'error': 'Missing user_id or item_id'})
        response.status_code = 400
        response.headers.add('Access-Control-Allow-Origin', '*') # <--- Add Header
        return response

    if not SQS_QUEUE_URL:
        response = jsonify({'error': 'Queue URL missing'})
        response.status_code = 500
        response.headers.add('Access-Control-Allow-Origin', '*') # <--- Add Header
        return response

    try:
        sqs.send_message(
            QueueUrl=SQS_QUEUE_URL,
            MessageBody=json.dumps(data)
        )
        response = jsonify({'message': 'Order received', 'order': data})
        response.status_code = 200
        response.headers.add('Access-Control-Allow-Origin', '*') # <--- Add Header
        return response
    
    except Exception as e:
        response = jsonify({'error': str(e)})
        response.status_code = 500
        response.headers.add('Access-Control-Allow-Origin', '*') # <--- Add Header
        return response

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000)
from flask import Flask, request, jsonify
from flask_cors import CORS  # <--- NEW IMPORT
import boto3
import os
import json
from dotenv import load_dotenv

# Load env vars
load_dotenv()

app = Flask(__name__)
CORS(app) # <--- ENABLE CORS SO FRONTEND CAN TALK TO IT

# Config
AWS_REGION = os.getenv("AWS_REGION", "ap-south-1")
SQS_QUEUE_URL = os.getenv("SQS_QUEUE_URL")

# Set up AWS Client
try:
    sqs = boto3.client('sqs', region_name=AWS_REGION)
except Exception as e:
    print(f"Warning: AWS Connection failed. {e}")
    sqs = None

@app.route('/buy', methods=['POST'])
def buy():
    # 1. Input Validation (KEEPS TEST #1 HAPPY)
    data = request.json
    if not data or 'user_id' not in data or 'item_id' not in data:
        return jsonify({'error': 'Missing user_id or item_id'}), 400

    # 2. Safety Check (KEEPS TEST #2 HAPPY)
    if not SQS_QUEUE_URL:
        return jsonify({'error': 'Server Misconfiguration: Queue URL missing'}), 500

    try:
        # 3. Send to SQS
        sqs.send_message(
            QueueUrl=SQS_QUEUE_URL,
            MessageBody=json.dumps(data)
        )
        return jsonify({'message': 'Order received', 'order': data}), 200
    
    except Exception as e:
        return jsonify({'error': str(e)}), 500

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000)
from flask import Flask, request, jsonify
from flask_cors import CORS
import boto3
import os
import json
from dotenv import load_dotenv

load_dotenv()

app = Flask(__name__)

# 1. Enable CORS for everything (The Standard Way)
CORS(app, resources={r"/*": {"origins": "*"}})

# 2. THE NUCLEAR OPTION (The Manual Override)
# This forces the headers onto every response, no matter what.
@app.after_request
def after_request(response):
    response.headers.add('Access-Control-Allow-Origin', '*')
    response.headers.add('Access-Control-Allow-Headers', 'Content-Type,Authorization')
    response.headers.add('Access-Control-Allow-Methods', 'GET,PUT,POST,DELETE,OPTIONS')
    return response

# Config
AWS_REGION = os.getenv("AWS_REGION", "ap-south-1")
SQS_QUEUE_URL = os.getenv("SQS_QUEUE_URL")

try:
    sqs = boto3.client('sqs', region_name=AWS_REGION)
except Exception as e:
    print(f"Warning: AWS Connection failed. {e}")
    sqs = None

@app.route('/buy', methods=['POST'])
def buy():
    # Input Validation
    data = request.json
    if not data or 'user_id' not in data or 'item_id' not in data:
        return jsonify({'error': 'Missing user_id or item_id'}), 400

    # Safety Check
    if not SQS_QUEUE_URL:
        return jsonify({'error': 'Server Misconfiguration: Queue URL missing'}), 500

    try:
        sqs.send_message(
            QueueUrl=SQS_QUEUE_URL,
            MessageBody=json.dumps(data)
        )
        return jsonify({'message': 'Order received', 'order': data}), 200
    
    except Exception as e:
        return jsonify({'error': str(e)}), 500

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000)
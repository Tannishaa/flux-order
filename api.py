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
DYNAMODB_TABLE = os.getenv("DYNAMODB_TABLE", "FluxOrdersIAC") # <--- Ensure this matches your table name

# AWS Clients
try:
    sqs = boto3.client('sqs', region_name=AWS_REGION)
    # CONNECT TO DYNAMODB
    dynamodb = boto3.resource('dynamodb', region_name=AWS_REGION)
    table = dynamodb.Table(DYNAMODB_TABLE)
except Exception as e:
    print(f"Warning: AWS Connection failed. {e}")
    sqs = None
    table = None

# --- 1. GET INVENTORY (New!) ---
@app.route('/inventory', methods=['GET'])
def get_inventory():
    if not table:
        return jsonify([]), 500
    
    try:
        # Scan returns everything. (In production, we'd query, but Scan is fine here)
        response = table.scan(ProjectionExpression='item_id')
        items = response.get('Items', [])
        # Convert to a simple list: ['A1', 'B2', 'C3']
        sold_ids = [item['item_id'] for item in items]
        
        # MANUAL CORS (Since we are in manual mode)
        resp = jsonify(sold_ids)
        resp.headers.add('Access-Control-Allow-Origin', '*')
        return resp
    except Exception as e:
        return jsonify({'error': str(e)}), 500

# --- 2. BUY TICKET ---
@app.route('/buy', methods=['POST', 'OPTIONS'])
def buy():
    # CORS HANDSHAKE
    if request.method == 'OPTIONS':
        response = jsonify({'status': 'CORS OK'})
        response.headers.add('Access-Control-Allow-Origin', '*')
        response.headers.add('Access-Control-Allow-Headers', 'Content-Type,Authorization')
        response.headers.add('Access-Control-Allow-Methods', 'POST,OPTIONS')
        return response

    # VALIDATION
    data = request.json
    if not data or 'user_id' not in data or 'item_id' not in data:
        response = jsonify({'error': 'Missing user_id or item_id'})
        response.status_code = 400
        response.headers.add('Access-Control-Allow-Origin', '*')
        return response

    try:
        # SEND TO WORKER
        sqs.send_message(
            QueueUrl=SQS_QUEUE_URL,
            MessageBody=json.dumps(data)
        )
        response = jsonify({'message': 'Order received', 'order': data})
        response.status_code = 200
        response.headers.add('Access-Control-Allow-Origin', '*')
        return response
    
    except Exception as e:
        response = jsonify({'error': str(e)})
        response.status_code = 500
        response.headers.add('Access-Control-Allow-Origin', '*')
        return response

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000)
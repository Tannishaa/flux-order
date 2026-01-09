from flask import Flask, request, jsonify
from flask_cors import CORS  # <--- NEW IMPORT
import boto3
import json
import os
from dotenv import load_dotenv

load_dotenv()

app = Flask(__name__)
CORS(app) # <--- THIS ENABLED CROSS-ORIGIN REQUESTS

# Load Config
SQS_QUEUE_URL = os.getenv('SQS_QUEUE_URL')
AWS_REGION = os.getenv('AWS_REGION', 'ap-south-1')

# Connect to SQS
try:
    sqs = boto3.client('sqs', region_name=AWS_REGION)
except Exception as e:
    print(f"Error connecting to AWS: {e}")

@app.route('/buy', methods=['POST'])
def buy_ticket():
    try:
        data = request.json
        
        # Send to SQS
        sqs.send_message(
            QueueUrl=SQS_QUEUE_URL,
            MessageBody=json.dumps(data)
        )
        return jsonify({"message": "Order Received", "status": "queued"}), 200

    except Exception as e:
        return jsonify({"error": str(e)}), 500

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000)
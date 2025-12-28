import boto3
import json
import uuid
from flask import Flask, request, jsonify

app = Flask(__name__)

import os
from dotenv import load_dotenv

# Load secrets from the .env file
load_dotenv()
SQS_QUEUE_URL = os.getenv('SQS_QUEUE_URL')  # SQS QUEUE URL
AWS_REGION = "ap-south-1"

# Initialize SQS
sqs = boto3.client('sqs', region_name=AWS_REGION)

@app.route('/buy', methods=['POST'])
def buy_ticket():
    try:
        # 1. Get User Data
        data = request.json
        user_id = data.get('user_id')
        item_id = data.get('item_id', 'ticket_001') # Default to Ticket 1
        
        # 2. Generate a Unique Order ID
        order_id = str(uuid.uuid4())
        
        # 3. Create the Message Payload
        message_body = {
            "order_id": order_id,
            "user_id": user_id,
            "item_id": item_id,
            "status": "PENDING"
        }
        
        # 4. Push to SQS (The "Waiting Room")
        response = sqs.send_message(
            QueueUrl=SQS_QUEUE_URL,
            MessageBody=json.dumps(message_body)
        )
        
        # 5. Instant Response to User
        return jsonify({
            "message": "Order Received! You are in line.",
            "order_id": order_id,
            "queue_msg_id": response['MessageId']
        }), 200

    except Exception as e:
        return jsonify({"error": str(e)}), 500

if __name__ == '__main__':
    # host='0.0.0.0' allows connections from outside the container
    app.run(host='0.0.0.0', port=5000, debug=True)
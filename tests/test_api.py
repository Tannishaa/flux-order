import pytest
from unittest.mock import patch, MagicMock
from api import app

# This 'fixture' creates a fake client for us to test
@pytest.fixture
def client():
    app.config['TESTING'] = True
    with app.test_client() as client:
        yield client

# Test 1: Does the API reject bad data? (Missing user_id)
def test_buy_missing_data(client):
    # Send an empty JSON
    response = client.post('/buy', json={})
    
    # We expect a 400 Bad Request error
    assert response.status_code == 400
    assert b"Missing user_id or item_id" in response.data

# Test 2: Does the API work when data is correct?
# We use @patch to FAKE the SQS connection so we don't need real AWS
@patch('api.sqs') 
def test_buy_success(mock_sqs, client):
    # Setup the data
    payload = {"user_id": "test_user", "item_id": "ticket_123"}
    
    # Call the API
    response = client.post('/buy', json=payload)
    
    # Assertions
    assert response.status_code == 200
    assert b"Order received" in response.data
    
    # Verify our code actually tried to send a message to SQS
    mock_sqs.send_message.assert_called_once()
# retail-pricing-agent-ai-ingestor-test/run_ingestor_test.py
import os
import json
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv() 

# Set environment variables for the agent (these are picked up by app.py)
os.environ['RAW_DATA_S3_BUCKET'] = os.getenv('RAW_DATA_S3_BUCKET')
os.environ['MARKET_DATA_TABLE'] = os.getenv('MARKET_DATA_TABLE')
os.environ['INVENTORY_TABLE'] = os.getenv('INVENTORY_TABLE')
os.environ['AWS_REGION'] = os.getenv('AWS_REGION')

# Import the lambda_handler function from the agent's app.py
from lambda_functions.market_data_ingestor.app import lambda_handler

# The EXACT initial dummy data you provided
raw_dummy_data_list = [
    {"sku_id": "SKU001", "competitor_name": "CompA", "price": 2.89, "timestamp": "2025-07-11T19:00:00Z", "region": "NYC"},
    {"sku_id": "SKU001", "competitor_name": "CompB", "price": 2.95, "timestamp": "2025-07-11T19:05:00Z", "region": "NYC"},
    {"sku_id": "SKU005", "competitor_name": "CompC", "price": 98.0, "timestamp": "2025-07-11T19:10:00Z", "region": "LA"}
]

# The lambda_handler expects an event object with a 'body' key.
# The 'body' key's value should be a JSON string representing this list.
event_data = {
    "body": json.dumps(raw_dummy_data_list)
}

print("\n--- Executing Market Data Ingestor Agent ---")
response = lambda_handler(event_data, {}) # Call the handler with the event data and an empty context
print(f"Agent Execution Response (Status Code): {response['statusCode']}")
print(f"Agent Execution Response (Body): {response['body']}")
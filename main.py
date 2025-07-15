import os
import json
import time
from flask import Flask, request, jsonify
from dotenv import load_dotenv
from flask_cors import CORS # Add this line

# Load environment variables from .env file
load_dotenv()

# --- ADD THESE PRINT STATEMENTS FOR DEBUGGING ---
print(f"DEBUG: AWS_REGION from .env: {os.getenv('AWS_REGION')}")
print(f"DEBUG: MARKET_DATA_TABLE from .env: {os.getenv('MARKET_DATA_TABLE')}")
print(f"DEBUG: INVENTORY_TABLE from .env: {os.getenv('INVENTORY_TABLE')}")
print(f"DEBUG: DEMAND_FORECASTS_TABLE from .env: {os.getenv('DEMAND_FORECASTS_TABLE')}")
print(f"DEBUG: CUSTOMER_PROFILES_TABLE from .env: {os.getenv('CUSTOMER_PROFILES_TABLE')}")
print(f"DEBUG: PRICING_PROMO_RECOMMENDATIONS_TABLE from .env: {os.getenv('PRICING_PROMO_RECOMMENDATIONS_TABLE')}")
print(f"DEBUG: PRICE_SYNC_LOG_TABLE from .env: {os.getenv('PRICE_SYNC_LOG_TABLE')}")
print(f"DEBUG: BEDROCK_MODEL_ID from .env: {os.getenv('BEDROCK_MODEL_ID')}")
print(f"DEBUG: STEP_FUNCTIONS_STATE_MACHINE_ARN from .env: {os.getenv('STEP_FUNCTIONS_STATE_MACHINE_ARN')}")
print(f"DEBUG: MOCK_ECOMMERCE_API_ENDPOINT from .env: {os.getenv('MOCK_ECOMMERCE_API_ENDPOINT')}")
# --- END DEBUG PRINT STATEMENTS ---

# Import simulated Lambda handlers
from lambda_functions.market_data_ingestor.app import lambda_handler as market_data_ingestor_handler
from lambda_functions.demand_forecast_agent.app import lambda_handler as demand_forecast_agent_handler
from lambda_functions.promotion_strategy_agent.app import lambda_handler as promotion_strategy_agent_handler
from lambda_functions.real_time_price_sync_agent.app import lambda_handler as real_time_price_sync_agent_handler
from lambda_functions.ui_backend.app import lambda_handler as ui_backend_handler

app = Flask(__name__)
CORS(app) # Add this line to enable CORS for all routes

# --- Mock E-commerce System (for Price Sync Agent) ---
# This simulates your retail system's product catalog
# In a real system, this would be a database.
mock_ecommerce_products = {
    "P001": {"name": "Ultra HD Smart TV 55-inch", "current_price": 999.99},
    "P002": {"name": "Noise-Cancelling Headphones", "current_price": 199.99},
    "P003": {"name": "Ergonomic Office Chair", "current_price": 349.00},
    "P004": {"name": "Portable Bluetooth Speaker", "current_price": 79.99},
    "P005": {"name": "Smart Home Security Camera", "current_price": 129.00}
}

@app.route('/mock-api/update_price', methods=['POST'])
def mock_update_price():
    data = request.json
    sku = data.get('sku')
    new_price = data.get('new_price')
    if sku in mock_ecommerce_products:
        old_price = mock_ecommerce_products[sku]['current_price']
        mock_ecommerce_products[sku]['current_price'] = new_price
        print(f"MOCK E-COMMERCE: Updated SKU {sku} price from {old_price} to {new_price}")
        return jsonify({"status": "success", "message": f"Price for {sku} updated to {new_price}"}), 200
    return jsonify({"status": "error", "message": f"SKU {sku} not found"}), 404

@app.route('/mock-api/activate_promo', methods=['POST'])
def mock_activate_promo():
    data = request.json
    sku = data.get('sku')
    promo_details = data.get('promo_details')
    print(f"MOCK E-COMMERCE: Activated promo for SKU {sku}: {promo_details}")
    return jsonify({"status": "success", "message": f"Promotion for {sku} activated"}), 200

# --- Local API Gateway Simulation (for UI Backend) ---
@app.route('/api/<path:subpath>', methods=['GET', 'POST'])
def ui_api_gateway(subpath):
    # Simulate API Gateway event structure
    event = {
        'path': f'/api/{subpath}',
        'httpMethod': request.method,
        'headers': dict(request.headers),
        'queryStringParameters': request.args,
        'body': request.data.decode('utf-8') if request.data else None,
        'isBase64Encoded': False
    }
    
    # Call the UI Backend Lambda handler
    response = ui_backend_handler(event, {})
    
    # Parse Lambda response and return to frontend
    status_code = response.get('statusCode', 200)
    headers = response.get('headers', {})
    body = response.get('body', '{}')
    
    # Ensure CORS headers are present for local development
    headers['Access-Control-Allow-Origin'] = '*'
    headers['Access-Control-Allow-Headers'] = 'Content-Type,Authorization'
    headers['Access-Control-Allow-Methods'] = 'GET,POST,PUT,DELETE,OPTIONS'

    return app.response_class(
        response=body,
        status=status_code,
        headers=headers,
        mimetype=headers.get('Content-Type', 'application/json')
    )

@app.route('/api/<path:subpath>', methods=['OPTIONS'])
def handle_options(subpath):
    # Handle CORS preflight requests
    response = jsonify({})
    response.headers['Access-Control-Allow-Origin'] = '*'
    response.headers['Access-Control-Allow-Headers'] = 'Content-Type,Authorization'
    response.headers['Access-Control-Allow-Methods'] = 'GET,POST,PUT,DELETE,OPTIONS'
    return response, 200

# --- Local Agent Orchestration (Simulated Step Functions) ---
@app.route('/trigger-full-agent-run', methods=['POST'])
def trigger_full_agent_run():
    """
    Simulates a full workflow run of all agents.
    In a real AWS setup, this would be a Step Functions execution.
    """
    print("\n--- Triggering Full Agent Workflow (Simulated) ---")
    
    # 1. Market Data Ingestor
    print("\n[Agent 1/4] Running Market Data Ingestor Agent...")
    ingestor_response = market_data_ingestor_handler({}, {})
    ingested_data = json.loads(ingestor_response['body']).get('data', [])
    print(f"Ingestor result: {ingestor_response['statusCode']}")

    # 2. Demand Forecast Agent
    print("\n[Agent 2/4] Running Demand Forecast Agent...")
    # Pass ingested data to forecast agent (simulating Step Functions data flow)
    forecast_event = {'ingested_data': json.dumps(ingested_data)}
    forecast_response = demand_forecast_agent_handler(forecast_event, {})
    forecasts = json.loads(forecast_response['body']).get('forecasts', [])
    print(f"Forecast result: {forecast_response['statusCode']}")

    # 3. Promotion Strategy Agent
    print("\n[Agent 3/4] Running Promotion Strategy Agent...")
    # Pass forecasts to strategy agent
    strategy_event = {'forecasts_output': json.dumps(forecasts)}
    strategy_response = promotion_strategy_agent_handler(strategy_event, {})
    pricing_recommendations = json.loads(strategy_response['body']).get('pricing_recommendations', [])
    promotion_ideas = json.loads(strategy_response['body']).get('promotion_ideas', [])
    print(f"Strategy result: {strategy_response['statusCode']}")
    print(f"Generated {len(pricing_recommendations)} pricing recommendations.")
    print(f"Generated {len(promotion_ideas)} promotion ideas.")

    # 4. Real-Time Price Sync Agent (Simulate applying recommendations)
    # In a real system, there might be a human approval step here.
    # For this demo, we'll just pass the generated pricing recommendations.
    print("\n[Agent 4/4] Running Real-Time Price Sync Agent (applying recommendations)...")
    sync_event = {'actions_to_sync': json.dumps(pricing_recommendations)}
    sync_response = real_time_price_sync_agent_handler(sync_event, {})
    sync_results = json.loads(sync_response['body']).get('sync_results', [])
    print(f"Sync result: {sync_response['statusCode']}")
    print(f"Sync results: {json.dumps(sync_results, indent=2)}")

    print("\n--- Full Agent Workflow Completed (Simulated) ---")
    return jsonify({"message": "Full agent workflow simulated successfully.", "details": sync_results}), 200

if __name__ == '__main__':
    # Ensure all requirements are installed for the main.py
    # pip install Flask python-dotenv requests
    
    # Run Flask app on port 5000 (UI Backend) and 5001 (Mock E-commerce API)
    # Use different ports for clarity, or integrate mock_api routes directly into /api/ if preferred.
    # For simplicity, we'll run the main app on 5000 and the mock e-commerce on 5001.
    # The MOCK_ECOMMERCE_API_ENDPOINT in .env points to 5001.
    
    # Start the mock e-commerce API in a separate thread/process if needed,
    # but for simple POST requests, Flask can handle both.
    # We'll run the mock e-commerce API on /mock-api/ paths within the same Flask app.
    
    print(f"Starting local Flask server on port {os.getenv('PORT', 5000)}...")
    print(f"UI Backend API: http://127.0.0.1:{os.getenv('PORT', 5000)}/api/products")
    print(f"Mock E-commerce API: http://127.0.0.1:{os.getenv('PORT', 5000)}/mock-api/update_price")
    print(f"Trigger Full Agent Run: http://127.0.0.1:{os.getenv('PORT', 5000)}/trigger-full-agent-run (POST)")
    
    app.run(debug=True, port=os.getenv('PORT', 5000))
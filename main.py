import os
import json
import time
from flask import Flask, request, jsonify
from dotenv import load_dotenv
from flask_cors import CORS # Ensure this is installed: pip install Flask-Cors

# Load environment variables from .env file
# This makes environment variables defined in .env accessible via os.getenv()
load_dotenv()

# --- DEBUG: Print Environment Variables on Startup ---
# This helps verify that your .env file is being read correctly
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
print(f"DEBUG: MOCK_MARKET_DATA_API_ENDPOINT from .env: {os.getenv('MOCK_MARKET_DATA_API_ENDPOINT')}")
print(f"DEBUG: SNS_PROMOTION_TOPIC_ARN from .env: {os.getenv('SNS_PROMOTION_TOPIC_ARN')}") # Added for completeness
# --- END DEBUG PRINTS ---

# Import simulated Lambda handlers from their respective app.py files
# In this local simulation, these are treated as local Python modules.
# In a real AWS deployment, these would be actual Lambda functions invoked by Step Functions or API Gateway.
from lambda_functions.market_data_ingestor.app import lambda_handler as market_data_ingestor_handler
from lambda_functions.demand_forecast_agent.app import lambda_handler as demand_forecast_agent_handler
from lambda_functions.promotion_strategy_agent.app import lambda_handler as promotion_strategy_agent_handler
from lambda_functions.real_time_price_sync_agent.app import lambda_handler as real_time_price_sync_agent_handler
from lambda_functions.ui_backend.app import lambda_handler as ui_backend_handler

# Initialize the Flask application
app = Flask(__name__)

# Enable CORS (Cross-Origin Resource Sharing) for all routes.
# This is crucial for allowing your React frontend (e.g., on localhost:1234)
# to make requests to this Flask backend (e.g., on localhost:5000).
# Flask-CORS handles preflight (OPTIONS) requests automatically for routes
# where the HTTP methods are explicitly defined.
CORS(app) 

# --- Mock E-commerce System (for Price Sync Agent) ---
# This dictionary simulates your retail system's product catalog for price updates.
# In a real system, this would be a live e-commerce platform's API or a persistent database.
mock_ecommerce_products = {
    "P001": {"name": "Ultra-Light Laptop Pro", "current_price": 999.99},
    "P002": {"name": "Next-Gen Smartphone X", "current_price": 199.99},
    "P003": {"name": "Premium Noise-Cancelling Headphones", "current_price": 299.99},
    "P004": {"name": "Smart Home Security Camera", "current_price": 129.99},
    "P005": {"name": "Ergonomic Office Chair", "current_price": 499.99}
}

@app.route('/mock-api/update_price', methods=['POST'])
def mock_update_price():
    """
    Simulates an external e-commerce API endpoint for updating product prices.
    This endpoint is called by the RealTimePriceSyncAgent.
    """
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
    """
    Simulates an external e-commerce API endpoint for activating promotions.
    This endpoint could be called by a future agent or system.
    """
    data = request.json
    sku = data.get('sku')
    promo_details = data.get('promo_details')
    print(f"MOCK E-COMMERCE: Activated promo for SKU {sku}: {promo_details}")
    return jsonify({"status": "success", "message": f"Promotion for {sku} activated"}), 200

@app.route('/mock-api/market-data', methods=['GET'])
def get_mock_market_data():
    """
    Mock endpoint to serve dummy competitor pricing data.
    This simulates an external market data API and is called by the MarketDataIngestorAgent.
    """
    try:
        # Path to the dummy JSON file is relative to main.py
        with open(os.path.join(os.path.dirname(__file__), 'data', 'dummy_competitor_pricing.json'), 'r') as f:
            data = json.load(f)
        print("DEBUG: Served mock market data from /mock-api/market-data")
        return jsonify(data), 200
    except Exception as e:
        print(f"ERROR: Failed to serve mock market data: {e}")
        return jsonify({"error": "Failed to load mock market data"}), 500

# --- Local API Gateway Simulation (for UI Backend and other direct UI calls) ---
# This route catches all requests starting with /api/ and passes them to the ui_backend_handler.
@app.route('/api/<path:subpath>', methods=['GET', 'POST'])
def ui_api_gateway(subpath):
    """
    Simulates AWS API Gateway routing requests to the ui_backend Lambda handler.
    Handles GET and POST requests from the React frontend for paths like /api/products, /api/generate-promo-idea.
    """
    # Construct a basic event object similar to what Lambda receives from API Gateway
    event = {
        'path': f'/api/{subpath}',
        'httpMethod': request.method,
        'headers': dict(request.headers),
        'queryStringParameters': request.args,
        'body': request.data.decode('utf-8') if request.data else None,
        'isBase64Encoded': False # Assuming non-base64 encoded body for this demo
    }
    
    print(f"UI Backend triggered: {request.method} /api/{subpath} (via main.py API Gateway simulation)")
    
    # Call the UI Backend Lambda handler (simulating Lambda invocation)
    response = ui_backend_handler(event, {})
    
    # Parse Lambda-style response and return to frontend
    status_code = response.get('statusCode', 200)
    headers = response.get('headers', {})
    body = response.get('body', '{}')
    
    # Flask-CORS (CORS(app)) handles global CORS headers, so manual addition here is redundant.
    
    return app.response_class(
        response=body,
        status=status_code,
        headers=headers,
        mimetype=headers.get('Content-Type', 'application/json')
    )

# --- Specific Route for Applying Recommendations ---
# This route is directly called by the frontend's applyRecommendation function.
# It's outside the /api/ prefix because it's a direct action, not a generic API Gateway route.
@app.route('/apply-recommendation', methods=['POST'])
def apply_recommendation_route():
    """
    Handles the request from the UI to apply a specific recommendation.
    It constructs an event for the ui_backend_handler to process.
    """
    # The ui_backend_handler's /api/apply-recommendation path expects the full recommendation object
    # from the frontend.
    event = {
        'path': '/api/apply-recommendation', # This is the internal path the ui_backend_handler expects
        'httpMethod': 'POST',
        'body': request.data.decode('utf-8') # Pass the raw JSON body from the frontend
    }
    print(f"UI Backend triggered: POST /apply-recommendation (via main.py route)")
    response = ui_backend_handler(event, None) # Call the ui_backend_handler
    return jsonify(json.loads(response['body'])), response['statusCode']

# --- OPTIONS route for /apply-recommendation (for CORS preflight) ---
# This is crucial to ensure the browser's preflight request gets a 200 OK.
@app.route('/apply-recommendation', methods=['OPTIONS'])
def handle_apply_recommendation_options():
    """
    Handles CORS preflight requests for the /apply-recommendation endpoint.
    Ensures a 200 OK status with necessary CORS headers for the browser to proceed.
    """
    response = jsonify({})
    # These headers are provided by Flask-CORS, but explicitly defining them here
    # can sometimes resolve specific browser preflight issues for direct routes.
    response.headers['Access-Control-Allow-Origin'] = '*'
    response.headers['Access-Control-Allow-Headers'] = 'Content-Type,Authorization'
    response.headers['Access-Control-Allow-Methods'] = 'POST,OPTIONS' # Only methods allowed for this specific endpoint
    print("DEBUG: Handled OPTIONS for /apply-recommendation with 200 OK.")
    return response, 200

# --- Local Agent Orchestration (Simulated Step Functions Workflow) ---
# This route triggers the entire pipeline of agents sequentially.
@app.route('/trigger-full-agent-run', methods=['POST'])
def trigger_full_agent_run():
    """
    Simulates a full workflow run of all agents, mimicking a Step Functions execution.
    Each agent's lambda_handler is called directly in sequence.
    """
    print("\n--- Triggering Full Agent Workflow (Simulated) ---")
    
    # 1. Market Data Ingestor Agent
    print("\n[Agent 1/4] Running Market Data Ingestor Agent...")
    # This agent fetches its own data (from mock API or local file) and writes to DynamoDB.
    ingestor_response = market_data_ingestor_handler({}, {})
    print(f"Ingestor result: {ingestor_response['statusCode']}")

    # 2. Demand Forecast Agent
    print("\n[Agent 2/4] Running Demand Forecast Agent...")
    # This agent scans DynamoDB tables itself; no input needed from previous agent.
    forecast_response = demand_forecast_agent_handler({}, {})
    print(f"Forecast result: {forecast_response['statusCode']}")

    # 3. Promotion Strategy Agent
    print("\n[Agent 3/4] Running Promotion Strategy Agent...")
    # This agent scans DynamoDB tables itself; no input needed from previous agent.
    strategy_response = promotion_strategy_agent_handler({}, {})
    pricing_recommendations = json.loads(strategy_response['body']).get('pricing_recommendations', [])
    promotion_ideas = json.loads(strategy_response['body']).get('promotion_ideas', [])
    print(f"Strategy result: {strategy_response['statusCode']}")
    print(f"Generated {len(pricing_recommendations)} pricing recommendations.")
    print(f"Generated {len(promotion_ideas)} promotion ideas.")

    # 4. Real-Time Price Sync Agent (Simulate applying recommendations)
    # This agent is designed to be triggered with specific recommendations to sync.
    # We pass the generated pricing recommendations (if any) to it.
    print("\n[Agent 4/4] Running Real-Time Price Sync Agent (applying recommendations)...")
    # The real_time_price_sync_agent_handler expects a list of recommendations under the 'recommendations' key
    sync_event = {'recommendations': pricing_recommendations} 
    sync_response = real_time_price_sync_agent_handler(sync_event, {})
    sync_results = json.loads(sync_response['body']).get('sync_results', [])
    print(f"Sync result: {sync_response['statusCode']}")
    print(f"Sync results: {json.dumps(sync_results, indent=2)}")

    print("\n--- Full Agent Workflow Completed (Simulated) ---")
    return jsonify({"message": "Full agent workflow simulated successfully.", "details": sync_results}), 200

if __name__ == '__main__':
    # Ensure all Python requirements are installed for main.py:
    # pip install Flask python-dotenv requests Flask-Cors
    
    # The Flask app will run on the port specified in .env (defaulting to 5000).
    # All mock APIs and the UI Backend API will be served from this single Flask app.
    # IMPORTANT: Ensure MOCK_ECOMMERCE_API_ENDPOINT and MOCK_MARKET_DATA_API_ENDPOINT
    # in your .env file point to http://127.0.0.1:5000/... for consistency.
    
    port = os.getenv('PORT', 5000)
    print(f"Starting local Flask server on port {port}...")
    print(f"UI Backend API: http://127.0.0.1:{port}/api/products")
    print(f"Mock E-commerce Price Update API: http://127.0.0.1:{port}/mock-api/update_price")
    print(f"Mock Market Data API: http://127.0.0.1:{port}/mock-api/market-data")
    print(f"Trigger Full Agent Run: http://127.0.0.1:{port}/trigger-full-agent-run (POST)")
    print(f"Apply Recommendation Endpoint: http://127.0.0.1:{port}/apply-recommendation (POST/OPTIONS)")
    
    app.run(debug=True, port=port)
Agentic AI Retail Pricing Agnet
🚀 Project Overview
The Agentic AI Retail Optimizer is a demonstration of a modern, cloud-native application designed to revolutionize retail pricing and promotion strategies. It leverages intelligent AI agents, serverless architecture on AWS, and real-time data processing to provide dynamic price recommendations and personalized promotional ideas. This project showcases how AI-driven automation can enhance business agility and profitability in the retail sector.

---

✨ Features
This application provides the following core functionalities:

Dynamic Product Dashboard: A real-time overview of product inventory, current prices, and key metrics.

Automated Agent Workflow Trigger: Initiate a full cycle of AI agents (market data ingestion, demand forecasting, promotion strategy, price sync) with a single click.

Intelligent Price Recommendations: Generates data-driven price adjustments for products based on market conditions, inventory levels, and demand forecasts.

AI-Powered Promotion Idea Generation: Utilizes Large Language Models (LLMs) via Amazon Bedrock to create creative and targeted promotional campaign ideas for specific products and customer segments.

Recommendation Management: View and apply pending price recommendations directly from the UI, simulating real-world price updates.

Real-time Data Sync (Simulated): The RealTimePriceSyncAgent simulates updating an external e-commerce system with new prices, and logs these actions.

Cloud-Native Architecture: Built on AWS serverless technologies for scalability, reliability, and cost-efficiency.


Architecture and Structure
The project is structured into a frontend (React), a local Python backend (Flask acting as a local API Gateway/orchestrator), and several AWS cloud services that the local backend interacts with.

``````

retail-pricing-optimizer/
├── data/
│   ├── dummy_competitor_pricing.json
│   ├── dummy_pos_data.json
│   ├── dummy_inventory_data.json
│   └── dummy_customer_profiles.json 
├── frontend/
│   ├── public/
│   │   └── index.html                 # Main HTML file for React app
│   ├── src/
│   │   ├── components/
│   │   │   ├── AIPromoGenerator.js    # UI for AI promo generation
│   │   │   ├── Dashboard.js           # UI for dashboard overview
│   │   │   └── ProductCard.js         # Reusable product display component
│   │   ├── App.js                     # Main React application component
│   │   └── index.js                   # React entry point
│   ├── package.json                   # Node.js dependencies for frontend
├── lambda_functions/
│   ├── market_data_ingestor/
│   │   ├── app.py                     # Lambda code: Ingests market data
│   │   └── requirements.txt
│   ├── demand_forecast_agent/
│   │   ├── app.py                     # Lambda code: Forecasts demand
│   │   └── requirements.txt
│   ├── promotion_strategy_agent/
│   │   ├── app.py                     # Lambda code: Generates pricing/promo strategies
│   │   └── requirements.txt
│   ├── real_time_price_sync_agent/
│   │   ├── app.py                     # Lambda code: Syncs prices to mock e-commerce
│   │   └── requirements.txt
│   ├── ui_backend/
│   │   ├── app.py                     # Lambda code: Serves UI data, triggers workflows
│   │   └── requirements.txt
├── main.py                            # Local Flask backend server (orchestrates local agent calls, mock API)
├── requirements.txt                   # Python dependencies for main.py
└── .env                               # Global environment variables (AWS credentials, table names, ARNs)
``````


### Dashboard an Demo
![Agentic AI Retail Pricing Agnet Dashboard](https://github.com/samhaldia/retail-pricing-agent-ai/blob/main/Retail-AI.PNG "Agentic AI Retail Pricing Agnet")

![Agentic AI Retail Pricing Agnet Products Listing](https://github.com/samhaldia/retail-pricing-agent-ai/blob/main/Retail-AI-Products.PNG "Agentic AI Retail Pricing Agnet Products Listing")

![Agentic AI Retail Pricing Agnet Recommendations](https://github.com/samhaldia/retail-pricing-agent-ai/blob/main/Retail-AI-Products-Recommend.PNG "Agentic AI Retail Pricing Agnet Recommendations")

![Agentic AI Retail Pricing Agnet Idea Generation](https://github.com/samhaldia/retail-pricing-agent-ai/blob/main/Retail-AI-Products-Ideas.PNG "Agentic AI Retail Pricing Agnet Idea Generation")


🛠️ Setup Guide: Running Locally Connected to AWS
Follow these steps to get the application running on your local machine, interacting with live AWS resources.
Prerequisites
•	Python 3.8+: Installed and added to your PATH.
•	Node.js & npm: Installed (LTS version recommended).
•	AWS CLI: Installed and configured (aws configure should be set up for us-east-1 with credentials that have permissions to create/manage IAM, S3, DynamoDB, Bedrock, and Step Functions).
•	Project Files: You should have the complete retail-pricing-optimizer project structure on your local machine.

Run Your Local Application and Test Connection to AWS
1.  Create venv of your choice
o   Got to project root
o   python -m venv retailenv
o   .\retailenv\Scripts\activate

2.	Update Your Local .env File:
o	Open retail-pricing-optimizer/.env.
o	# AWS Configuration
o	AWS_REGION=us-east-1
o	
o	# S3 Bucket Names (Replace with YOUR unique bucket names)
o	S3_LANDING_ZONE_BUCKET=market-data-landing-zone-bit-charms
o	S3_PROCESSED_DATA_BUCKET=processed-data-store-bit-charms
o	S3_LAMBDA_DEPLOYMENT_BUCKET=lambda-deployment-package-bit-charms
o	S3_FRONTEND_HOSTING_BUCKET=retail-pricing-optimizer-frontend-bit-charms  
o	
o	# DynamoDB Tables (use names as created at AWS Console)
o	MARKET_DATA_TABLE=retail-market-data
o	INVENTORY_TABLE=retail-inventory
o	DEMAND_FORECASTS_TABLE=retail-demand-forecasts
o	CUSTOMER_PROFILES_TABLE=retail-customer-profiles
o	PRICING_PROMO_RECOMMENDATIONS_TABLE=retail-pricing-promo-recommendations
o	PRICE_SYNC_LOG_TABLE=retail-price-sync-logs
o	
o	# Bedrock Model ID
o	BEDROCK_MODEL_ID=anthropic.claude-3-sonnet-20240229-v1:0
o	
o	# Mock API Endpoint (This remains LOCAL, your local Python backend will use this)
o	MOCK_ECOMMERCE_API_ENDPOINT=http://127.0.0.1:5000/mock-api
o	
o	# Step Functions State Machine ARN (UPDATE THIS WITH YOUR ACTUAL ARN FROM AWS CONSOLE)
o	STEP_FUNCTIONS_STATE_MACHINE_ARN=arn:aws:states:us-east-1:YOUR_ACCOUNT_ID:stateMachine

3.	Install Python Dependencies:
o	Open Command Prompt/PowerShell.
o	Navigate to retail-pricing-agent-ai/ (project root).
o	Run: pip install -r requirements.txt
o	For each folder in retail-pricing-optimizer/lambda_functions/ (e.g., market_data_ingestor, demand_forecast_agent, etc.), navigate into it and run pip install -r requirements.txt.

4.	Install Node.js Dependencies:
o	Navigate to retail-pricing-optimizer/frontend/.
o	Run: npm install

Create Your AWS Resources (Using AWS Console UI)
Ensure you are in the US East (N. Virginia) us-east-1 region in your AWS Console.

1.	Create IAM Role (RetailAgentLambdaRole):
o	Go to IAM -> Roles -> Create role.
o	Trusted entity type: AWS service -> Lambda.
o	Permissions: Attach managed policies: AWSLambdaBasicExecutionRole, AmazonS3FullAccess, AmazonDynamoDBFullAccess, AmazonBedrockFullAccess, AWSStepFunctionsFullAccess.
o	Role name: RetailAgentLambdaRole.
o	Create role.

2.	Create S3 Buckets (4 total):
o	Go to S3 -> Create bucket.
o	Create buckets in us-east-1 with unique names (e.g., append your initials or a random string).
	market-data-landing-zone-YOURUNIQUEID (Block all public access: checked)
	processed-data-store-YOURUNIQUEID (Block all public access: checked)
	lambda-deployment-package-YOURUNIQUEID (Block all public access: checked)
	retail-pricing-optimizer-frontend-YOURUNIQUEID (Block all public access: UNCHECKED) # Required when fronentd is deployed to AWS

3.	Create DynamoDB Tables (6 total):
o	Go to DynamoDB -> Tables -> Create table.
o	Create tables in us-east-1 with On-demand capacity. Use the DynamoDB JSON format for manual item creation later.
	retail-market-data: PK: sku_region_pk (String), SK: timestamp (String)
	retail-inventory: PK: sku_region_pk (String)
	retail-demand-forecasts: PK: sku_region_pk (String), SK: forecast_date (String)
	retail-customer-profiles: PK: customer_id (String)
	retail-pricing-promo-recommendations: PK: sku_region_pk (String), SK: timestamp (String)
	retail-price-sync-logs: PK: sku_region_pk (String), SK: timestamp (String)

4.	Enable Amazon Bedrock Model Access:
o	Go to Amazon Bedrock -> Model access.
o	Click "Manage model access".
o	Request access for Anthropic Claude 3 Sonnet.
5.	Create Step Functions State Machine (RetailPricingOptimizationWorkflow):
o	Go to Step Functions -> State machines -> Create state machine.
o	Authoring method: Design your workflow visually -> Standard.
o	State machine name: RetailPricingOptimizationWorkflow.
o	Permissions: Use an existing role -> Select RetailAgentLambdaRole.
o	Definition (Code tab): Paste the ASL definition (from previous responses), replacing YOUR_ACCOUNT_ID with your actual 12-digit AWS account ID.
o	Create state machine.
o	Copy its ARN (e.g., arn:aws:states:us-east-1:123456789012:stateMachine:RetailPricingOptimizationWorkflow). Paste this ARN into STEP_FUNCTIONS_STATE_MACHINE_ARN in your local .env file.


1.	Start Your Local Python Backend (main.py):
o	Open first Command Prompt/PowerShell.
o	cd project_root
o	python main.py
o	Keep this window open.

2.	Start Your Local React Frontend:
o	Open second Command Prompt/PowerShell.
o	cd project_root/frontend
o	npm start
o	Keep this window open. Your browser should open to http://localhost:1234.

3.	Populate Initial Data in AWS DynamoDB (Crucial):
o	Go to the AWS DynamoDB Console.
o	For retail-inventory, retail-customer-profiles, and retail-market-data tables, add at least 1-3 items each using the DynamoDB JSON format provided in previous responses.
o	Example for retail-inventory:
	{
	  "sku_region_pk": { "S": "P001_US-EAST" },
	  "sku": { "S": "P001" },
	  "current_stock": { "N": "999.99" },
	  "cost": { "N": "750.00" },
	  "inventory": { "N": "120" },
	  "last_updated": { "S": "2025-07-15T10:00:00Z" }
	}
o	Example for retail-customer-profiles:	
	{
      "customer_id": {
        "S": "C101"
      },
      "last_purchase_date": { "S": "2025-07-13" },
      "preferences": {
        "L": [
          {
          "S": "electronics"
          },
          {
            "S": "smart home"
          }
        ]
      },
      "segment": {
        "S": "Loyalty Tier A"
      }
    }

**Note**: We can also access the data avaibale locally in data folder

4.	Verify UI Data Fetching:
o	Refresh http://localhost:1234.
o	Check "Products" tab and "Dashboard" for data from DynamoDB.

5.	Trigger Agent Workflow:
o	On "Dashboard", click "Trigger Agent Run".
o	Observe main.py console: Look for DEBUG messages from each agent, indicating successful writes to DynamoDB.
o	Observe AWS Step Functions Console: See the execution start (and fail, as Lambdas aren't deployed yet).
o	Verify AWS DynamoDB Console: Check retail-market-data, retail-demand-forecasts, retail-pricing-promo-recommendations, retail-price-sync-logs for new data.

6.	Test "AI Promos":
o	Go to "AI Promos" tab. Enter a prompt like "Suggest a flash sale for a gaming laptop for tech enthusiasts."
o	Click "Get Promotion Idea".
o	Observe main.py console for Bedrock interaction.
o	Observe UI for generated promo text.

7.	Test "Apply Recommendation":
o	If recommendations appear on the "Recommendations" tab, click "Apply Recommendation".
o	Observe main.py console for sync logs.
o	Verify retail-pricing-promo-recommendations (status change) and retail-inventory (price update) in DynamoDB.









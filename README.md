🛍️ Agentic AI Retail Pricing Optimizer
🚀 Project Overview
The Agentic AI Retail Pricing Optimizer is a cutting-edge, cloud-native application designed to transform retail pricing and promotion strategies. It leverages intelligent AI agents, a robust serverless architecture on AWS, and real-time data processing to deliver dynamic price recommendations and personalized promotional ideas. This project showcases how AI-driven automation can significantly enhance business agility and profitability in the competitive retail sector.

✨ Features
This application provides the following core functionalities:

Dynamic Product Dashboard: Gain a real-time, comprehensive overview of product inventory, current prices, and vital key performance metrics.

Automated Agent Workflow Trigger: Initiate a complete cycle of interconnected AI agents—including market data ingestion, demand forecasting, promotion strategy generation, and price synchronization—with a single, intuitive click.

Intelligent Price Recommendations: Generates data-driven price adjustments for products, dynamically informed by prevailing market conditions, inventory levels, and precise demand forecasts.

AI-Powered Promotion Idea Generation: Utilizes powerful Large Language Models (LLMs) via Amazon Bedrock to craft creative, targeted promotional campaign ideas tailored for specific products and customer segments.

Recommendation Management: Easily view and apply pending price recommendations directly from the user interface, simulating real-world price updates to your e-commerce system.

Real-time Data Sync (Simulated): The RealTimePriceSyncAgent simulates the crucial process of updating an external e-commerce system with new prices, meticulously logging all such actions for auditing.

Cloud-Native Architecture: Built entirely on AWS serverless technologies (Lambda, Step Functions, DynamoDB, S3, Bedrock) to ensure unparalleled scalability, high reliability, and optimal cost-efficiency.

🏗️ Architecture and Structure
The project is thoughtfully structured with a clear separation of concerns, featuring a React frontend, a local Python backend (Flask acting as a local API Gateway/orchestrator), and seamless integration with various AWS cloud services that the local backend orchestrates and interacts with.

``````
retail-pricing-agent-ai/
├── data/
│   ├── dummy_competitor_pricing.json
│   ├── dummy_pos_data.json
│   ├── dummy_inventory_data.json
│   └── dummy_customer_profiles.json
├── frontend/
│   ├── public/
│   │   └── index.html               # Main HTML file for React app
│   ├── src/
│   │   ├── components/
│   │   │   ├── AIPromoGenerator.js  # UI for AI promo generation
│   │   │   ├── Dashboard.js         # UI for dashboard overview
│   │   │   └── ProductCard.js       # Reusable product display component
│   │   ├── App.js                   # Main React application component
│   │   └── index.js                 # React entry point
│   └── package.json                 # Node.js dependencies for frontend
├── lambda_functions/
│   ├── market_data_ingestor/
│   │   ├── app.py                   # Lambda code: Ingests market data
│   │   └── requirements.txt
│   ├── demand_forecast_agent/
│   │   ├── app.py                   # Lambda code: Forecasts demand
│   │   └── requirements.txt
│   ├── promotion_strategy_agent/
│   │   ├── app.py                   # Lambda code: Generates pricing/promo strategies
│   │   └── requirements.txt
│   ├── real_time_price_sync_agent/
│   │   ├── app.py                   # Lambda code: Syncs prices to mock e-commerce
│   │   └── requirements.txt
│   ├── ui_backend/
│   │   ├── app.py                   # Lambda code: Serves UI data, triggers workflows
│   │   └── requirements.txt
├── main.py                          # Local Flask backend server (orchestrates local agent calls, mock API)
├── requirements.txt                 # Python dependencies for main.py
└── .env                             # Global environment variables (AWS credentials, table names, ARNs)

``````

📊 Dashboard & Demo

![Agentic AI Retail Pricing Agnet Dashboard](https://github.com/samhaldia/retail-pricing-agent-ai/blob/main/Retail-AI.PNG "Agentic AI Retail Pricing Agnet")

![Agentic AI Retail Pricing Agnet Products Listing](https://github.com/samhaldia/retail-pricing-agent-ai/blob/main/Retail-AI-Products.PNG "Agentic AI Retail Pricing Agnet Products Listing")

![Agentic AI Retail Pricing Agnet Recommendations](https://github.com/samhaldia/retail-pricing-agent-ai/blob/main/Retail-AI-Products-Recommend.PNG "Agentic AI Retail Pricing Agnet Recommendations")

![Agentic AI Retail Pricing Agnet Idea Generation](https://github.com/samhaldia/retail-pricing-agent-ai/blob/main/Retail-AI-Products-Ideas.PNG "Agentic AI Retail Pricing Agnet Idea Generation")

Export to Sheets
🛠️ Setup Guide: Running Locally Connected to AWS
Follow these comprehensive steps to get the application running on your local machine, seamlessly interacting with live AWS resources.

Prerequisites
Before you begin, ensure you have the following installed and configured:

Python 3.8+: Installed and added to your system's PATH.

Node.js & npm: Installed (LTS version recommended).

AWS CLI: Installed and configured. Run aws configure and ensure it's set up for us-east-1 with credentials that have permissions to create and manage IAM, S3, DynamoDB, Bedrock, and Step Functions resources.

Project Files: You should have the complete retail-pricing-agent-ai project structure cloned or downloaded to your local machine.

Create Your AWS Resources (Using AWS Console UI)
Important: Ensure you are operating within the US East (N. Virginia) us-east-1 region in your AWS Console for all resource creation.

Create IAM Role (RetailAgentLambdaRole):

Navigate to IAM -> Roles -> Create role.

Trusted entity type: AWS service -> Lambda.

Permissions: Attach the following AWS managed policies:

AWSLambdaBasicExecutionRole

AmazonS3FullAccess

AmazonDynamoDBFullAccess

AmazonBedrockFullAccess

AWSStepFunctionsFullAccess

Role name: RetailAgentLambdaRole.

Complete the role creation.

Create S3 Buckets (4 total):

Go to S3 -> Create bucket.

Create these four buckets in us-east-1, ensuring unique names (e.g., append your initials or a random string to avoid conflicts).

market-data-landing-zone-YOURUNIQUEID (Keep "Block all public access" checked)

processed-data-store-YOURUNIQUEID (Keep "Block all public access" checked)

lambda-deployment-package-YOURUNIQUEID (Keep "Block all public access" checked)

retail-pricing-agent-ai-frontend-YOURUNIQUEID (For frontend deployment later, "Block all public access" should be UNCHECKED)

Create DynamoDB Tables (6 total):

Go to DynamoDB -> Tables -> Create table.

Create all tables in us-east-1 with On-demand capacity.

retail-market-data: Partition key: sku_region_pk (String), Sort key: timestamp (String)

retail-inventory: Partition key: sku_region_pk (String)

retail-demand-forecasts: Partition key: sku_region_pk (String), Sort key: forecast_date (String)

retail-customer-profiles: Partition key: customer_id (String)

retail-pricing-promo-recommendations: Partition key: sku_region_pk (String), Sort key: timestamp (String)

retail-price-sync-logs: Partition key: sku_region_pk (String), Sort key: timestamp (String)

Enable Amazon Bedrock Model Access:

Navigate to Amazon Bedrock -> **Model access`.

Click "Manage model access".

Request access for Anthropic Claude 3 Sonnet.

Create Step Functions State Machine (RetailPricingOptimizationWorkflow):

Go to Step Functions -> State machines -> Create state machine.

Authoring method: Design your workflow visually -> Standard.

State machine name: RetailPricingOptimizationWorkflow.

Permissions: Choose "Use an existing role" -> Select RetailAgentLambdaRole.

Definition (Code tab): Paste the Amazon States Language (ASL) definition for your workflow here (you'll need to obtain this from your project's Step Functions design or previous instructions), ensuring you replace YOUR_ACCOUNT_ID with your actual 12-digit AWS account ID.

Create the state machine.

Copy its ARN (e.g., arn:aws:states:us-east-1:123456789012:stateMachine:RetailPricingOptimizationWorkflow). You will paste this ARN into the STEP_FUNCTIONS_STATE_MACHINE_ARN variable in your local .env file.

Run Your Local Application and Test Connection to AWS
Create and Activate Python Virtual Environment:

Navigate to your project root (retail-pricing-agent-ai/).

Create a virtual environment:

Bash

python -m venv retailenv
Activate it:

Windows (Command Prompt/PowerShell):

DOS

.\retailenv\Scripts\activate
Linux/macOS (Bash/Zsh):

Bash

source retailenv/bin/activate
Update Your Local .env File:

Open retail-pricing-agent-ai/.env.

Update the following variables with your specific values (especially the unique S3 bucket names and your Step Functions ARN):

Code snippet

# AWS Configuration
AWS_REGION=us-east-1

# S3 Bucket Names (Replace with YOUR unique bucket names created above)
S3_LANDING_ZONE_BUCKET=market-data-landing-zone-YOURUNIQUEID
S3_PROCESSED_DATA_BUCKET=processed-data-store-YOURUNIQUEID
S3_LAMBDA_DEPLOYMENT_BUCKET=lambda-deployment-package-YOURUNIQUEID
S3_FRONTEND_HOSTING_BUCKET=retail-pricing-agent-ai-frontend-YOURUNIQUEID

# DynamoDB Tables (Use names as created at AWS Console)
MARKET_DATA_TABLE=retail-market-data
INVENTORY_TABLE=retail-inventory
DEMAND_FORECASTS_TABLE=retail-demand-forecasts
CUSTOMER_PROFILES_TABLE=retail-customer-profiles
PRICING_PROMO_RECOMMENDATIONS_TABLE=retail-pricing-promo-recommendations
PRICE_SYNC_LOG_TABLE=retail-price-sync-logs

# Bedrock Model ID
BEDROCK_MODEL_ID=anthropic.claude-3-sonnet-20240229-v1:0

# Mock API Endpoint (This remains LOCAL, your local Python backend will use this)
MOCK_ECOMMERCE_API_ENDPOINT=http://127.0.0.1:5000/mock-api

# Step Functions State Machine ARN (UPDATE THIS WITH YOUR ACTUAL ARN FROM AWS CONSOLE)
STEP_FUNCTIONS_STATE_MACHINE_ARN=arn:aws:states:us-east-1:YOUR_ACCOUNT_ID:stateMachine:RetailPricingOptimizationWorkflow
Install Python Dependencies:

Ensure your virtual environment is active.

From the project root (retail-pricing-agent-ai/), run:

Bash

pip install -r requirements.txt
For each subfolder within retail-pricing-agent-ai/lambda_functions/ (e.g., market_data_ingestor, demand_forecast_agent, etc.), navigate into it and run:

Bash

pip install -r requirements.txt
Install Node.js Dependencies:

Navigate to retail-pricing-agent-ai/frontend/.

Run:

Bash

npm install
Start Your Local Python Backend (main.py):

Open your first Command Prompt/PowerShell/Terminal window.

Navigate to the project root (retail-pricing-agent-ai/).

Ensure your virtual environment is active.

Run:

Bash

python main.py
Keep this window open and running.

Start Your Local React Frontend:

Open a second Command Prompt/PowerShell/Terminal window.

Navigate to retail-pricing-agent-ai/frontend/.

Run:

Bash

npm start
Keep this window open. Your default web browser should automatically open to http://localhost:1234.

Populate Initial Data in AWS DynamoDB (Crucial):

Go to the AWS DynamoDB Console.

For the retail-inventory, retail-customer-profiles, and retail-market-data tables, add at least 1-3 items each manually. Use the DynamoDB JSON format for item creation.

Example for retail-inventory:

JSON

{
    "sku_region_pk": { "S": "P001_US-EAST" },
    "sku": { "S": "P001" },
    "current_stock": { "N": "120" },
    "cost": { "N": "750.00" },
    "inventory": { "N": "120" },
    "last_updated": { "S": "2025-07-15T10:00:00Z" }
}
Example for retail-customer-profiles:

JSON

{
    "customer_id": { "S": "C101" },
    "last_purchase_date": { "S": "2025-07-13" },
    "preferences": {
        "L": [
            { "S": "electronics" },
            { "S": "smart home" }
        ]
    },
    "segment": { "S": "Loyalty Tier A" }
}
Note: While dummy data is available in the data/ folder, manual entry into DynamoDB is essential for the application to interact with live cloud resources from the start.

Verify UI Data Fetching:

Refresh your browser at http://localhost:1234.

Check the "Products" tab and "Dashboard" for data being fetched and displayed from your DynamoDB tables.

Trigger Agent Workflow:

On the "Dashboard" tab of your running application, click the "Trigger Agent Run" button.

Observe your main.py console: Look for DEBUG messages from each agent, indicating successful attempts to write to DynamoDB.

Observe your AWS Step Functions Console: You should see a new execution start for your RetailPricingOptimizationWorkflow (it might show as failed initially, as the Lambda functions themselves are not yet deployed).

Verify AWS DynamoDB Console: Check retail-market-data, retail-demand-forecasts, retail-pricing-promo-recommendations, and retail-price-sync-logs for newly generated data.

Test "AI Promos":

Go to the "AI Promos" tab in your application.

Enter a prompt, e.g., "Suggest a flash sale for a gaming laptop for tech enthusiasts."

Click "Get Promotion Idea".

Observe your main.py console: You should see output related to the Bedrock interaction.

Observe your UI: The generated promotion text should appear.

Test "Apply Recommendation":

If recommendations have appeared on the "Recommendations" tab, click "Apply Recommendation".

Observe your main.py console: Look for sync logs.

Verify in DynamoDB: Check retail-pricing-promo-recommendations (status change) and retail-inventory (price update).
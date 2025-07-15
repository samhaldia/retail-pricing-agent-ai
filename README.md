Agentic AI Retail Optimizer
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
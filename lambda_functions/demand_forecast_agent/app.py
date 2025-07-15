import json
import os
import time
import boto3
from botocore.exceptions import ClientError
from boto3.dynamodb.conditions import Key
from dotenv import load_dotenv
from decimal import Decimal # Import Decimal type

# Load environment variables (for local testing)
load_dotenv(os.path.join(os.path.dirname(__file__), '..', '..', '.env'))

# AWS Resource Clients
dynamodb = boto3.resource('dynamodb', region_name=os.getenv("AWS_REGION", "us-east-1"))
market_data_table = dynamodb.Table(os.getenv("MARKET_DATA_TABLE", "retail-market-data"))
inventory_table = dynamodb.Table(os.getenv("INVENTORY_TABLE", "retail-inventory"))
demand_forecasts_table = dynamodb.Table(os.getenv("DEMAND_FORECASTS_TABLE", "retail-demand-forecasts"))

def lambda_handler(event, context):
    """
    Lambda function for the Demand Forecast Agent.
    Reads market data and inventory, performs a simple forecast, and stores it.
    Triggered by Step Functions.
    """
    print("Demand Forecast Agent triggered.")

    # Get the AWS region, convert to uppercase for the PK suffix
    current_aws_region = os.getenv("AWS_REGION", "us-east-1").upper()

    try:
        # Fetch all SKUs from inventory table (as our product master for demo)
        print(f"DEBUG: Scanning {inventory_table.name} for all inventory items.")
        response = inventory_table.scan() # Scan is okay for small demo data
        all_inventory_items = response['Items']
        print(f"DEBUG: Found {len(all_inventory_items)} inventory items.")
        
        forecasts = []
        for inventory_item in all_inventory_items:
            sku = inventory_item['sku'] # Original SKU from inventory item
            sku_region_pk = f"{sku}_{current_aws_region}" # Construct composite PK
            
            # Convert Decimal values to float immediately after retrieval for calculations
            current_stock = float(inventory_item.get('current_stock', Decimal('1.0'))) # Mock current price for simplicity
            
            # --- Get Latest Competitor Price from retail-market-data ---
            print(f"DEBUG: Querying {market_data_table.name} for latest competitor price for {sku_region_pk}.")
            try:
                market_data_response = market_data_table.query(
                    KeyConditionExpression=Key('sku_region_pk').eq(sku_region_pk),
                    ScanIndexForward=False, # Get latest first
                    Limit=1
                )
                latest_competitor_price_decimal = market_data_response['Items'][0]['competitor_price'] if market_data_response['Items'] else None
                latest_competitor_price = float(latest_competitor_price_decimal) if latest_competitor_price_decimal is not None else None
                print(f"DEBUG: Latest competitor price for {sku_region_pk}: {latest_competitor_price}")
            except ClientError as e:
                print(f"ERROR: ClientError querying market data for {sku_region_pk}: {e.response['Error']['Message']}")
                latest_competitor_price = None
            except Exception as e:
                print(f"ERROR: Unexpected error fetching competitor price for {sku_region_pk}: {e}")
                latest_competitor_price = None

            # --- Simple Dummy Forecasting Logic (Replace with SageMaker in production) ---
            simulated_demand_factor = 1.0 # Base demand factor
            
            # Simulate impact of competitor price
            if latest_competitor_price:
                if latest_competitor_price < (current_stock * 0.9): 
                    simulated_demand_factor -= 0.05 
                elif latest_competitor_price > (current_stock * 1.1):
                    simulated_demand_factor += 0.03 

            simulated_demand_factor += (time.time() % 100 / 1000 - 0.05) 
            
            forecasted_demand = max(1, round(current_stock * simulated_demand_factor * 0.8))

            forecast_item = {
                'sku_region_pk': sku_region_pk, # Partition Key
                'forecast_date': time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()), # Sort Key
                'sku': sku, # Original SKU as attribute
                'forecasted_demand_next_7_days': Decimal(str(forecasted_demand)), # Store as Decimal
                'demand_factor': Decimal(str(round(simulated_demand_factor, 2))), # Store as Decimal
                'competitor_price': Decimal(str(latest_competitor_price)) if latest_competitor_price is not None else None # Store as Decimal
            }
            forecasts.append(forecast_item)
            
            # Store forecast in DynamoDB
            print(f"DEBUG: Attempting to put forecast item to {demand_forecasts_table.name}: {forecast_item}")
            try:
                demand_forecasts_table.put_item(Item=forecast_item)
                print(f"DEBUG: Successfully put forecast for SKU {sku_region_pk}")
            except ClientError as e:
                print(f"ERROR: ClientError putting forecast for SKU {sku_region_pk}: {e.response['Error']['Message']}")
            except Exception as e:
                print(f"ERROR: Unexpected error putting forecast for SKU {sku_region_pk}: {e}")

        print(f"Generated and stored {len(forecasts)} demand forecasts.")
        return {
            'statusCode': 200,
            'body': json.dumps({
                'message': 'Demand forecasts generated successfully',
                'forecasts': forecasts 
            }, default=str) # Use default=str to handle Decimal in JSON serialization
        }
    except Exception as e:
        print(f"ERROR: Error in Demand Forecast Agent: {e}")
        return {
            'statusCode': 500,
            'body': json.dumps({'message': f'Error generating demand forecasts: {str(e)}'})
        }
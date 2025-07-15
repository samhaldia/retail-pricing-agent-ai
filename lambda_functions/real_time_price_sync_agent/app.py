import json
import os
import time
import requests
import boto3
from botocore.exceptions import ClientError
from dotenv import load_dotenv
from decimal import Decimal # Import Decimal type

# Load environment variables (for local testing)
load_dotenv(os.path.join(os.path.dirname(__file__), '..', '..', '.env'))

# AWS Resource Clients
dynamodb = boto3.resource('dynamodb', region_name=os.getenv("AWS_REGION", "us-east-1"))
price_sync_log_table = dynamodb.Table(os.getenv("PRICE_SYNC_LOG_TABLE", "retail-price-sync-logs"))
inventory_table = dynamodb.Table(os.getenv("INVENTORY_TABLE", "retail-inventory"))

# Mock E-commerce API Endpoint (from .env)
mock_api_endpoint = os.getenv("MOCK_ECOMMERCE_API_ENDPOINT")

def lambda_handler(event, context):
    """
    Lambda function for the Real-Time Price Sync Agent.
    Simulates syncing price/promo actions to a retail system and logs results.
    Triggered by Step Functions.
    """
    print("Real-Time Price Sync Agent triggered.")

    # Get the AWS region, convert to uppercase for the PK suffix
    current_aws_region = os.getenv("AWS_REGION", "us-east-1").upper()

    actions = event.get('pricing_recommendations', []) 
    print(f"DEBUG: Received {len(actions)} pricing recommendations to sync.")

    if not mock_api_endpoint:
        print("ERROR: MOCK_ECOMMERCE_API_ENDPOINT not set in .env or Lambda environment. Cannot simulate API calls.")
        return {
            'statusCode': 500,
            'body': json.dumps({'message': 'MOCK_ECOMMERCE_API_ENDPOINT not configured.'})
        }

    sync_results = []
    for action in actions:
        sku = action.get('sku')
        action_type = action.get('type') 
        
        if not sku or not action_type:
            print(f"WARN: Skipping malformed action: {action}")
            continue

        sku_region_pk = f"{sku}_{current_aws_region}"
        current_timestamp = time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())

        # Ensure recommended_price is converted from Decimal to float if it came from previous agent's output
        recommended_price = float(action.get('recommended_price', Decimal('0.0'))) 

        sync_log_item = {
            'sku_region_pk': sku_region_pk, 
            'timestamp': current_timestamp, 
            'action_id': action.get('id', f"action_{sku}_{current_timestamp}"), 
            'sku': sku,
            'action_type': action_type,
            'status': 'failed', 
            'details': 'N/A',
            'recommended_price': Decimal(str(recommended_price)) # Store as Decimal
        }

        if action_type == 'price_adjustment':
            payload = {'sku': sku, 'new_price': recommended_price}
            print(f"DEBUG: Attempting to call mock API to update price for SKU {sku} to {recommended_price}.")
            try:
                response = requests.post(f"{mock_api_endpoint}/update_price", json=payload)
                response.raise_for_status() 
                result = response.json()
                sync_log_item['status'] = 'success'
                sync_log_item['details'] = result.get('message', 'Price updated successfully.')
                print(f"DEBUG: Successfully synced price for SKU {sku} to {recommended_price}")

                # --- Update Inventory Table with new current price ---
                print(f"DEBUG: Updating {inventory_table.name} for {sku_region_pk} with new price {recommended_price}.")
                try:
                    inventory_table.update_item(
                        Key={'sku_region_pk': sku_region_pk}, 
                        UpdateExpression="SET current_stock = :new_price, last_updated = :ts", 
                        ExpressionAttributeValues={
                            ':new_price': Decimal(str(recommended_price)), # Store as Decimal
                            ':ts': current_timestamp
                        }
                    )
                    print(f"DEBUG: Updated inventory table for {sku_region_pk} with new price {recommended_price}")
                except ClientError as e:
                    print(f"ERROR: ClientError updating inventory table for {sku_region_pk}: {e.response['Error']['Message']}")
                except Exception as e:
                    print(f"ERROR: Unexpected error updating inventory for {sku_region_pk}: {e}")
                
            except requests.exceptions.RequestException as e:
                sync_log_item['details'] = f"API call failed: {str(e)}"
                print(f"ERROR: Failed to sync price for SKU {sku}: {e}")
            except Exception as e:
                sync_log_item['details'] = f"ERROR: Unexpected error during price sync for SKU {sku}: {e}"
                print(f"ERROR: Unexpected error during price sync for SKU {sku}: {e}")

        # Add other action types (e.g., 'promotion_activation') if needed
        
        sync_results.append(sync_log_item)
        print(f"DEBUG: Attempting to log sync result to {price_sync_log_table.name}: {sync_log_item}")
        try:
            price_sync_log_table.put_item(Item=sync_log_item)
            print(f"DEBUG: Successfully logged sync result for SKU {sku_region_pk}")
        except ClientError as e:
            print(f"ERROR: ClientError logging sync result for SKU {sku_region_pk}: {e.response['Error']['Message']}")
        except Exception as e:
            print(f"ERROR: Unexpected error logging sync result for SKU {sku_region_pk}: {e}")

    print(f"Completed syncing {len(sync_results)} actions.")
    return {
        'statusCode': 200,
        'body': json.dumps({
            'message': 'Price and promotion sync completed',
            'sync_results': sync_results
        }, default=str) # Use default=str to handle Decimal in JSON serialization
    }
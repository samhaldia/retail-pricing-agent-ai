import json
import os
import time
import boto3
import requests 
from botocore.exceptions import ClientError
from decimal import Decimal
from dotenv import load_dotenv

# Load environment variables (for local testing)
load_dotenv(os.path.join(os.path.dirname(__file__), '..', '..', '.env'))

# AWS Resource Clients
dynamodb = boto3.resource('dynamodb', region_name=os.getenv("AWS_REGION", "us-east-1"))
recommendations_table = dynamodb.Table(os.getenv("PRICING_PROMO_RECOMMENDATIONS_TABLE", "retail-pricing-promo-recommendations"))
inventory_table = dynamodb.Table(os.getenv("INVENTORY_TABLE", "retail-inventory"))
price_sync_log_table = dynamodb.Table(os.getenv("PRICE_SYNC_LOG_TABLE", "retail-price-sync-logs"))

# Ensure this points to port 5000 as per main.py update
ECOMMERCE_PRICE_UPDATE_API = os.getenv("MOCK_ECOMMERCE_API_ENDPOINT", "http://127.0.0.1:5000/mock-api/update_price")

def _update_ecommerce_price(sku, new_price):
    """
    Simulates sending a real-time price update to an external e-commerce platform.
    """
    payload = {
        'sku': sku,
        'new_price': new_price
    }
    print(f"DEBUG: Attempting to send price update to e-commerce API: {ECOMMERCE_PRICE_UPDATE_API} for SKU {sku} to price {new_price}")
    try:
        response = requests.post(ECOMMERCE_PRICE_UPDATE_API, json=payload)
        response.raise_for_status() 
        print(f"DEBUG: Successfully updated price for SKU {sku} on e-commerce platform (simulated). Response: {response.json()}")
        return True
    except requests.exceptions.RequestException as e:
        print(f"ERROR: Failed to update price for SKU {sku} on e-commerce platform: {e}")
        return False
    except Exception as e:
        print(f"ERROR: Unexpected error in _update_ecommerce_price for SKU {sku}: {e}")
        return False

def lambda_handler(event, context):
    """
    Lambda function for the Real-Time Price Sync Agent.
    Applies approved pricing recommendations and logs the sync action.
    Triggered by Step Functions or directly by UI apply action.
    """
    print("Real-Time Price Sync Agent triggered.")

    recommendations_to_sync = event.get('recommendations', [])

    synced_actions_count = 0
    synced_results = []

    if not recommendations_to_sync:
        print("DEBUG: No recommendations received in event for sync agent.")
        return {
            'statusCode': 200,
            'body': json.dumps({'message': 'No recommendations provided to sync.'})
        }

    for rec in recommendations_to_sync:
        print(f"DEBUG: Sync Agent inspecting recommendation: ID={rec.get('id', 'N/A')}, SKU={rec.get('sku', 'N/A')}, Type='{rec.get('type', 'N/A')}', Status='{rec.get('status', 'N/A')}'")

        if rec.get('type') == 'price_adjustment' and rec.get('status') == 'applied':
            sku_region_pk = rec.get('sku_region_pk') 
            sku = rec.get('sku')
            # --- FIX: Use 'recommendedPrice' (camelCase) from frontend object ---
            recommended_price = float(rec.get('recommendedPrice', 0.0)) 
            # --- END FIX ---

            if not sku_region_pk or not sku or recommended_price is None:
                print(f"WARN: Skipping recommendation {rec.get('id', 'N/A')} due to missing critical fields (sku_region_pk, sku, recommended_price).")
                synced_results.append({'sku': sku, 'status': 'skipped', 'reason': 'missing critical fields'})
                continue 

            print(f"DEBUG: Processing recommendation for SKU {sku_region_pk} with new price {recommended_price}")

            if _update_ecommerce_price(sku, recommended_price):
                try:
                    inventory_table.update_item(
                        Key={'sku_region_pk': sku_region_pk},
                        UpdateExpression="SET current_stock = :price, last_updated = :ts",
                        ExpressionAttributeValues={
                            ':price': Decimal(str(recommended_price)), 
                            ':ts': time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())
                        }
                    )
                    print(f"DEBUG: Successfully updated inventory table for SKU {sku_region_pk}")

                    log_item = {
                        'sku_region_pk': sku_region_pk,
                        'timestamp': time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
                        'recommendation_id': rec.get('id', 'N/A'),
                        'sku': sku,
                        'action': 'price_sync',
                        'old_price': Decimal(str(rec.get('currentPrice', 0.0))), # Use currentPrice from frontend object
                        'new_price': Decimal(str(recommended_price)), 
                        'status': 'success'
                    }
                    price_sync_log_table.put_item(Item=log_item)
                    print(f"DEBUG: Successfully logged price sync for SKU {sku_region_pk}")

                    synced_actions_count += 1
                    synced_results.append({'sku': sku, 'status': 'success', 'new_price': recommended_price})

                except ClientError as e:
                    print(f"ERROR: ClientError during DynamoDB updates for SKU {sku_region_pk}: {e.response['Error']['Message']}")
                    synced_results.append({'sku': sku, 'status': 'failed_db_update', 'error': str(e)})
                except Exception as e:
                    print(f"ERROR: Unexpected error during DynamoDB updates for SKU {sku_region_pk}: {e}")
                    synced_results.append({'sku': sku, 'status': 'failed_db_update', 'error': str(e)})
            else:
                print(f"ERROR: Failed to update e-commerce price for SKU {sku_region_pk}. Skipping subsequent DB updates.")
                synced_results.append({'sku': sku, 'status': 'failed_ecommerce_update', 'new_price': recommended_price})
        else:
            print(f"DEBUG: Skipping recommendation {rec.get('id', 'N/A')} due to status '{rec.get('status', 'N/A')}' or type '{rec.get('type', 'N/A')}' (expected 'applied' and 'price_adjustment').")
            synced_results.append({'sku': rec.get('sku', 'N/A'), 'status': 'skipped', 'reason': 'status or type mismatch'})

    print(f"Completed syncing {synced_actions_count} actions.")
    return {
        'statusCode': 200,
        'body': json.dumps({
            'message': f'Price and promotion sync completed',
            'sync_results': synced_results
        }, default=str) 
    }
import json
import os
import time
import boto3
from botocore.exceptions import ClientError
from dotenv import load_dotenv
from decimal import Decimal # <--- ADD THIS IMPORT

# Load environment variables (for local testing, not strictly needed in AWS Lambda env vars)
load_dotenv(os.path.join(os.path.dirname(__file__), '..', '..', '.env'))

# AWS Resource Clients
dynamodb = boto3.resource('dynamodb', region_name=os.getenv("AWS_REGION", "us-east-1"))
market_data_table_name = os.getenv("MARKET_DATA_TABLE", "retail-market-data")
market_data_table = dynamodb.Table(market_data_table_name)

def lambda_handler(event, context):
    """
    Lambda function for the Market Data Ingestor Agent.
    Ingests competitor pricing data into DynamoDB.
    Triggered by Kinesis Firehose or EventBridge in a real AWS setup.
    """
    print("Market Data Ingestor Agent triggered.")
    
    # Get the AWS region, convert to uppercase for the PK suffix
    current_aws_region = os.getenv("AWS_REGION", "us-east-1").upper()

    try:
        # If triggered by a direct test or Step Functions, event might contain data
        if 'dummy_competitor_data' in event:
            competitor_data = event['dummy_competitor_data']
        else:
            # Fallback for initial population or direct local test from dummy file
            with open(os.path.join(os.path.dirname(__file__), '..', '..', 'data', 'dummy_competitor_pricing.json'), 'r') as f:
                competitor_data = json.load(f)

        ingested_count = 0
        for item in competitor_data:
            sku = item.get('sku')
            if not sku:
                print(f"Skipping item due to missing SKU: {item}")
                continue

            # Construct the composite Partition Key using the AWS region
            sku_region_pk = f"{sku}_{current_aws_region}"
            
            # Ensure 'timestamp' is present and valid
            if 'timestamp' not in item:
                item['timestamp'] = time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())
            
            # Prepare item for DynamoDB
            db_item = {
                'sku_region_pk': sku_region_pk,
                'timestamp': item['timestamp'],
                'sku': sku, # Keep original SKU as an attribute for convenience
                # Convert competitor_price to Decimal before storing
                'competitor_price': Decimal(str(item.get('competitor_price', 0.0))) # <--- CHANGE IS HERE
                # Add other relevant fields if they exist in your dummy data
            }
            
            try:
                print(f"DEBUG: Attempting to put item to {market_data_table_name}: {db_item}")
                market_data_table.put_item(Item=db_item)
                ingested_count += 1
                print(f"DEBUG: Successfully put item {sku_region_pk}")
            except ClientError as e:
                print(f"ERROR: ClientError putting item {sku_region_pk}: {e.response['Error']['Message']}")
            except Exception as e:
                print(f"ERROR: Unexpected error processing item {sku_region_pk}: {e}")

        print(f"Successfully ingested {ingested_count} market data points into {market_data_table_name}.")
        return {
            'statusCode': 200,
            'body': json.dumps({
                'message': 'Market data ingested successfully',
                'data_count': ingested_count,
                'ingested_items': competitor_data 
            }, default=str) # <--- ADD default=str for Decimal serialization
        }
    except Exception as e:
        print(f"ERROR: Error in Market Data Ingestor: {e}")
        return {
            'statusCode': 500,
            'body': json.dumps({'message': f'Error ingesting market data: {str(e)}'})
        }
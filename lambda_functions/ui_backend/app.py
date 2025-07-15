import json
import os
import boto3
from botocore.exceptions import ClientError
from boto3.dynamodb.conditions import Key
from dotenv import load_dotenv
import time
from decimal import Decimal # Import Decimal type

# Load environment variables (for local testing)
load_dotenv(os.path.join(os.path.dirname(__file__), '..', '..', '.env'))

# AWS Resource Clients
dynamodb = boto3.resource('dynamodb', region_name=os.getenv("AWS_REGION", "us-east-1"))
recommendations_table = dynamodb.Table(os.getenv("PRICING_PROMO_RECOMMENDATIONS_TABLE", "retail-pricing-promo-recommendations"))
inventory_table = dynamodb.Table(os.getenv("INVENTORY_TABLE", "retail-inventory"))
customer_profiles_table = dynamodb.Table(os.getenv("CUSTOMER_PROFILES_TABLE", "retail-customer-profiles"))
demand_forecasts_table = dynamodb.Table(os.getenv("DEMAND_FORECASTS_TABLE", "retail-demand-forecasts"))

stepfunctions_client = boto3.client('stepfunctions', region_name=os.getenv("AWS_REGION", "us-east-1"))
step_functions_state_machine_arn = os.getenv("STEP_FUNCTIONS_STATE_MACHINE_ARN", "arn:aws:states:us-east-1:123456789012:stateMachine:RetailPricingOptimizationWorkflow")


def lambda_handler(event, context):
    """
    Lambda function acting as the UI backend API.
    Triggered by API Gateway.
    Fetches data for the UI and triggers agent workflows.
    """
    path = event.get('path', '/')
    http_method = event.get('httpMethod', 'GET')

    print(f"UI Backend triggered: {http_method} {path}")

    # Set CORS headers for all responses
    cors_headers = {
        'Content-Type': 'application/json',
        'Access-Control-Allow-Origin': '*', # Allow all origins for hackathon demo
        'Access-Control-Allow-Headers': 'Content-Type,Authorization',
        'Access-Control-Allow-Methods': 'GET,POST,PUT,DELETE,OPTIONS'
    }

    # Handle CORS preflight
    if http_method == 'OPTIONS':
        return {
            'statusCode': 200,
            'headers': cors_headers,
            'body': ''
        }

    # Get the AWS region, convert to uppercase for the PK suffix
    current_aws_region = os.getenv("AWS_REGION", "us-east-1").upper()

    # Fetch products and recommendations for the UI
    if path == '/api/products' and http_method == 'GET':
        try:
            print(f"DEBUG: Scanning {inventory_table.name} for all inventory items.")
            inventory_response = inventory_table.scan()
            all_inventory_items = inventory_response['Items']
            print(f"DEBUG: Found {len(all_inventory_items)} inventory items.")

            print(f"DEBUG: Scanning {recommendations_table.name} for pending price recommendations.")
            recommendations_response = recommendations_table.scan(
                FilterExpression=Key('type').eq('price_adjustment') & Key('status').eq('pending_review')
            )
            pending_price_recommendations = recommendations_response['Items']
            print(f"DEBUG: Found {len(pending_price_recommendations)} pending recommendations.")
            
            print(f"DEBUG: Scanning {demand_forecasts_table.name} for all demand forecasts.")
            demand_forecasts_response = demand_forecasts_table.scan()
            all_demand_forecasts = demand_forecasts_response['Items']
            print(f"DEBUG: Found {len(all_demand_forecasts)} demand forecasts.")

            products_for_ui = []
            recommendations_for_ui = []

            for item in all_inventory_items:
                sku = item['sku']
                sku_region_pk = f"{sku}_{current_aws_region}"
                
                # Convert Decimal values to float immediately after retrieval
                current_price = float(item.get('current_stock', Decimal('1.0')))
                inventory = float(item.get('inventory', Decimal('0')))
                cost = float(item.get('cost', Decimal(str(current_price * 0.7))))

                latest_pending_rec = next(
                    (rec for rec in sorted(pending_price_recommendations, key=lambda x: x['timestamp'], reverse=True) 
                     if rec.get('sku_region_pk') == sku_region_pk),
                    None
                )
                
                latest_forecast = next(
                    (f for f in sorted(all_demand_forecasts, key=lambda x: x['forecast_date'], reverse=True) 
                     if f.get('sku_region_pk') == sku_region_pk),
                    None
                )

                recommended_price = current_price
                recommendation_reason = "No new recommendation."
                
                if latest_pending_rec:
                    recommended_price = float(latest_pending_rec['recommended_price'])
                    recommendation_reason = latest_pending_rec['reason']
                    
                    recommendations_for_ui.append({
                        "id": latest_pending_rec['id'],
                        "sku": sku,
                        "sku_region_pk": sku_region_pk,
                        "name": f"Product {sku}",
                        "category": "General",
                        "currentPrice": current_price,
                        "cost": cost,
                        "inventory": inventory,
                        "region": current_aws_region,
                        "imageUrl": f"https://placehold.co/400x300/E0F2F7/000000?text={sku}",
                        "recommendedPrice": recommended_price,
                        "recommendationReason": recommendation_reason,
                        "latestDemandFactor": float(latest_forecast.get('demand_factor', Decimal('1.0'))) if latest_forecast else 1.0,
                        "latestCompetitorPrice": float(latest_forecast.get('competitor_price', Decimal('0.0'))) if latest_forecast and latest_forecast.get('competitor_price') is not None else None
                    })

                products_for_ui.append({
                    "id": sku,
                    "sku_region_pk": sku_region_pk,
                    "name": f"Product {sku}",
                    "category": "General",
                    "currentPrice": current_price,
                    "cost": cost,
                    "inventory": inventory,
                    "region": current_aws_region,
                    "imageUrl": f"https://placehold.co/400x300/E0F2F7/000000?text={sku}",
                    "recommendedPrice": recommended_price,
                    "recommendationReason": recommendation_reason,
                    "latestDemandFactor": float(latest_forecast.get('demand_factor', Decimal('1.0'))) if latest_forecast else 1.0,
                    "latestCompetitorPrice": float(latest_forecast.get('competitor_price', Decimal('0.0'))) if latest_forecast and latest_forecast.get('competitor_price') is not None else None
                })
            
            return {
                'statusCode': 200,
                'headers': cors_headers,
                'body': json.dumps({
                    'products': products_for_ui,
                    'recommendations': recommendations_for_ui
                }, default=str) # Use default=str to handle Decimal in JSON serialization
            }
        except ClientError as e:
            print(f"ERROR: DynamoDB Client Error fetching products: {e.response['Error']['Message']}")
            return {
                'statusCode': 500,
                'headers': cors_headers,
                'body': json.dumps({'message': f'Error fetching products: {e.response["Error"]["Message"]}'})
            }
        except Exception as e:
            print(f"ERROR: Unexpected error fetching products: {e}")
            return {
                'statusCode': 500,
                'headers': cors_headers,
                'body': json.dumps({'message': f'Error fetching products: {str(e)}'})
            }
            
    # Trigger a full agent run via Step Functions
    elif path == '/api/trigger-agent-run' and http_method == 'POST':
        try:
            print(f"DEBUG: Attempting to start Step Functions execution for state machine ARN: {step_functions_state_machine_arn}")
            response = stepfunctions_client.start_execution(
                stateMachineArn=step_functions_state_machine_arn,
                input=json.dumps({"trigger": "UI_Initiated_Run"})
            )
            print(f"DEBUG: Step Functions execution started: {response['executionArn']}")
            return {
                'statusCode': 200,
                'headers': cors_headers,
                'body': json.dumps({'message': 'Agent workflow triggered successfully.', 'executionArn': response['executionArn']})
            }
        except ClientError as e:
            print(f"ERROR: Step Functions Client Error triggering agent run: {e.response['Error']['Message']}")
            return {
                'statusCode': 500,
                'headers': cors_headers,
                'body': json.dumps({'message': f'Error triggering agent run: {e.response["Error"]["Message"]}'})
            }
        except Exception as e:
            print(f"ERROR: Unexpected error triggering agent run: {e}")
            return {
                'statusCode': 500,
                'headers': cors_headers,
                'body': json.dumps({'message': f'Error triggering agent run: {str(e)}'})
            }

    # Simulate LLM call for promo ideas (by directly calling the Bedrock part of strategy agent)
    elif path == '/api/generate-promo-idea' and http_method == 'POST':
        try:
            request_body = json.loads(event.get('body', '{}'))
            prompt = request_body.get('prompt', 'Generate a general promotion idea.')
            
            # Note: This is a direct import for local testing. In AWS, this would be a separate Lambda call.
            from lambda_functions.promotion_strategy_agent.app import _invoke_bedrock_model
            print(f"DEBUG: Calling Bedrock model via _invoke_bedrock_model with prompt: {prompt[:50]}...")
            promo_text = _invoke_bedrock_model(prompt)
            print(f"DEBUG: Received promo text from Bedrock: {promo_text[:50]}...")

            return {
                'statusCode': 200,
                'headers': cors_headers,
                'body': json.dumps({'promo_idea': promo_text})
            }
        except Exception as e:
            print(f"ERROR: Error generating promo idea: {e}")
            return {
                'statusCode': 500,
                'headers': cors_headers,
                'body': json.dumps({'message': f'Error generating promo idea: {str(e)}'})
            }
    
    # Handle applying a recommendation (update status in DynamoDB)
    elif path == '/api/apply-recommendation' and http_method == 'POST':
        try:
            request_body = json.loads(event.get('body', '{}'))
            recommendation_id = request_body.get('recommendation_id')
            sku = request_body.get('sku')
            new_price = float(request_body.get('new_price'))

            if not recommendation_id or not sku or new_price is None:
                return {
                    'statusCode': 400,
                    'headers': cors_headers,
                    'body': json.dumps({'message': 'Missing recommendation_id, sku, or new_price'})
                }
            
            print(f"DEBUG: Scanning {recommendations_table.name} to find recommendation with ID: {recommendation_id}")
            found_rec_item = None
            scan_response = recommendations_table.scan(
                FilterExpression=Key('id').eq(recommendation_id)
            )
            if scan_response['Items']:
                found_rec_item = scan_response['Items'][0]
                print(f"DEBUG: Found recommendation item: {found_rec_item}")
            else:
                print(f"WARN: Recommendation {recommendation_id} not found to update status.")


            if found_rec_item:
                print(f"DEBUG: Updating status of recommendation {recommendation_id} to 'applied' in {recommendations_table.name}.")
                recommendations_table.update_item(
                    Key={
                        'sku_region_pk': found_rec_item['sku_region_pk'],
                        'timestamp': found_rec_item['timestamp']
                    },
                    UpdateExpression="SET #s = :status_val",
                    ExpressionAttributeNames={'#s': 'status'},
                    ExpressionAttributeValues={':status_val': 'applied'}
                )
                print(f"DEBUG: Recommendation {recommendation_id} status updated to 'applied'.")
            else:
                print(f"WARN: Recommendation {recommendation_id} not found to update status.")


            sku_region_pk = f"{sku}_{current_aws_region}"
            print(f"DEBUG: Updating current_stock for {sku_region_pk} to {new_price} in {inventory_table.name}.")
            inventory_table.update_item(
                Key={'sku_region_pk': sku_region_pk},
                UpdateExpression="SET current_stock = :new_price, last_updated = :ts",
                ExpressionAttributeValues={
                    ':new_price': Decimal(str(new_price)), # Convert back to Decimal for DynamoDB storage
                    ':ts': time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())
                }
            )
            print(f"DEBUG: Inventory table updated for {sku_region_pk}.")

            return {
                'statusCode': 200,
                'headers': cors_headers,
                'body': json.dumps({'message': f'Recommendation {recommendation_id} applied and price updated for {sku}'})
            }
        except ClientError as e:
            print(f"ERROR: DynamoDB Client Error applying recommendation: {e.response['Error']['Message']}")
            return {
                'statusCode': 500,
                'headers': cors_headers,
                'body': json.dumps({'message': f'Error applying recommendation: {e.response["Error"]["Message"]}'})
            }
        except Exception as e:
            print(f"ERROR: Unexpected error applying recommendation: {e}")
            return {
                'statusCode': 500,
                'headers': cors_headers,
                'body': json.dumps({'message': f'Error applying recommendation: {str(e)}'})
            }


    return {
        'statusCode': 404,
        'headers': cors_headers,
        'body': json.dumps({'message': 'Not Found'})
    }
import json
import os
import random
import time
import boto3
from botocore.exceptions import ClientError
from boto3.dynamodb.conditions import Key
from dotenv import load_dotenv
from decimal import Decimal

# Load environment variables (for local testing)
load_dotenv(os.path.join(os.path.dirname(__file__), '..', '..', '.env'))

# AWS Resource Clients
dynamodb = boto3.resource('dynamodb', region_name=os.getenv("AWS_REGION", "us-east-1"))
recommendations_table = dynamodb.Table(os.getenv("PRICING_PROMO_RECOMMENDATIONS_TABLE", "retail-pricing-promo-recommendations"))
demand_forecasts_table = dynamodb.Table(os.getenv("DEMAND_FORECASTS_TABLE", "retail-demand-forecasts"))
inventory_table = dynamodb.Table(os.getenv("INVENTORY_TABLE", "retail-inventory"))
customer_profiles_table = dynamodb.Table(os.getenv("CUSTOMER_PROFILES_TABLE", "retail-customer-profiles"))

bedrock_runtime = boto3.client('bedrock-runtime', region_name=os.getenv("AWS_REGION", "us-east-1"))
bedrock_model_id = os.getenv("BEDROCK_MODEL_ID", "anthropic.claude-3-sonnet-20240229-v1:0")

def _invoke_bedrock_model(user_prompt_text): # Renamed 'prompt' to 'user_prompt_text' for clarity
    """
    Invokes an Amazon Bedrock model to generate promotional content.
    Uses a system prompt to set context.
    """
    try:
        # Define a strong system prompt to set the context
        system_prompt = (
            "You are an expert retail marketing strategist specializing in promotions and sales. "
            "Your goal is to generate creative, concise, and compelling promotional ideas for e-commerce products. "
            "Focus on discounts, bundles, limited-time offers, and engaging marketing copy. "
            "Always provide a specific offer or call to action. Do not give career advice."
        )

        body = json.dumps({
            "anthropic_version": "bedrock-2023-05-31",
            "max_tokens": 200,
            "messages": [
                {"role": "user", "content": [{"type": "text", "text": system_prompt + "\n\n" + user_prompt_text}]} # Combine system and user prompt
            ]
        })
        
        print(f"DEBUG: Invoking Bedrock model {bedrock_model_id} with combined prompt (first 100 chars): {body[:100]}...")
        response = bedrock_runtime.invoke_model(
            modelId=bedrock_model_id,
            contentType="application/json",
            accept="application/json",
            body=body
        )
        
        response_body = json.loads(response.get('body').read())
        if 'content' in response_body and len(response_body['content']) > 0 and 'text' in response_body['content'][0]:
            generated_text = response_body['content'][0]['text']
            print(f"DEBUG: Bedrock generated text: {generated_text[:100]}...")
            return generated_text
        else:
            print(f"WARN: Bedrock response missing expected 'content' or 'text': {response_body}")
            return "Bedrock response format unexpected."
    except ClientError as e:
        print(f"ERROR: Bedrock Client Error: {e.response['Error']['Message']}")
        return "Error generating promo text with Bedrock."
    except Exception as e:
        print(f"ERROR: Unexpected error invoking Bedrock: {e}")
        return "Error generating promo text with Bedrock."

def lambda_handler(event, context):
    """
    Lambda function for the Promotion Strategy Agent.
    Reads forecasts, inventory, and customer data to make recommendations
    and generate personalized promotion ideas using Amazon Bedrock.
    Triggered by Step Functions.
    """
    print("Promotion Strategy Agent triggered.")

    current_aws_region = os.getenv("AWS_REGION", "us-east-1").upper()

    try:
        print(f"DEBUG: Scanning {demand_forecasts_table.name} for all forecasts.")
        forecasts_response = demand_forecasts_table.scan()
        all_forecasts = forecasts_response['Items']
        print(f"DEBUG: Found {len(all_forecasts)} forecasts.")
        
        print(f"DEBUG: Scanning {inventory_table.name} for all inventory items.")
        inventory_response = inventory_table.scan()
        all_inventory_items = inventory_response['Items']
        print(f"DEBUG: Found {len(all_inventory_items)} inventory items.")
        
        print(f"DEBUG: Scanning {customer_profiles_table.name} for all customer profiles.")
        customer_response = customer_profiles_table.scan()
        customer_profiles = customer_response['Items']
        print(f"DEBUG: Found {len(customer_profiles)} customer profiles.")

        pricing_recommendations = []
        promotion_ideas = []

        for current_product_info in all_inventory_items:
            sku = current_product_info['sku']
            sku_region_pk = f"{sku}_{current_aws_region}"
            
            current_price = float(current_product_info.get('current_stock', Decimal('1.0')))
            inventory = float(current_product_info.get('inventory', Decimal('0')))
            cost = float(current_product_info.get('cost', Decimal(str(current_price * 0.7))))

            print(f"DEBUG: Processing SKU {sku_region_pk}. Current Price: {current_price}, Inventory: {inventory}, Cost: {cost}")

            latest_forecast = next(
                (f for f in sorted(all_forecasts, key=lambda x: x['forecast_date'], reverse=True) if f.get('sku_region_pk') == sku_region_pk),
                None
            )
            
            demand_factor = float(latest_forecast.get('demand_factor', Decimal('1.0'))) if latest_forecast else 1.0
            competitor_price = float(latest_forecast.get('competitor_price', Decimal('0.0'))) if latest_forecast and latest_forecast.get('competitor_price') is not None else None
            
            print(f"DEBUG:   Demand Factor: {demand_factor}, Competitor Price: {competitor_price}")

            new_price = current_price
            reason = "Optimal price based on current conditions."

            if demand_factor > 1.1 and inventory > 50:
                new_price = round(current_price * 1.05, 2)
                reason = f"High demand detected ({demand_factor}). Increasing price to maximize revenue."
            elif demand_factor < 0.9 and inventory > 150:
                new_price = round(current_price * 0.9, 2)
                reason = f"Low demand detected ({demand_factor}). Decreasing price to clear inventory."
            elif inventory < 30 and demand_factor > 1.0:
                if current_price < cost * 1.3:
                    new_price = round(current_price * 1.1, 2)
                    reason = f"Critical low stock ({inventory}). Increasing price to manage demand and maximize profit."
            elif competitor_price is not None and competitor_price < current_price * 0.95:
                new_price = round(competitor_price * 0.98, 2)
                reason = f"Competitor price (${competitor_price}) is significantly lower. Adjusting price to remain competitive."
            
            if new_price != current_price:
                rec_id = f"price_{sku}_{int(time.time())}"
                pricing_recommendation_item = {
                    'sku_region_pk': sku_region_pk,
                    'timestamp': time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
                    'id': rec_id,
                    'sku': sku,
                    'original_price': Decimal(str(current_price)),
                    'recommended_price': Decimal(str(new_price)),
                    'reason': reason,
                    'type': 'price_adjustment',
                    'status': 'pending_review',
                }
                pricing_recommendations.append(pricing_recommendation_item)
                print(f"DEBUG: Attempting to put price recommendation to {recommendations_table.name}: {rec_id}, New Price: {new_price}")
                try:
                    recommendations_table.put_item(Item=pricing_recommendation_item)
                    print(f"DEBUG: Successfully put price recommendation {rec_id}")
                except ClientError as e:
                    print(f"ERROR: ClientError putting price recommendation for SKU {sku_region_pk}: {e.response['Error']['Message']}")
                except Exception as e:
                    print(f"ERROR: Unexpected error putting price recommendation for SKU {sku_region_pk}: {e}")
            else:
                print(f"DEBUG: No price change recommended for SKU {sku_region_pk}.")

            for customer in customer_profiles:
                if random.random() < 0.2: # 20% chance to generate promo per customer segment
                    customer_segment = customer['segment']
                    customer_prefs = ", ".join(customer.get('preferences', []))
                    
                    # Construct the user prompt for the LLM
                    user_prompt_for_llm = (
                        f"Generate a concise, engaging promotion idea for product SKU '{sku}' "
                        f"targeting '{customer_segment}' customers (who like {customer_prefs}). "
                        f"Current inventory: {inventory} units. Demand factor: {demand_factor}. "
                        f"Focus on driving sales or clearing inventory. "
                        f"Suggest a specific discount or offer. Max 50 words."
                    )
                    
                    llm_promo_text = _invoke_bedrock_model(user_prompt_for_llm) # Pass the user prompt
                    
                    promo_id = f"promo_{sku}_{customer_segment}_{int(time.time())}"
                    promotion_idea_item = {
                        'sku_region_pk': sku_region_pk,
                        'timestamp': time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
                        'id': promo_id,
                        'sku': sku,
                        'customer_segment': customer_segment,
                        'promo_text': llm_promo_text,
                        'type': 'promotion_idea',
                        'status': 'draft',
                    }
                    promotion_ideas.append(promotion_idea_item)
                    print(f"DEBUG: Attempting to put promo idea to {recommendations_table.name}: {promo_id}")
                    try:
                        recommendations_table.put_item(Item=promotion_idea_item)
                        print(f"DEBUG: Successfully put promo idea {promo_id}")
                    except ClientError as e:
                        print(f"ERROR: ClientError putting promo idea for SKU {sku_region_pk}, segment {customer_segment}: {e.response['Error']['Message']}")
                    except Exception as e:
                        print(f"ERROR: Unexpected error putting promo idea for SKU {sku_region_pk}, segment {customer_segment}: {e}")
                    break # Only one promo per SKU per customer segment for simplicity in demo

        print(f"Generated {len(pricing_recommendations)} pricing recommendations and {len(promotion_ideas)} promotion ideas.")
        return {
            'statusCode': 200,
            'body': json.dumps({
                'message': 'Strategy recommendations generated successfully',
                'pricing_recommendations': pricing_recommendations,
                'promotion_ideas': promotion_ideas
            }, default=str)
        }
    except Exception as e:
        print(f"ERROR: Error in Promotion Strategy Agent: {e}")
        return {
            'statusCode': 500,
            'body': json.dumps({'message': f'Error generating strategy recommendations: {str(e)}'})
        }
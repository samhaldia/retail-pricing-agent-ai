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
sns_client = boto3.client('sns', region_name=os.getenv("AWS_REGION", "us-east-1"))
bedrock_model_id = os.getenv("BEDROCK_MODEL_ID", "anthropic.claude-3-sonnet-20240229-v1:0")
sns_promotion_topic_arn = os.getenv("SNS_PROMOTION_TOPIC_ARN") 

def _invoke_bedrock_model(prompt_text): # This is for general text generation (used by AIPromoGenerator)
    """
    Invokes an Amazon Bedrock model for general text generation (e.g., promo copy).
    Returns raw text response.
    """
    try:
        messages = [
            {"role": "user", "content": [{"type": "text", "text": prompt_text}]}
        ]

        body = json.dumps({
            "anthropic_version": "bedrock-2023-05-31",
            "max_tokens": 200, # Max 200 tokens for promo copy
            "messages": messages
        })
        
        print(f"DEBUG: Invoking Bedrock for general text with prompt (first 100 chars): {body[:100]}...")
        response = bedrock_runtime.invoke_model(
            modelId=bedrock_model_id,
            contentType="application/json",
            accept="application/json",
            body=body
        )
        
        response_body = json.loads(response.get('body').read())
        # --- NEW DEBUG PRINTS FOR BEDROCK RESPONSE ---
        print(f"DEBUG: Raw Bedrock response body for general text: {json.dumps(response_body, indent=2)}")
        # --- END NEW DEBUG PRINTS ---

        # Extract the generated text from the response
        generated_text = response_body['content'][0]['text']
        print(f"DEBUG: Extracted generated text from Bedrock: {generated_text[:100]}...") # Print first 100 chars
        return generated_text

    except ClientError as e:
        print(f"ERROR: Bedrock Client Error for general text generation: {e.response['Error']['Message']}")
        return f"Error: {e.response['Error']['Message']}"
    except Exception as e:
        import traceback # Import traceback here for local debugging
        print(f"ERROR: Unexpected error invoking Bedrock for general text generation: {e}")
        print(traceback.format_exc()) # Print full traceback
        return f"Error: {str(e)}"

def _invoke_bedrock_model_for_recommendation(data_context_prompt): # This is for structured recommendations
    """
    Invokes an Amazon Bedrock model to generate pricing/promotion recommendations
    with reasoning, expecting a structured JSON output.
    """
    try:
        system_prompt = (
            "You are an expert retail pricing and promotion strategist. "
            "Your primary goal is to recommend optimal price adjustments or promotion strategies "
            "to maximize revenue, clear inventory, or remain competitive. "
            "Analyze the provided product data, market conditions, and demand forecasts. "
            "If a price change is beneficial, recommend a specific 'recommended_price' that is different from 'current_price'. "
            "If the current price is truly optimal, recommend the 'current_price'. "
            "Provide your recommendation and detailed reasoning in a JSON format. "
            "The JSON should contain: "
            "'recommended_price' (float), "
            "'recommendation_type' (string, MUST be 'price_adjustment' for price changes, or 'flash_sale', 'bundle_offer' for promotions), "
            "'reason' (string explaining the decision), and "
            "'promo_copy' (string, a short engaging marketing message if applicable, otherwise empty string). "
            "Always output valid JSON only. Do not include any conversational text outside the JSON."
        )

        user_prompt = f"Analyze the following product context and provide an optimal strategy:\n\n{data_context_prompt}"

        messages = [
            {"role": "user", "content": [{"type": "text", "text": system_prompt + "\n\n" + user_prompt}]}
        ]

        body = json.dumps({
            "anthropic_version": "bedrock-2023-05-31",
            "max_tokens": 500, 
            "messages": messages
        })
        
        print(f"DEBUG: Invoking Bedrock for recommendation with prompt (first 200 chars): {body[:200]}...")
        response = bedrock_runtime.invoke_model(
            modelId=bedrock_model_id,
            contentType="application/json",
            accept="application/json",
            body=body
        )
        
        response_body = json.loads(response.get('body').read())
        generated_text = response_body['content'][0]['text']
        print(f"DEBUG: Bedrock raw recommendation response: {generated_text}")

        try:
            llm_recommendation = json.loads(generated_text)
            return llm_recommendation
        except json.JSONDecodeError:
            print(f"ERROR: Bedrock did not return valid JSON for recommendation: {generated_text}")
            return None

    except ClientError as e:
        print(f"ERROR: Bedrock Client Error for recommendation: {e.response['Error']['Message']}")
        return None
    except Exception as e:
        print(f"ERROR: Unexpected error invoking Bedrock for recommendation: {e}")
        return None

def _send_customer_alert(customer_contact_info, message):
    """
    Sends an alert to a customer using AWS SNS.
    customer_contact_info can be a phone number for SMS or an email address.
    """
    try:
        if not sns_promotion_topic_arn:
            print("WARN: SNS_PROMOTION_TOPIC_ARN not set in .env. Skipping customer alert.")
            return False

        if '@' in customer_contact_info: 
            print(f"DEBUG: Attempting to send email alert via SNS topic {sns_promotion_topic_arn} to {customer_contact_info}")
            sns_client.publish(
                TopicArn=sns_promotion_topic_arn,
                Message=message,
                Subject="Exclusive Promotion Alert!"
            )
            print(f"DEBUG: Email alert sent to topic {sns_promotion_topic_arn} for {customer_contact_info}")
        else: 
            print(f"DEBUG: Attempting to send SMS alert to {customer_contact_info}")
            sns_client.publish(
                PhoneNumber=customer_contact_info,
                Message=message
            )
            print(f"DEBUG: SMS alert sent to {customer_contact_info}")
        return True
    except ClientError as e:
        print(f"ERROR: SNS Client Error sending alert to {customer_contact_info}: {e.response['Error']['Message']}")
        return False
    except Exception as e:
        print(f"ERROR: Unexpected error sending alert to {customer_contact_info}: {e}")
        return False

def lambda_handler(event, context):
    """
    Lambda function for the Promotion Strategy Agent.
    Now uses Amazon Bedrock for core pricing/promotion recommendations.
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
            sku = current_product_info.get('sku') 
            if not sku:
                print(f"WARN: Skipping inventory item due to missing 'sku' attribute: {current_product_info}")
                continue

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

            # --- Prepare comprehensive data context for LLM ---
            data_context = {
                "sku": sku,
                "current_price": current_price,
                "inventory": inventory,
                "cost_of_goods": cost,
                "latest_demand_factor": demand_factor,
                "latest_competitor_price": competitor_price,
                "customer_segments_available": [c.get('segment') for c in customer_profiles if c.get('segment')],
                "business_goal_priority": "maximize_revenue_and_clear_excess_inventory_and_be_competitive" 
            }
            context_prompt = json.dumps(data_context, indent=2)

            # --- Invoke Bedrock for the core recommendation ---
            llm_recommendation_output = _invoke_bedrock_model_for_recommendation(context_prompt)

            if llm_recommendation_output:
                new_price = float(llm_recommendation_output.get('recommended_price', current_price))
                recommendation_reason = llm_recommendation_output.get('reason', "LLM provided no specific reason.")
                recommendation_type = llm_recommendation_output.get('recommendation_type', 'price_adjustment')
                promo_copy = llm_recommendation_output.get('promo_copy', '')

                if new_price != current_price or recommendation_type != 'price_adjustment': 
                    rec_id = f"llm_price_{sku}_{int(time.time())}"
                    pricing_recommendation_item = {
                        'sku_region_pk': sku_region_pk,
                        'timestamp': time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
                        'id': rec_id,
                        'sku': sku,
                        'original_price': Decimal(str(current_price)),
                        'recommended_price': Decimal(str(new_price)),
                        'reason': recommendation_reason,
                        'type': recommendation_type, 
                        'promo_copy': promo_copy, 
                        'status': 'pending_review', 
                    }
                    pricing_recommendations.append(pricing_recommendation_item)
                    print(f"DEBUG: Attempting to put LLM-generated recommendation to {recommendations_table.name}: {rec_id}, New Price: {new_price}, Type: {recommendation_type}")
                    try:
                        recommendations_table.put_item(Item=pricing_recommendation_item)
                        print(f"DEBUG: Successfully put LLM-generated recommendation {rec_id}")
                    except ClientError as e:
                        print(f"ERROR: ClientError putting LLM recommendation for SKU {sku_region_pk}: {e.response['Error']['Message']}")
                    except Exception as e:
                        print(f"ERROR: Unexpected error putting LLM recommendation for SKU {sku_region_pk}: {e}")
                else:
                    print(f"DEBUG: LLM recommended no significant price change or specific promo for SKU {sku_region_pk} (type: {recommendation_type}, price: {new_price}).")

                # --- Handle Promotion Idea Generation and Alerting ---
                if promo_copy:
                    llm_promo_text = promo_copy
                    print(f"DEBUG: Using promo copy directly from LLM's recommendation output.")
                else:
                    print(f"DEBUG: LLM did not provide promo_copy. Attempting to generate separate creative text.")
                    user_prompt_for_llm_creative = (
                        f"Generate a concise, engaging marketing message for product SKU '{sku}'. "
                        f"Current inventory: {inventory} units. Demand factor: {demand_factor}. "
                        f"Suggest a specific discount or offer. Max 50 words."
                    )
                    # Use the _invoke_bedrock_model function defined above for simple text generation
                    llm_promo_text = _invoke_bedrock_model(user_prompt_for_llm_creative)


                if llm_promo_text and "Error:" not in llm_promo_text: # Check for actual content, not just error string
                    for customer in customer_profiles:
                        if random.random() < 0.2: 
                            customer_segment = customer['segment']
                            customer_prefs = ", ".join(customer.get('preferences', []))
                            customer_contact = customer.get('email') or customer.get('phone_number') 
                            
                            promo_id = f"promo_{sku}_{customer['customer_id']}_{int(time.time())}"
                            promotion_idea_item = {
                                'sku_region_pk': sku_region_pk,
                                'timestamp': time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
                                'id': promo_id,
                                'sku': sku,
                                'customer_id': customer['customer_id'],
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
                                
                                if customer_contact and llm_promo_text:
                                    alert_message = f"📢 Special Offer for You!\nProduct: {sku}\nOffer: {llm_promo_text}\nDon't miss out!"
                                    if _send_customer_alert(customer_contact, alert_message):
                                        recommendations_table.update_item(
                                            Key={'sku_region_pk': sku_region_pk, 'timestamp': promotion_idea_item['timestamp']},
                                            UpdateExpression="SET #status = :sent_status",
                                            ExpressionAttributeNames={'#status': 'status'},
                                            ExpressionAttributeValues={':sent_status': 'sent'}
                                        )
                                        print(f"DEBUG: Successfully sent promotion alert for SKU {sku} to {customer_contact}. Status updated to 'sent'.")
                                    else:
                                        print(f"WARN: Failed to send promotion alert for SKU {sku} to {customer_contact}.")

                            except ClientError as e:
                                print(f"ERROR: ClientError putting promo idea for SKU {sku_region_pk}, segment {customer_segment}: {e.response['Error']['Message']}")
                            except Exception as e:
                                print(f"ERROR: Unexpected error putting promo idea for SKU {sku_region_pk}, segment {customer_segment}: {e}")
                            break 
                else:
                    print(f"DEBUG: No valid promo copy generated for SKU {sku_region_pk} to send alerts.")
            else:
                print(f"WARN: Bedrock recommendation invocation failed or returned no valid output for SKU {sku_region_pk}.")

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
        import traceback
        print(f"ERROR: Error in Promotion Strategy Agent: {e}")
        print(traceback.format_exc())
        return {
            'statusCode': 500,
            'body': json.dumps({'message': f'Error generating strategy recommendations: {str(e)}'})
        }
import boto3
import json
import os

dynamodb = boto3.resource("dynamodb")
table = dynamodb.Table(os.environ["TABLE_NAME"])

def lambda_handler(event, context):
    order_id = event["pathParameters"]["id"]
    
    resp = table.get_item(Key={"id": order_id})
    item = resp.get("Item")

    if not item:
        return {
            "statusCode": 404,
            "body": json.dumps({"error": "Order not found"})
        }

    return {
        "statusCode": 200,
        "body": json.dumps(item)
    }

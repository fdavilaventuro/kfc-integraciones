import boto3
import json
import os
from decimal import Decimal

dynamodb = boto3.resource("dynamodb")
table = dynamodb.Table(os.environ["TABLE_NAME"])

# Convierte Decimal a string para JSON
def decimal_default(obj):
    if isinstance(obj, Decimal):
        return str(obj)
    raise TypeError

def lambda_handler(event, context):
    try:
        order_id = event["pathParameters"]["id"]
        
        # Obtener orden de DynamoDB
        resp = table.get_item(Key={"id": order_id})
        item = resp.get("Item")

        if not item:
            return {
                "statusCode": 404,
                "body": json.dumps({"error": "Order not found"})
            }

        # Extraer historial de estados si existe
        status_history = item.get("statusHistory", [])
        current_status = item.get("status", "PENDING")

        result = {
            "id": item["id"],
            "currentStatus": current_status,
            "statusHistory": status_history,
            # Incluir otros campos relevantes de la orden
            **{k: v for k, v in item.items() if k not in ["status", "statusHistory", "id"]}
        }

        return {
            "statusCode": 200,
            "body": json.dumps(result, default=decimal_default)
        }

    except Exception as e:
        return {
            "statusCode": 500,
            "body": json.dumps({"error": "Error interno", "details": str(e)})
        }

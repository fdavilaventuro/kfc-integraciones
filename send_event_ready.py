import boto3
import json
import os
from decimal import Decimal

events = boto3.client("events")
dynamodb = boto3.resource("dynamodb")
table = dynamodb.Table(os.environ["TABLE_NAME"])

# Convierte Decimal a string para JSON
def decimal_default(obj):
    if isinstance(obj, Decimal):
        return str(obj)
    raise TypeError

def lambda_handler(event, context):
    try:
        # Validar body
        if "body" not in event or not event["body"]:
            return {"statusCode": 400, "body": json.dumps({"error": "Body vacío o inválido"})}

        body = json.loads(event["body"])
        if "orderId" not in body:
            return {"statusCode": 400, "body": json.dumps({"error": "Falta 'orderId'"})}

        order_id = body["orderId"]

        # Verificar que la orden exista
        resp = table.get_item(Key={"id": order_id})
        if "Item" not in resp:
            return {"statusCode": 404, "body": json.dumps({"error": f"Orden {order_id} no existe"})}

        # Enviar evento ORDER.READY a EventBridge
        event_resp = events.put_events(
            Entries=[{
                "Source": "kfc.orders",
                "DetailType": "ORDER.READY",
                "EventBusName": os.environ["EVENT_BUS"],
                "Detail": json.dumps({"orderId": order_id})
            }]
        )

        return {
            "statusCode": 200,
            "body": json.dumps({
                "message": "READY enviado",
                "eventResponse": event_resp
            }, default=decimal_default)
        }

    except Exception as e:
        return {"statusCode": 500, "body": json.dumps({"error": str(e)})}

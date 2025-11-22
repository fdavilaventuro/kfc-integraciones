import json
import time
import boto3
import os
from decimal import Decimal

dynamodb = boto3.resource("dynamodb")
table = dynamodb.Table(os.environ["TABLE_NAME"])
events = boto3.client("events")

# Convierte Decimal a string para JSON
def decimal_default(obj):
    if isinstance(obj, Decimal):
        return str(obj)
    raise TypeError

def lambda_handler(event, context):
    try:
        body = json.loads(event.get("body", "{}"))
        order_id = body.get("orderId")
        if not order_id:
            return {"statusCode": 400, "body": json.dumps({"error": "orderId requerido"})}

        # Verificar que la orden exista
        resp = table.get_item(Key={"id": order_id})
        order = resp.get("Item")
        if not order:
            return {"statusCode": 404, "body": json.dumps({"error": "Orden no encontrada"})}

        # Simular pago (generar paymentId)
        payment_id = f"PAY-{int(time.time())}"

        # Enviar evento ORDER.PAID a EventBridge
        event_resp = events.put_events(
            Entries=[{
                "Source": "kfc.orders",
                "DetailType": "ORDER.PAID",
                "EventBusName": os.environ["EVENT_BUS"],
                "Detail": json.dumps({"orderId": order_id, "paymentId": payment_id})
            }]
        )

        return {
            "statusCode": 200,
            "body": json.dumps({
                "message": "PAID enviado",
                "eventResponse": event_resp
            }, default=decimal_default)
        }

    except Exception as e:
        return {"statusCode": 500, "body": json.dumps({"error": str(e)})}

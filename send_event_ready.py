import boto3
import json
import os
from datetime import datetime

events = boto3.client("events")
dynamodb = boto3.resource("dynamodb")
table = dynamodb.Table(os.environ["TABLE_NAME"])

# Transiciones válidas
VALID_TRANSITIONS = {
    "PENDING": ["READY"],
    "READY": [],
    "PAID": []
}

def lambda_handler(event, context):
    try:
        if "body" not in event or not event["body"]:
            return {"statusCode": 400, "body": json.dumps({"error": "Body vacío o inválido"})}

        body = json.loads(event["body"])
        order_id = body.get("orderId")
        if not order_id:
            return {"statusCode": 400, "body": json.dumps({"error": "Falta 'orderId'"})}

        # Obtener orden
        resp = table.get_item(Key={"id": order_id})
        order = resp.get("Item")
        if not order:
            return {"statusCode": 404, "body": json.dumps({"error": f"Orden {order_id} no existe"})}

        # Validar transición
        current_status = order.get("status", "PENDING")
        if "READY" not in VALID_TRANSITIONS.get(current_status, []):
            return {
                "statusCode": 400,
                "body": json.dumps({
                    "error": f"No se puede pasar de {current_status} → READY"
                })
            }

        # Actualizar estado en DynamoDB
        now = datetime.utcnow().isoformat() + "Z"
        table.update_item(
            Key={"id": order_id},
            UpdateExpression="""
                SET #s = :s,
                    updatedAt = :t,
                    statusHistory = list_append(if_not_exists(statusHistory, :empty_list), :h)
            """,
            ExpressionAttributeNames={"#s": "status"},
            ExpressionAttributeValues={
                ":s": "READY",
                ":t": now,
                ":h": [{"status": "READY", "timestamp": now}],
                ":empty_list": []
            }
        )

        # Enviar evento a EventBridge
        resp_event = events.put_events(
            Entries=[{
                "Source": "kfc.orders",
                "DetailType": "ORDER.READY",
                "EventBusName": os.environ["EVENT_BUS"],
                "Detail": json.dumps({"orderId": order_id})
            }]
        )

        return {
            "statusCode": 200,
            "body": json.dumps({"message": "READY enviado y estado actualizado", "eventResponse": resp_event})
        }

    except Exception as e:
        return {"statusCode": 500, "body": json.dumps({"error": str(e)})}

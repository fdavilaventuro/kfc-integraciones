import boto3
import json
import os
from decimal import Decimal
import time

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

        # Verificar orden en DynamoDB
        resp = table.get_item(Key={"id": order_id})
        if "Item" not in resp:
            return {"statusCode": 404, "body": json.dumps({"error": f"Orden {order_id} no existe"})}

        # Actualizar estado a READY y guardar en historial
        now = time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())
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

        # Enviar evento EventBridge
        event_resp = events.put_events(
            Entries=[{
                "Source": "kfc.orders",
                "DetailType": "ORDER.READY",
                "EventBusName": os.environ["EVENT_BUS"],
                "Detail": json.dumps({"orderId": order_id})
            }]
        )

        # Obtener orden actualizada
        updated_order = table.get_item(Key={"id": order_id})["Item"]

        return {
            "statusCode": 200,
            "body": json.dumps({
                "message": "READY enviado y estado actualizado",
                "eventResponse": event_resp,
                "order": updated_order
            }, default=decimal_default)
        }

    except Exception as e:
        return {"statusCode": 500, "body": json.dumps({"error": str(e)})}

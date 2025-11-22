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

# Reglas de transición válidas
VALID_TRANSITIONS = {
    "PENDING": ["READY"],      # Para poder pagar, primero debe estar READY
    "READY": ["PAID"],         # Solo READY → PAID
    "PAID": []                  # No se puede volver a pagar
}

def lambda_handler(event, context):
    try:
        body = json.loads(event.get("body", "{}"))
        order_id = body.get("orderId")
        if not order_id:
            return {"statusCode": 400, "body": json.dumps({"error": "orderId requerido"})}

        # Obtener orden
        resp = table.get_item(Key={"id": order_id})
        order = resp.get("Item")
        if not order:
            return {"statusCode": 404, "body": json.dumps({"error": "Orden no encontrada"})}

        current_status = order.get("status", "PENDING")

        # Validar transición
        if "PAID" not in VALID_TRANSITIONS.get(current_status, []):
            return {
                "statusCode": 400,
                "body": json.dumps({
                    "error": f"No se puede pagar la orden en estado {current_status}"
                })
            }

        # Simular pago
        payment_id = f"PAY-{int(time.time())}"
        now = time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())

        # Actualizar estado a PAID y agregar al historial
        table.update_item(
            Key={"id": order_id},
            UpdateExpression="""
                SET #s = :s,
                    updatedAt = :t,
                    paymentId = :p,
                    statusHistory = list_append(if_not_exists(statusHistory, :empty_list), :h)
            """,
            ExpressionAttributeNames={"#s": "status"},
            ExpressionAttributeValues={
                ":s": "PAID",
                ":t": now,
                ":p": payment_id,
                ":h": [{"status": "PAID", "timestamp": now}],
                ":empty_list": []
            }
        )

        # Enviar evento EventBridge (opcional, si quieres notificar)
        event_resp = events.put_events(
            Entries=[{
                "Source": "kfc.orders",
                "DetailType": "ORDER.PAID",
                "EventBusName": os.environ["EVENT_BUS"],
                "Detail": json.dumps({"orderId": order_id})
            }]
        )

        # Obtener orden actualizada
        updated_order = table.get_item(Key={"id": order_id})["Item"]

        return {
            "statusCode": 200,
            "body": json.dumps({
                "message": "PAID enviado y estado actualizado",
                "eventResponse": event_resp,
                "order": updated_order
            }, default=decimal_default)
        }

    except Exception as e:
        return {"statusCode": 500, "body": json.dumps({"error": str(e)})}

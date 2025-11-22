import json
import time
import boto3
import os

dynamodb = boto3.resource("dynamodb")
table = dynamodb.Table(os.environ["TABLE_NAME"])

# Reglas de transición válidas
VALID_TRANSITIONS = {
    "PENDING": [],      # No se puede pagar aún
    "READY": ["PAID"],  # Solo READY → PAID
    "PAID": []          # No se puede volver a pagar
}

def lambda_handler(event, context):
    try:
        body = json.loads(event.get("body", "{}"))
        order_id = body.get("orderId")
        if not order_id:
            return {"statusCode": 400, "body": json.dumps({"error": "orderId requerido"})}

        # Traer orden de DynamoDB
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

        # Actualizar orden en DynamoDB
        now = time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())
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

        return {
            "statusCode": 200,
            "body": json.dumps({
                "paymentId": payment_id,
                "status": "PAID",
                "message": "Pago simulado correctamente."
            })
        }

    except Exception as e:
        return {"statusCode": 500, "body": json.dumps({"error": str(e)})}

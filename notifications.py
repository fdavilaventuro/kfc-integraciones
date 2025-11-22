import json
import boto3
import os
from datetime import datetime

# Conexión a DynamoDB
dynamodb = boto3.resource("dynamodb")
table = dynamodb.Table(os.environ["TABLE_NAME"])

# Definimos transiciones válidas
VALID_TRANSITIONS = {
    "PENDING": ["READY"],
    "READY": ["PAID"],
    "PAID": []
}

def lambda_handler(event, context):
    print("Evento recibido:", json.dumps(event))

    # EventBridge puede enviar un solo evento o batch
    records = event.get("Records", [event])

    for record in records:
        # Detalle del evento
        detail = record.get("detail", {})
        if "body" in record:
            try:
                detail = json.loads(record["body"])
            except:
                print("ERROR parsing body:", record["body"])
                continue

        order_id = detail.get("orderId")
        status_event = record.get("detail-type") or detail.get("type")

        if not order_id:
            print("ERROR: No orderId in event")
            continue

        # Mapear eventos a status
        status_map = {
            "ORDER.READY": "READY",
            "ORDER.PAID": "PAID",
            "ORDER.CREATED": "PENDING"  # asumimos PENDING al crear
        }
        new_status = status_map.get(status_event)

        if not new_status:
            print("Evento desconocido:", status_event)
            continue

        try:
            # Traer orden actual
            resp = table.get_item(Key={"id": order_id})
            item = resp.get("Item")

            if not item:
                print(f"ERROR: Orden {order_id} no existe")
                continue

            current_status = item.get("status", "PENDING")

            # Validar transición
            if new_status not in VALID_TRANSITIONS.get(current_status, []):
                print(f"Transición inválida: {current_status} → {new_status}")
                continue

            now = datetime.utcnow().isoformat()

            # Actualizar status, historial y timestamp
            table.update_item(
                Key={"id": order_id},
                UpdateExpression="""
                    SET #s = :s,
                        updatedAt = :t,
                        statusHistory = list_append(if_not_exists(statusHistory, :empty_list), :h)
                """,
                ExpressionAttributeNames={"#s": "status"},
                ExpressionAttributeValues={
                    ":s": new_status,
                    ":t": now,
                    ":h": [{"status": new_status, "timestamp": now}],
                    ":empty_list": []
                }
            )
            print(f"Orden {order_id} actualizada: {current_status} → {new_status} a las {now}")

        except Exception as e:
            print(f"ERROR procesando orden {order_id}: {e}")

    return {"msg": "processed"}

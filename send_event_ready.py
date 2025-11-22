import boto3
import json
import os

client = boto3.client("events")

def lambda_handler(event, context):
    try:
        # Validar que el body exista
        if "body" not in event:
            return {"statusCode": 400, "body": json.dumps({"error": "No se recibió body en la solicitud"})}

        # Validar JSON
        try:
            body = json.loads(event["body"])
        except Exception:
            return {"statusCode": 400, "body": json.dumps({"error": "Body no es un JSON válido"})}

        # Validar orderId
        order_id = body.get("orderId") or body.get("order_id")
        if not order_id:
            return {"statusCode": 400, "body": json.dumps({"error": "Falta el campo obligatorio 'orderId'"})}

        # Enviar evento
        resp = client.put_events(
            Entries=[{
                "Source": "kfc.orders",
                "DetailType": "ORDER.READY",
                "EventBusName": os.environ["EVENT_BUS"],
                "Detail": json.dumps({"orderId": order_id})
            }]
        )

        return {"statusCode": 200, "body": json.dumps(resp)}

    except Exception as e:
        # Error inesperado
        return {
            "statusCode": 500,
            "body": json.dumps({"error": "Error interno en send_event_ready", "detail": str(e)})
        }

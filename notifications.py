import json

def lambda_handler(event, context):
    try:
        print("===== Evento recibido en notification_handler =====")
        print(json.dumps(event))

        # EventBridge envía eventos en event["detail"]
        records = event.get("detail")
        if not records:
            print("Evento sin 'detail'")
            return {"statusCode": 400, "body": json.dumps({"error": "Evento inválido"})}

        event_type = event.get("detail-type")
        order_id = records.get("orderId")

        if not order_id:
            print("Falta orderId en el evento")
            return {"statusCode": 400, "body": json.dumps({"error": "Falta orderId"})}

        print(f"Procesando evento {event_type} para orden {order_id}")

        # Aquí podrías enviar notificaciones por WebSocket, SNS, Firebase, etc.
        # ---------------------------------------------------------------
        #   EJEMPLO: enviar mensaje a consola simulando envío real
        # ---------------------------------------------------------------
        print(f"Notificación enviada: {event_type} para orden {order_id}")

        return {
            "statusCode": 200,
            "body": json.dumps({"message": "processed", "event": event_type, "orderId": order_id})
        }

    except Exception as e:
        print("ERROR notification_handler:", str(e))
        return {
            "statusCode": 500,
            "body": json.dumps({"error": "Error interno", "details": str(e)})
        }

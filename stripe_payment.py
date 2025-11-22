import json
import time

def lambda_handler(event, context):
    try:
        print("Evento recibido stripe_payment:", json.dumps(event))

        body = json.loads(event.get("body", "{}"))

        # Parámetros mock opcionales
        amount = body.get("amount", 0)
        currency = body.get("currency", "USD")

        payment_id = f"PAY-{int(time.time())}"

        resp = {
            "paymentId": payment_id,
            "status": "PAID",
            "amount": amount,
            "currency": currency,
            "message": "Pago simulado correctamente."
        }

        return {"statusCode": 200, "body": json.dumps(resp)}

    except Exception as e:
        print("ERROR stripe_payment:", str(e))
        return {
            "statusCode": 500,
            "body": json.dumps({"error": "Error interno en pago simulado", "details": str(e)})
        }

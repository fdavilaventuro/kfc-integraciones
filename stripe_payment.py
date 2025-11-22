import json
import time

def lambda_handler(event, context):
    payment_id = f"PAY-{int(time.time())}"

    return {
        "statusCode": 200,
        "body": json.dumps({
            "paymentId": payment_id,
            "status": "PAID",
            "message": "Pago simulado correctamente."
        })
    }

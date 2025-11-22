import json
import boto3
import os
import stripe

stripe.api_key = os.environ["STRIPE_SECRET"]
dynamodb = boto3.resource("dynamodb")
table = dynamodb.Table(os.environ["TABLE_NAME"])

def lambda_handler(event, context):
    body = json.loads(event["body"])
    order_id = body["orderId"]
    amount = int(float(body["amount"]) * 100)

    # Crear intento de pago
    payment = stripe.PaymentIntent.create(
        amount=amount,
        currency="usd",
        metadata={"orderId": order_id}
    )

    # Actualizar orden como pagada
    table.update_item(
        Key={"id": order_id},
        UpdateExpression="SET #s = :s, paymentId = :p",
        ExpressionAttributeNames={"#s": "status"},
        ExpressionAttributeValues={":s": "PAID", ":p": payment.id}
    )

    return {
        "statusCode": 200,
        "body": json.dumps({
            "paymentId": payment.id,
            "status": "PAID"
        })
    }

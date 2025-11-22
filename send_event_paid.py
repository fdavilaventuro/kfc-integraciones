import boto3
import json
import os

events = boto3.client("events")
dynamodb = boto3.resource("dynamodb")
table = dynamodb.Table(os.environ["TABLE_NAME"])

def lambda_handler(event, context):
    try:
        # Validar body
        if "body" not in event or not event["body"]:
            return {"statusCode": 400, "body": json.dumps({"error": "Body vacío o inválido"})}

        body = json.loads(event["body"])

        if "orderId" not in body:
            return {"statusCode": 400, "body": json.dumps({"error": "Falta 'orderId'"})}

        order_id = body["orderId"]

        # Verificar si existe la orden
        result = table.get_item(Key={"id": order_id})

        if "Item" not in result:
            return {"statusCode": 404, "body": json.dumps({"error": f"Orden {order_id} no existe"})}

        # Enviar evento
        resp = events.put_events(
            Entries=[{
                "Source": "kfc.orders",
                "DetailType": "ORDER.PAID",
                "EventBusName": os.environ["EVENT_BUS"],
                "Detail": json.dumps({"orderId": order_id})
            }]
        )

        return {"statusCode": 200, "body": json.dumps({"message": "Evento enviado", "eventResponse": resp})}

    except Exception as e:
        print("ERROR:", str(e))
        return {"statusCode": 500, "body": json.dumps({"error": str(e)})}

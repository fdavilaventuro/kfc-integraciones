import boto3
import json
import os

dynamodb = boto3.resource("dynamodb")
table = dynamodb.Table(os.environ["TABLE_NAME"])

def lambda_handler(event, context):
    try:
        print("Evento recibido:", json.dumps(event))

        # Validar path params
        path = event.get("pathParameters")
        if not path or "id" not in path:
            return {
                "statusCode": 400,
                "body": json.dumps({"error": "Falta parámetro 'id' en la URL"})
            }

        order_id = path["id"]

        # Buscar en DynamoDB
        resp = table.get_item(Key={"id": order_id})
        item = resp.get("Item")

        if not item:
            return {
                "statusCode": 404,
                "body": json.dumps({"error": f"Orden '{order_id}' no encontrada"})
            }

        return {
            "statusCode": 200,
            "body": json.dumps(item)
        }

    except Exception as e:
        print("ERROR get_order_status:", str(e))
        return {
            "statusCode": 500,
            "body": json.dumps({"error": "Error interno", "details": str(e)})
        }

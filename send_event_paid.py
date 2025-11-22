import boto3
import json
import os

client = boto3.client("events")

def lambda_handler(event, context):
    body = json.loads(event["body"])
    order_id = body["orderId"]

    resp = client.put_events(
        Entries=[{
            "Source": "kfc.orders",
            "DetailType": "ORDER.PAID",
            "EventBusName": os.environ["EVENT_BUS"],
            "Detail": json.dumps({"orderId": order_id})
        }]
    )

    return {"statusCode": 200, "body": json.dumps(resp)}

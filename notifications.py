import json

def lambda_handler(event, context):
    print("Evento recibido:", json.dumps(event))
    return {"msg": "processed"}

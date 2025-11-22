# KFC Integraciones

Este repositorio contiene la lógica de **integraciones** del sistema de pedidos de KFC, incluyendo **DynamoDB**, **EventBridge**, **S3** y simulación de pagos con **Stripe**. Este módulo se integra con el frontend y el workflow de Step Functions.

---

## Contenido del Repo

- `serverless.yml` → Configuración de infraestructura y funciones Lambda.
- Lambdas:
  - `get_order_status.py` → Consulta el estado de una orden.
  - `stripe_payment.py` → Simula un pago y envía eventos a EventBridge.
  - `send_event_ready.py` → Envía evento `ORDER.READY`.
  - `notifications.py` → Lambda que procesa eventos de EventBridge (`notification_handler`).
- `README.md` → Documentación y guía de uso.

---

## Recursos en AWS

| Recurso | Descripción |
|---------|------------|
| DynamoDB Table | `Orders` → guarda las órdenes y su historial de estados. |
| EventBridge Bus | `orders-bus` → recibe eventos `ORDER.READY` y `ORDER.PAID`. |
| S3 Bucket | `kfc-assets` → almacena imágenes o assets del frontend. |
| Lambda Functions | Gestionan eventos, pagos simulados y consultas de estado. |

---

## Variables de Entorno

Asegúrate de definir estas variables en cada Lambda o en Serverless:

```text
TABLE_NAME=Orders
EVENT_BUS=orders-bus
REGION=us-east-1
````

---

## Endpoints API

| Método | Ruta           | Descripción                                                             |
| ------ | -------------- | ----------------------------------------------------------------------- |
| GET    | `/status/{id}` | Consulta el estado de la orden.                                         |
| POST   | `/pay`         | Simula un pago y genera evento `ORDER.PAID`.                            |
| POST   | `/event/ready` | Envía evento `ORDER.READY` para simular que la cocina terminó la orden. |

> **Nota:** `/event/paid` ya no es necesario, la transición a `PAID` se hace desde `/pay`.

---

## Ejemplo de Orden para DynamoDB

```bash
aws dynamodb put-item \
    --table-name Orders \
    --item '{
        "id": {"S": "ORDER-001"},
        "status": {"S": "PENDING"},
        "statusHistory": {"L":[]}
    }' \
    --region us-east-1
```

Puedes crear varias órdenes (`ORDER-002`, `ORDER-003`) para pruebas.

---

## Flujo de Pruebas Recomendado

1. Insertar una orden en DynamoDB (`PENDING`).
2. Consultar estado inicial:

   ```http
   GET /status/ORDER-001
   ```
3. Marcar orden como lista (`READY`):

   ```http
   POST /event/ready
   {
       "orderId": "ORDER-001"
   }
   ```
4. Confirmar cambio:

   ```http
   GET /status/ORDER-001
   ```
5. Simular pago:

   ```http
   POST /pay
   {
       "orderId": "ORDER-001"
   }
   ```
6. Confirmar estado `PAID`:

   ```http
   GET /status/ORDER-001
   ```

---

## EventBridge

Eventos que se envían y consumen:

* `ORDER.READY` → enviado por `send_event_ready.py`.
* `ORDER.PAID` → enviado por `stripe_payment.py`.
* `notification_handler` consume ambos eventos y actualiza el historial de la orden.

Ejemplo de payload:

```json
{
  "orderId": "ORDER-001"
}
```

---

## Logs y Depuración

Todos los logs de Lambda están en **CloudWatch**:

* `/aws/lambda/kfc-integraciones-dev-get_order_status`
* `/aws/lambda/kfc-integraciones-dev-stripe_payment`
* `/aws/lambda/kfc-integraciones-dev-send_order_ready`
* `/aws/lambda/kfc-integraciones-dev-notification_handler`

Verifica los logs para entender la transición de estados y errores.

---

## Recomendaciones

* No actualizar el estado directamente desde `notification_handler` si ya se hace en las Lambdas de acción (evita redundancia).
* Usar siempre la función `/status/{id}` para consultar el estado más reciente.
* Para pruebas de integración, usar Postman o CURL con los endpoints definidos.

---

## Diagrama de Flujo Simplificado

```
Frontend/API Gateway
       |
       v
   /pay  ---> stripe_payment.py ---> EventBridge (ORDER.PAID)
       |
   /event/ready ---> send_event_ready.py ---> EventBridge (ORDER.READY)
       |
       v
notification_handler.py (historial)
       |
       v
DynamoDB Orders
```

---

## Contribución

1. Clonar el repo.
2. Configurar variables de entorno.
3. Hacer deploy con Serverless:

```bash
sls deploy
```

4. Probar endpoints siguiendo el flujo recomendado.

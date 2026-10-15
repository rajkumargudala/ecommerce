# Extra API examples

## Create a product

```bash
curl -X POST http://localhost:8082/products \
  -H "Content-Type: application/json" \
  -d '{"name":"Platform Engineering Mug","category":"Workspace","description":"Demo item","price":16.50,"image":"☕"}'
```

If the new product is id 7:

```bash
curl -X POST http://localhost:8083/inventory/7/adjust \
  -H "Content-Type: application/json" \
  -d '{"delta":40}'
```

## Manually reserve inventory

```bash
curl -X POST http://localhost:8083/inventory/reserve \
  -H "Content-Type: application/json" \
  -d '{"items":[{"productId":1,"quantity":2}]}'
```

## Send a notification

```bash
curl -X POST http://localhost:8086/notifications \
  -H "Content-Type: application/json" \
  -d '{"recipient":"admin@devopsshack.com","type":"INFO","subject":"Manual notification","message":"Notification service works."}'
```

## Manage a cart

Set the quantity for a product in a customer's cart:

```bash
curl -X PUT http://localhost/api/cart/carts/customer-123/items \
  -H "Content-Type: application/json" \
  -d '{"productId":1,"quantity":2}'
```

Read it with `GET /api/cart/carts/customer-123`; remove one item with `DELETE /api/cart/carts/customer-123/items/1`, or clear the cart with `DELETE /api/cart/carts/customer-123`.

## Create and track a shipment

```bash
curl -X POST http://localhost/api/shipping/shipments \
  -H "Content-Type: application/json" \
  -d '{"orderId":101,"recipientName":"Alex Customer","addressLine1":"1 Market Street","city":"San Francisco","region":"CA","postalCode":"94105","country":"US"}'
```

Track by shipment ID with `GET /api/shipping/shipments/1`. Update progress with `PATCH /api/shipping/shipments/1/status` and `{"status":"IN_TRANSIT"}`.

## Submit and summarize product reviews

```bash
curl -X POST http://localhost/api/reviews/reviews \
  -H "Content-Type: application/json" \
  -d '{"productId":1,"customerId":"customer-123","rating":5,"title":"Great product","body":"Works as described."}'
```

Read reviews with `GET /api/reviews/reviews?productId=1` and the aggregate with `GET /api/reviews/reviews/summary?productId=1`.

## Validate and redeem a promotion

The service seeds `WELCOME10` (10% off a subtotal of at least $25) and `SAVE5` ($5 off a subtotal of at least $20):

```bash
curl -X POST http://localhost/api/promotions/promotions/validate \
  -H "Content-Type: application/json" \
  -d '{"code":"WELCOME10","customerId":"customer-123","subtotal":50}'
```

Redeem after order creation by sending the same fields plus `"orderId":"101"` to `POST /api/promotions/promotions/redeem`.

## Index and search products

The catalog should publish product changes to the search index using `PUT /api/search/search/index`:

```bash
curl -X PUT http://localhost/api/search/search/index \
  -H "Content-Type: application/json" \
  -d '{"productId":1,"name":"AI Mechanical Keyboard","category":"Workspace","description":"Low-profile mechanical keyboard","price":79.99,"image":"⌨️","active":true}'
```

Search indexed products with `GET /api/search/search?q=keyboard` or filter with `&category=Workspace`.

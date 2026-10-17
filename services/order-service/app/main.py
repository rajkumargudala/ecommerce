import os
import json
import logging
import threading
from datetime import datetime, timezone
from decimal import Decimal
from typing import Literal
from uuid import uuid4

import boto3
import httpx
import psycopg2
from kafka import KafkaProducer
from psycopg2.extras import RealDictCursor, Json
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, EmailStr, Field

DB_DSN = os.getenv(
    "ORDER_DB_DSN",
    "dbname=order_db user=order_user password=order_db_password_123 host=order-db port=5432",
)
CATALOG_URL = os.getenv("CATALOG_URL", "http://catalog-service:8082")
INVENTORY_URL = os.getenv("INVENTORY_URL", "http://inventory-service:8083")
NOTIFICATION_URL = os.getenv("NOTIFICATION_URL", "http://notification-service:8086")
PROMOTIONS_URL = os.getenv("PROMOTIONS_URL", "http://promotions-service:8091")
KAFKA_BOOTSTRAP_SERVERS = os.getenv("KAFKA_BOOTSTRAP_SERVERS", "")
KAFKA_SECRET_ARN = os.getenv("KAFKA_SECRET_ARN", "")
AWS_REGION = os.getenv("AWS_REGION", os.getenv("AWS_DEFAULT_REGION", "us-east-1"))
KAFKA_ORDERS_TOPIC = os.getenv("KAFKA_ORDERS_TOPIC", "orders.created")
KAFKA_ENABLED = bool(KAFKA_BOOTSTRAP_SERVERS or KAFKA_SECRET_ARN)

if KAFKA_ENABLED and not (KAFKA_BOOTSTRAP_SERVERS and KAFKA_SECRET_ARN):
    raise RuntimeError("KAFKA_BOOTSTRAP_SERVERS and KAFKA_SECRET_ARN must both be configured")

logger = logging.getLogger("order-service")
_producer = None
_producer_lock = threading.Lock()
_dispatcher_stop = threading.Event()
_dispatcher_thread = None

app = FastAPI(title="DevOps Shack Order Service", version="1.0.0")
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

def conn():
    return psycopg2.connect(DB_DSN, cursor_factory=RealDictCursor)

def migrate():
    with conn() as db:
        with db.cursor() as cur:
            cur.execute("""
                CREATE TABLE IF NOT EXISTS orders (
                    id BIGSERIAL PRIMARY KEY,
                    user_email VARCHAR(200) NOT NULL,
                    status VARCHAR(40) NOT NULL DEFAULT 'CREATED',
                    total NUMERIC(12,2) NOT NULL CHECK(total>=0),
                    items JSONB NOT NULL,
                    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
                    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
                )
            """)
            cur.execute("ALTER TABLE orders ADD COLUMN IF NOT EXISTS subtotal NUMERIC(12,2)")
            cur.execute("ALTER TABLE orders ADD COLUMN IF NOT EXISTS discount_amount NUMERIC(12,2) NOT NULL DEFAULT 0")
            cur.execute("ALTER TABLE orders ADD COLUMN IF NOT EXISTS promotion_code VARCHAR(80)")
            cur.execute("UPDATE orders SET subtotal=total WHERE subtotal IS NULL")
            cur.execute("""
                CREATE TABLE IF NOT EXISTS order_event_outbox (
                    event_id UUID PRIMARY KEY,
                    event_type VARCHAR(100) NOT NULL,
                    payload JSONB NOT NULL,
                    dispatchable BOOLEAN NOT NULL DEFAULT FALSE,
                    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
                    published_at TIMESTAMPTZ
                )
            """)
            cur.execute("""
                CREATE INDEX IF NOT EXISTS order_event_outbox_pending_idx
                ON order_event_outbox(created_at)
                WHERE dispatchable=TRUE AND published_at IS NULL
            """)

migrate()


def kafka_producer():
    global _producer
    if _producer is not None:
        return _producer

    with _producer_lock:
        if _producer is not None:
            return _producer

        secret_response = boto3.client("secretsmanager", region_name=AWS_REGION).get_secret_value(
            SecretId=KAFKA_SECRET_ARN
        )
        credentials = json.loads(secret_response["SecretString"])
        _producer = KafkaProducer(
            bootstrap_servers=[server.strip() for server in KAFKA_BOOTSTRAP_SERVERS.split(",") if server.strip()],
            security_protocol="SASL_SSL",
            sasl_mechanism="SCRAM-SHA-512",
            sasl_plain_username=credentials["username"],
            sasl_plain_password=credentials["password"],
            key_serializer=lambda key: key.encode("utf-8"),
            value_serializer=lambda value: json.dumps(value, separators=(",", ":")).encode("utf-8"),
            acks="all",
            retries=10,
            max_in_flight_requests_per_connection=1,
            request_timeout_ms=20000,
        )
        logger.info("Kafka order event producer initialized")
        return _producer


def publish_pending_order_events():
    producer = kafka_producer()
    published = 0

    # Keep the row locks until Kafka acknowledges each record and the published
    # timestamps commit. SKIP LOCKED lets multiple order pods drain the outbox.
    with conn() as db:
        with db.cursor() as cur:
            cur.execute("""
                SELECT event_id::text, payload
                FROM order_event_outbox
                WHERE dispatchable=TRUE AND published_at IS NULL
                ORDER BY created_at
                LIMIT 25
                FOR UPDATE SKIP LOCKED
            """)
            events = cur.fetchall()

            for event in events:
                producer.send(
                    KAFKA_ORDERS_TOPIC,
                    key=event["event_id"],
                    value=event["payload"],
                ).get(timeout=20)
                cur.execute(
                    "UPDATE order_event_outbox SET published_at=NOW() WHERE event_id=%s",
                    (event["event_id"],),
                )
                published += 1

    return published


def order_event_dispatcher():
    while not _dispatcher_stop.is_set():
        try:
            if publish_pending_order_events() == 0:
                _dispatcher_stop.wait(2)
        except Exception:
            logger.exception("Could not publish pending order events; will retry")
            _dispatcher_stop.wait(5)


@app.on_event("startup")
def start_order_event_dispatcher():
    global _dispatcher_thread
    if not KAFKA_ENABLED:
        logger.info("Kafka is not configured; using the notification HTTP fallback")
        return

    _dispatcher_stop.clear()
    _dispatcher_thread = threading.Thread(
        target=order_event_dispatcher,
        name="order-event-dispatcher",
        daemon=True,
    )
    _dispatcher_thread.start()


@app.on_event("shutdown")
def stop_order_event_dispatcher():
    global _producer
    _dispatcher_stop.set()
    if _dispatcher_thread is not None:
        _dispatcher_thread.join(timeout=10)
    if _producer is not None:
        _producer.close(timeout=10)
        _producer = None

class OrderItemIn(BaseModel):
    product_id: int
    quantity: int = Field(gt=0, le=100)

class OrderCreate(BaseModel):
    user_email: EmailStr
    items: list[OrderItemIn]
    promotion_code: str | None = None

class StatusUpdate(BaseModel):
    status: Literal["CREATED", "PAID", "PROCESSING", "SHIPPED", "CANCELLED", "REFUNDED"]

def serialize(row):
    if row is None:
        return None
    out = dict(row)
    if isinstance(out.get("total"), Decimal):
        out["total"] = float(out["total"])
    return out

@app.get("/health")
def health():
    with conn() as db:
        with db.cursor() as cur:
            cur.execute("SELECT 1")
    return {"service": "order-service", "status": "UP", "language": "Python"}

@app.get("/orders")
def list_orders():
    with conn() as db:
        with db.cursor() as cur:
            cur.execute("SELECT * FROM orders ORDER BY id DESC")
            return [serialize(x) for x in cur.fetchall()]

@app.get("/orders/{order_id}")
def get_order(order_id: int):
    with conn() as db:
        with db.cursor() as cur:
            cur.execute("SELECT * FROM orders WHERE id=%s", (order_id,))
            row = cur.fetchone()
    if not row:
        raise HTTPException(404, "order not found")
    return serialize(row)

@app.post("/orders", status_code=201)
async def create_order(payload: OrderCreate):
    if not payload.items:
        raise HTTPException(400, "at least one item is required")

    enriched = []
    reserve_items = []
    subtotal = Decimal("0.00")
    discount_amount = Decimal("0.00")
    promotion_code = payload.promotion_code.strip() if payload.promotion_code else None
    total = Decimal("0.00")

    async with httpx.AsyncClient(timeout=5.0) as client:
        for item in payload.items:
            response = await client.get(f"{CATALOG_URL}/products/{item.product_id}")
            if response.status_code == 404:
                raise HTTPException(400, f"product {item.product_id} not found")
            response.raise_for_status()
            product = response.json()

            if not product.get("active", True):
                raise HTTPException(409, f"product {item.product_id} is inactive")

            unit_price = Decimal(str(product["price"]))
            line_total = unit_price * item.quantity
            subtotal += line_total

            enriched.append({
                "product_id": item.product_id,
                "name": product["name"],
                "quantity": item.quantity,
                "unit_price": float(unit_price),
                "line_total": float(line_total),
            })
            reserve_items.append({"productId": item.product_id, "quantity": item.quantity})

        if promotion_code:
            quote_response = await client.post(
                f"{PROMOTIONS_URL}/promotions/validate",
                json={
                    "code": promotion_code,
                    "customerId": str(payload.user_email),
                    "subtotal": float(subtotal),
                },
            )
            if quote_response.status_code >= 400:
                try:
                    detail = quote_response.json().get("detail", "promotion could not be applied")
                except Exception:
                    detail = "promotion could not be applied"
                raise HTTPException(quote_response.status_code, detail)
            quote = quote_response.json()
            promotion_code = quote["code"]
            discount_amount = Decimal(str(quote["discountAmount"]))
            total = Decimal(str(quote["total"]))
        else:
            total = subtotal

        reserve = await client.post(
            f"{INVENTORY_URL}/inventory/reserve",
            json={"items": reserve_items},
        )
        if reserve.status_code >= 400:
            try:
                detail = reserve.json().get("error", "inventory reservation failed")
            except Exception:
                detail = "inventory reservation failed"
            raise HTTPException(409, detail)

        event_id = str(uuid4()) if KAFKA_ENABLED else None
        try:
            with conn() as db:
                with db.cursor() as cur:
                    cur.execute("""
                        INSERT INTO orders(
                            user_email,status,total,subtotal,discount_amount,promotion_code,items
                        ) VALUES(%s,'CREATED',%s,%s,%s,%s,%s)
                        RETURNING *
                    """, (
                        str(payload.user_email), total, subtotal, discount_amount,
                        promotion_code, Json(enriched),
                    ))
                    row = cur.fetchone()
                    if KAFKA_ENABLED:
                        event_payload = {
                            "event_id": event_id,
                            "event_type": "order.created",
                            "occurred_at": datetime.now(timezone.utc).isoformat(),
                            "data": {
                                "order_id": row["id"],
                                "user_email": str(payload.user_email),
                                "total": float(total),
                            },
                        }
                        cur.execute("""
                            INSERT INTO order_event_outbox(event_id,event_type,payload,dispatchable)
                            VALUES(%s,%s,%s,%s)
                        """, (
                            event_id,
                            "order.created",
                            Json(event_payload),
                            not bool(promotion_code),
                        ))
        except Exception:
            await client.post(
                f"{INVENTORY_URL}/inventory/release",
                json={"items": reserve_items},
            )
            raise

        if promotion_code:
            try:
                redemption = await client.post(
                    f"{PROMOTIONS_URL}/promotions/redeem",
                    json={
                        "code": promotion_code,
                        "customerId": str(payload.user_email),
                        "subtotal": float(subtotal),
                        "orderId": str(row["id"]),
                    },
                )
                if redemption.status_code >= 400:
                    try:
                        detail = redemption.json().get("detail", "promotion redemption failed")
                    except Exception:
                        detail = "promotion redemption failed"
                    raise HTTPException(redemption.status_code, detail)
            except Exception as e:
                detail = e.detail if isinstance(e, HTTPException) else "promotion redemption failed; please try again"
                try:
                    with conn() as db:
                        with db.cursor() as cur:
                            if event_id:
                                cur.execute(
                                    "DELETE FROM order_event_outbox WHERE event_id=%s",
                                    (event_id,),
                                )
                            cur.execute("DELETE FROM orders WHERE id=%s", (row["id"],))
                except Exception:
                    pass
                try:
                    await client.post(
                        f"{INVENTORY_URL}/inventory/release",
                        json={"items": reserve_items},
                    )
                except Exception:
                    pass
                if isinstance(e, HTTPException):
                    raise
                raise HTTPException(502, detail) from e

        if KAFKA_ENABLED:
            if promotion_code:
                with conn() as db:
                    with db.cursor() as cur:
                        cur.execute(
                            "UPDATE order_event_outbox SET dispatchable=TRUE WHERE event_id=%s",
                            (event_id,),
                        )
        else:
            try:
                await client.post(
                    f"{NOTIFICATION_URL}/notifications",
                    json={
                        "recipient": str(payload.user_email),
                        "type": "ORDER",
                        "subject": f"Order #{row['id']} created",
                        "message": f"Your order was created successfully. Total: ${float(total):.2f}",
                    },
                )
            except Exception:
                pass

    return serialize(row)

@app.put("/orders/{order_id}/status")
async def update_status(order_id: int, payload: StatusUpdate):
    with conn() as db:
        with db.cursor() as cur:
            cur.execute("SELECT * FROM orders WHERE id=%s", (order_id,))
            existing = cur.fetchone()

    if not existing:
        raise HTTPException(404, "order not found")

    if payload.status == "CANCELLED" and existing["status"] == "CREATED":
        reserve_items = [
            {"productId": item["product_id"], "quantity": item["quantity"]}
            for item in existing["items"]
        ]
        async with httpx.AsyncClient(timeout=5.0) as client:
            release = await client.post(
                f"{INVENTORY_URL}/inventory/release",
                json={"items": reserve_items},
            )
            if release.status_code >= 400:
                raise HTTPException(409, "could not release reserved inventory")

    with conn() as db:
        with db.cursor() as cur:
            cur.execute("""
                UPDATE orders SET status=%s,updated_at=NOW()
                WHERE id=%s
                RETURNING *
            """, (payload.status, order_id))
            row = cur.fetchone()
    return serialize(row)

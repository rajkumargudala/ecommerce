import os
from decimal import Decimal
from typing import Literal

import httpx
import psycopg2
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

migrate()

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

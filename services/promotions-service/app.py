import os
from contextlib import contextmanager
from datetime import datetime, timezone
from decimal import Decimal, ROUND_HALF_UP
from typing import Iterator

import psycopg2
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel, ConfigDict, Field
from psycopg2.extras import RealDictCursor

DATABASE_URL = os.getenv(
    "DATABASE_URL",
    "postgres://promotions_user:promotions_db_password_123@promotions-db:5432/promotions_db?sslmode=disable",
)

app = FastAPI(title="Promotions Service", version="1.0.0")


@contextmanager
def database() -> Iterator[psycopg2.extensions.connection]:
    connection = psycopg2.connect(DATABASE_URL)
    try:
        with connection:
            yield connection
    finally:
        connection.close()


@app.on_event("startup")
def initialize_database() -> None:
    with database() as connection, connection.cursor() as cursor:
        cursor.execute(
            """
            CREATE TABLE IF NOT EXISTS promotions (
                id BIGSERIAL PRIMARY KEY,
                code VARCHAR(80) NOT NULL UNIQUE,
                description VARCHAR(250) NOT NULL,
                discount_type VARCHAR(16) NOT NULL CHECK (discount_type IN ('PERCENT', 'FIXED')),
                discount_value NUMERIC(10,2) NOT NULL CHECK (discount_value > 0),
                min_subtotal NUMERIC(12,2) NOT NULL DEFAULT 0 CHECK (min_subtotal >= 0),
                starts_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
                ends_at TIMESTAMPTZ,
                max_redemptions INTEGER CHECK (max_redemptions IS NULL OR max_redemptions > 0),
                per_customer_limit INTEGER NOT NULL DEFAULT 1 CHECK (per_customer_limit > 0),
                active BOOLEAN NOT NULL DEFAULT TRUE
            )
            """
        )
        cursor.execute(
            """
            CREATE TABLE IF NOT EXISTS promotion_redemptions (
                id BIGSERIAL PRIMARY KEY,
                promotion_id BIGINT NOT NULL REFERENCES promotions(id),
                customer_id VARCHAR(200) NOT NULL,
                order_id VARCHAR(100) NOT NULL UNIQUE,
                subtotal NUMERIC(12,2) NOT NULL CHECK (subtotal >= 0),
                discount_amount NUMERIC(12,2) NOT NULL CHECK (discount_amount >= 0),
                created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
                UNIQUE (promotion_id, customer_id, order_id)
            )
            """
        )
        cursor.execute(
            "CREATE INDEX IF NOT EXISTS idx_promotion_redemptions_customer ON promotion_redemptions(promotion_id, customer_id)"
        )
        cursor.execute(
            """
            INSERT INTO promotions(code, description, discount_type, discount_value, min_subtotal)
            VALUES ('WELCOME10', '10% off orders of $25 or more', 'PERCENT', 10, 25),
                   ('SAVE5', 'Save $5 on orders of $20 or more', 'FIXED', 5, 20)
            ON CONFLICT (code) DO NOTHING
            """
        )


class PromotionInput(BaseModel):
    model_config = ConfigDict(populate_by_name=True)

    code: str = Field(min_length=1, max_length=80)
    customer_id: str = Field(alias="customerId", min_length=1, max_length=200)
    subtotal: Decimal = Field(ge=0, max_digits=12, decimal_places=2)


class RedemptionRequest(PromotionInput):
    order_id: str = Field(alias="orderId", min_length=1, max_length=100)


def quote_promotion(cursor, payload: PromotionInput, lock: bool = False) -> tuple[dict, Decimal]:
    query = "SELECT * FROM promotions WHERE upper(code)=upper(%s)"
    if lock:
        query += " FOR UPDATE"
    cursor.execute(query, (payload.code.strip(),))
    promotion = cursor.fetchone()
    if promotion is None or not promotion["active"]:
        raise HTTPException(status_code=404, detail="promotion not found or inactive")

    now = datetime.now(timezone.utc)
    if promotion["starts_at"] > now or (promotion["ends_at"] and promotion["ends_at"] <= now):
        raise HTTPException(status_code=409, detail="promotion is outside its valid period")

    subtotal = payload.subtotal.quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)
    if subtotal < promotion["min_subtotal"]:
        raise HTTPException(status_code=422, detail="order subtotal does not meet the promotion minimum")

    cursor.execute(
        "SELECT COUNT(*) AS count FROM promotion_redemptions WHERE promotion_id=%s",
        (promotion["id"],),
    )
    total_redemptions = cursor.fetchone()["count"]
    if promotion["max_redemptions"] is not None and total_redemptions >= promotion["max_redemptions"]:
        raise HTTPException(status_code=409, detail="promotion redemption limit reached")

    customer_id = payload.customer_id.strip()
    cursor.execute(
        "SELECT COUNT(*) AS count FROM promotion_redemptions WHERE promotion_id=%s AND customer_id=%s",
        (promotion["id"], customer_id),
    )
    customer_redemptions = cursor.fetchone()["count"]
    if customer_redemptions >= promotion["per_customer_limit"]:
        raise HTTPException(status_code=409, detail="customer has reached the promotion limit")

    if promotion["discount_type"] == "PERCENT":
        discount = min(subtotal, subtotal * promotion["discount_value"] / Decimal("100"))
    else:
        discount = min(subtotal, promotion["discount_value"])
    discount = discount.quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)
    return promotion, discount


def serialize_promotion(row: dict) -> dict:
    return {
        "code": row["code"],
        "description": row["description"],
        "discountType": row["discount_type"],
        "discountValue": row["discount_value"],
        "minSubtotal": row["min_subtotal"],
        "startsAt": row["starts_at"],
        "endsAt": row["ends_at"],
        "maxRedemptions": row["max_redemptions"],
        "perCustomerLimit": row["per_customer_limit"],
    }


@app.get("/health")
def health() -> dict:
    with database() as connection, connection.cursor() as cursor:
        cursor.execute("SELECT 1")
    return {"service": "promotions-service", "status": "UP", "language": "Python"}


@app.get("/promotions")
def list_promotions() -> list[dict]:
    with database() as connection, connection.cursor(cursor_factory=RealDictCursor) as cursor:
        cursor.execute(
            "SELECT * FROM promotions WHERE active=TRUE ORDER BY code"
        )
        rows = cursor.fetchall()
    return [serialize_promotion(row) for row in rows]


@app.post("/promotions/validate")
def validate_promotion(payload: PromotionInput) -> dict:
    with database() as connection, connection.cursor(cursor_factory=RealDictCursor) as cursor:
        promotion, discount = quote_promotion(cursor, payload)
    subtotal = payload.subtotal.quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)
    return {
        "code": promotion["code"],
        "subtotal": subtotal,
        "discountAmount": discount,
        "total": subtotal - discount,
    }


@app.post("/promotions/redeem", status_code=201)
def redeem_promotion(payload: RedemptionRequest) -> dict:
    try:
        with database() as connection, connection.cursor(cursor_factory=RealDictCursor) as cursor:
            promotion, discount = quote_promotion(cursor, payload, lock=True)
            subtotal = payload.subtotal.quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)
            cursor.execute(
                """
                INSERT INTO promotion_redemptions(
                    promotion_id, customer_id, order_id, subtotal, discount_amount
                ) VALUES (%s, %s, %s, %s, %s)
                RETURNING id, created_at
                """,
                (
                    promotion["id"],
                    payload.customer_id.strip(),
                    payload.order_id.strip(),
                    subtotal,
                    discount,
                ),
            )
            redemption = cursor.fetchone()
    except psycopg2.errors.UniqueViolation as error:
        raise HTTPException(status_code=409, detail="order already has a promotion redemption") from error

    return {
        "id": redemption["id"],
        "orderId": payload.order_id,
        "customerId": payload.customer_id,
        "code": promotion["code"],
        "subtotal": subtotal,
        "discountAmount": discount,
        "total": subtotal - discount,
        "createdAt": redemption["created_at"],
    }

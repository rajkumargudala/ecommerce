import os
import secrets
from contextlib import contextmanager
from enum import Enum
from typing import Iterator

import psycopg2
from fastapi import FastAPI, HTTPException, Query
from pydantic import BaseModel, ConfigDict, Field
from psycopg2.extras import RealDictCursor

DATABASE_URL = os.getenv(
    "DATABASE_URL",
    "postgres://shipping_user:shipping_db_password_123@shipping-db:5432/shipping_db?sslmode=disable",
)

app = FastAPI(title="Shipping Service", version="1.0.0")


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
            CREATE TABLE IF NOT EXISTS shipments (
                id BIGSERIAL PRIMARY KEY,
                order_id BIGINT NOT NULL UNIQUE CHECK (order_id > 0),
                recipient_name VARCHAR(200) NOT NULL,
                address_line1 VARCHAR(250) NOT NULL,
                address_line2 VARCHAR(250) NOT NULL DEFAULT '',
                city VARCHAR(120) NOT NULL,
                region VARCHAR(120) NOT NULL DEFAULT '',
                postal_code VARCHAR(40) NOT NULL,
                country VARCHAR(100) NOT NULL,
                carrier VARCHAR(100) NOT NULL DEFAULT 'STANDARD',
                tracking_number VARCHAR(80) NOT NULL UNIQUE,
                status VARCHAR(40) NOT NULL DEFAULT 'LABEL_CREATED',
                created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
                updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
            )
            """
        )


class ShipmentStatus(str, Enum):
    LABEL_CREATED = "LABEL_CREATED"
    IN_TRANSIT = "IN_TRANSIT"
    OUT_FOR_DELIVERY = "OUT_FOR_DELIVERY"
    DELIVERED = "DELIVERED"
    RETURNED = "RETURNED"
    CANCELLED = "CANCELLED"


class ShipmentRequest(BaseModel):
    model_config = ConfigDict(populate_by_name=True)

    order_id: int = Field(alias="orderId", gt=0)
    recipient_name: str = Field(alias="recipientName", min_length=1, max_length=200)
    address_line1: str = Field(alias="addressLine1", min_length=1, max_length=250)
    address_line2: str = Field(default="", alias="addressLine2", max_length=250)
    city: str = Field(min_length=1, max_length=120)
    region: str = Field(default="", max_length=120)
    postal_code: str = Field(alias="postalCode", min_length=1, max_length=40)
    country: str = Field(min_length=1, max_length=100)
    carrier: str = Field(default="STANDARD", min_length=1, max_length=100)


class StatusRequest(BaseModel):
    status: ShipmentStatus


def serialize(row: dict) -> dict:
    return {
        "id": row["id"],
        "orderId": row["order_id"],
        "recipientName": row["recipient_name"],
        "addressLine1": row["address_line1"],
        "addressLine2": row["address_line2"],
        "city": row["city"],
        "region": row["region"],
        "postalCode": row["postal_code"],
        "country": row["country"],
        "carrier": row["carrier"],
        "trackingNumber": row["tracking_number"],
        "status": row["status"],
        "createdAt": row["created_at"],
        "updatedAt": row["updated_at"],
    }


@app.get("/health")
def health() -> dict:
    with database() as connection, connection.cursor() as cursor:
        cursor.execute("SELECT 1")
    return {"service": "shipping-service", "status": "UP", "language": "Python"}


@app.post("/shipments", status_code=201)
def create_shipment(payload: ShipmentRequest) -> dict:
    try:
        with database() as connection, connection.cursor(cursor_factory=RealDictCursor) as cursor:
            cursor.execute(
                """
                INSERT INTO shipments(
                    order_id, recipient_name, address_line1, address_line2, city,
                    region, postal_code, country, carrier, tracking_number
                ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
                RETURNING *
                """,
                (
                    payload.order_id,
                    payload.recipient_name.strip(),
                    payload.address_line1.strip(),
                    payload.address_line2.strip(),
                    payload.city.strip(),
                    payload.region.strip(),
                    payload.postal_code.strip(),
                    payload.country.strip(),
                    payload.carrier.strip(),
                    f"SHIP-{secrets.token_hex(6).upper()}",
                ),
            )
            row = cursor.fetchone()
    except psycopg2.errors.UniqueViolation as error:
        raise HTTPException(status_code=409, detail="shipment already exists for this order") from error
    return serialize(row)


@app.get("/shipments")
def list_shipments(order_id: int | None = Query(default=None, alias="orderId", gt=0)) -> list[dict]:
    with database() as connection, connection.cursor(cursor_factory=RealDictCursor) as cursor:
        if order_id is None:
            cursor.execute("SELECT * FROM shipments ORDER BY id DESC")
        else:
            cursor.execute("SELECT * FROM shipments WHERE order_id=%s ORDER BY id DESC", (order_id,))
        rows = cursor.fetchall()
    return [serialize(row) for row in rows]


@app.get("/shipments/{shipment_id}")
def get_shipment(shipment_id: int) -> dict:
    with database() as connection, connection.cursor(cursor_factory=RealDictCursor) as cursor:
        cursor.execute("SELECT * FROM shipments WHERE id=%s", (shipment_id,))
        row = cursor.fetchone()
    if row is None:
        raise HTTPException(status_code=404, detail="shipment not found")
    return serialize(row)


@app.patch("/shipments/{shipment_id}/status")
def update_status(shipment_id: int, payload: StatusRequest) -> dict:
    with database() as connection, connection.cursor(cursor_factory=RealDictCursor) as cursor:
        cursor.execute(
            "UPDATE shipments SET status=%s, updated_at=NOW() WHERE id=%s RETURNING *",
            (payload.status.value, shipment_id),
        )
        row = cursor.fetchone()
    if row is None:
        raise HTTPException(status_code=404, detail="shipment not found")
    return serialize(row)

import os
from contextlib import contextmanager
from typing import Iterator

import psycopg2
from fastapi import FastAPI, HTTPException, Response
from pydantic import BaseModel, ConfigDict, Field
from psycopg2.extras import RealDictCursor

DATABASE_URL = os.getenv(
    "DATABASE_URL",
    "postgres://cart_user:cart_db_password_123@cart-db:5432/cart_db?sslmode=disable",
)

app = FastAPI(title="Cart Service", version="1.0.0")


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
            CREATE TABLE IF NOT EXISTS cart_items (
                customer_id VARCHAR(200) NOT NULL,
                product_id BIGINT NOT NULL CHECK (product_id > 0),
                quantity INTEGER NOT NULL CHECK (quantity > 0),
                updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
                PRIMARY KEY (customer_id, product_id)
            )
            """
        )


class CartItemRequest(BaseModel):
    model_config = ConfigDict(populate_by_name=True)

    product_id: int = Field(alias="productId", gt=0)
    quantity: int = Field(gt=0, le=1000)


def serialize_item(row: dict) -> dict:
    return {
        "productId": row["product_id"],
        "quantity": row["quantity"],
        "updatedAt": row["updated_at"],
    }


@app.get("/health")
def health() -> dict:
    with database() as connection, connection.cursor() as cursor:
        cursor.execute("SELECT 1")
    return {"service": "cart-service", "status": "UP", "language": "Python"}


@app.get("/carts/{customer_id}")
def get_cart(customer_id: str) -> dict:
    with database() as connection, connection.cursor(cursor_factory=RealDictCursor) as cursor:
        cursor.execute(
            "SELECT product_id, quantity, updated_at FROM cart_items WHERE customer_id=%s ORDER BY product_id",
            (customer_id,),
        )
        rows = cursor.fetchall()
    return {"customerId": customer_id, "items": [serialize_item(row) for row in rows]}


@app.put("/carts/{customer_id}/items")
def set_cart_item(customer_id: str, payload: CartItemRequest) -> dict:
    with database() as connection, connection.cursor(cursor_factory=RealDictCursor) as cursor:
        cursor.execute(
            """
            INSERT INTO cart_items(customer_id, product_id, quantity)
            VALUES (%s, %s, %s)
            ON CONFLICT (customer_id, product_id)
            DO UPDATE SET quantity=EXCLUDED.quantity, updated_at=NOW()
            RETURNING product_id, quantity, updated_at
            """,
            (customer_id, payload.product_id, payload.quantity),
        )
        row = cursor.fetchone()
    return {"customerId": customer_id, **serialize_item(row)}


@app.delete("/carts/{customer_id}/items/{product_id}", status_code=204)
def remove_cart_item(customer_id: str, product_id: int) -> Response:
    with database() as connection, connection.cursor() as cursor:
        cursor.execute(
            "DELETE FROM cart_items WHERE customer_id=%s AND product_id=%s",
            (customer_id, product_id),
        )
        if cursor.rowcount == 0:
            raise HTTPException(status_code=404, detail="cart item not found")
    return Response(status_code=204)


@app.delete("/carts/{customer_id}", status_code=204)
def clear_cart(customer_id: str) -> Response:
    with database() as connection, connection.cursor() as cursor:
        cursor.execute("DELETE FROM cart_items WHERE customer_id=%s", (customer_id,))
    return Response(status_code=204)

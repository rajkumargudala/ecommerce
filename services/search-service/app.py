import os
from contextlib import contextmanager
from decimal import Decimal
from typing import Iterator

import psycopg2
from fastapi import FastAPI, HTTPException, Query
from pydantic import BaseModel, ConfigDict, Field
from psycopg2.extras import RealDictCursor

DATABASE_URL = os.getenv(
    "DATABASE_URL",
    "postgres://search_user:search_db_password_123@search-db:5432/search_db?sslmode=disable",
)

app = FastAPI(title="Search Service", version="1.0.0")


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
            CREATE TABLE IF NOT EXISTS search_documents (
                product_id BIGINT PRIMARY KEY CHECK (product_id > 0),
                name VARCHAR(160) NOT NULL,
                category VARCHAR(100) NOT NULL,
                description TEXT NOT NULL DEFAULT '',
                price NUMERIC(12,2) NOT NULL CHECK (price >= 0),
                image TEXT NOT NULL DEFAULT '',
                active BOOLEAN NOT NULL DEFAULT TRUE,
                updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
            )
            """
        )
        cursor.execute(
            """
            CREATE INDEX IF NOT EXISTS idx_search_documents_vector
            ON search_documents USING GIN (
                to_tsvector('english', name || ' ' || category || ' ' || description)
            )
            """
        )


class ProductIndexRequest(BaseModel):
    model_config = ConfigDict(populate_by_name=True)

    product_id: int = Field(alias="productId", gt=0)
    name: str = Field(min_length=1, max_length=160)
    category: str = Field(min_length=1, max_length=100)
    description: str = Field(default="", max_length=10000)
    price: Decimal = Field(ge=0, max_digits=12, decimal_places=2)
    image: str = ""
    active: bool = True


def serialize(row: dict) -> dict:
    return {
        "productId": row["product_id"],
        "name": row["name"],
        "category": row["category"],
        "description": row["description"],
        "price": row["price"],
        "image": row["image"],
        "active": row["active"],
    }


@app.get("/health")
def health() -> dict:
    with database() as connection, connection.cursor() as cursor:
        cursor.execute("SELECT 1")
    return {"service": "search-service", "status": "UP", "language": "Python"}


@app.get("/search")
def search_products(
    q: str = Query(default="", max_length=200),
    category: str | None = Query(default=None, max_length=100),
    limit: int = Query(default=20, ge=1, le=100),
) -> list[dict]:
    query = q.strip()
    with database() as connection, connection.cursor(cursor_factory=RealDictCursor) as cursor:
        cursor.execute(
            """
            SELECT product_id, name, category, description, price, image, active,
                   CASE WHEN %s = '' THEN 0::real ELSE ts_rank(
                       to_tsvector('english', name || ' ' || category || ' ' || description),
                       plainto_tsquery('english', %s)
                   ) END AS rank
            FROM search_documents
            WHERE active=TRUE
              AND (%s = '' OR to_tsvector('english', name || ' ' || category || ' ' || description)
                   @@ plainto_tsquery('english', %s))
              AND (%s IS NULL OR lower(category)=lower(%s))
            ORDER BY rank DESC, name
            LIMIT %s
            """,
            (query, query, query, query, category, category, limit),
        )
        rows = cursor.fetchall()
    return [{**serialize(row), "rank": row["rank"]} for row in rows]


@app.put("/search/index")
def index_product(payload: ProductIndexRequest) -> dict:
    with database() as connection, connection.cursor(cursor_factory=RealDictCursor) as cursor:
        cursor.execute(
            """
            INSERT INTO search_documents(product_id, name, category, description, price, image, active)
            VALUES (%s, %s, %s, %s, %s, %s, %s)
            ON CONFLICT (product_id)
            DO UPDATE SET name=EXCLUDED.name, category=EXCLUDED.category,
                          description=EXCLUDED.description, price=EXCLUDED.price,
                          image=EXCLUDED.image, active=EXCLUDED.active, updated_at=NOW()
            RETURNING product_id, name, category, description, price, image, active
            """,
            (
                payload.product_id,
                payload.name.strip(),
                payload.category.strip(),
                payload.description.strip(),
                payload.price,
                payload.image,
                payload.active,
            ),
        )
        row = cursor.fetchone()
    return serialize(row)


@app.delete("/search/index/{product_id}", status_code=204)
def remove_product(product_id: int) -> None:
    with database() as connection, connection.cursor() as cursor:
        cursor.execute("DELETE FROM search_documents WHERE product_id=%s", (product_id,))
        if cursor.rowcount == 0:
            raise HTTPException(status_code=404, detail="indexed product not found")

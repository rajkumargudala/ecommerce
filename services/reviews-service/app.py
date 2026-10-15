import os
from contextlib import contextmanager
from typing import Iterator

import psycopg2
from fastapi import FastAPI, HTTPException, Query
from pydantic import BaseModel, ConfigDict, Field
from psycopg2.extras import RealDictCursor

DATABASE_URL = os.getenv(
    "DATABASE_URL",
    "postgres://reviews_user:reviews_db_password_123@reviews-db:5432/reviews_db?sslmode=disable",
)

app = FastAPI(title="Reviews Service", version="1.0.0")


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
            CREATE TABLE IF NOT EXISTS product_reviews (
                id BIGSERIAL PRIMARY KEY,
                product_id BIGINT NOT NULL CHECK (product_id > 0),
                customer_id VARCHAR(200) NOT NULL,
                rating SMALLINT NOT NULL CHECK (rating BETWEEN 1 AND 5),
                title VARCHAR(200) NOT NULL DEFAULT '',
                body TEXT NOT NULL DEFAULT '',
                created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
                updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
                UNIQUE (product_id, customer_id)
            )
            """
        )
        cursor.execute(
            "CREATE INDEX IF NOT EXISTS idx_product_reviews_product ON product_reviews(product_id, created_at DESC)"
        )


class ReviewRequest(BaseModel):
    model_config = ConfigDict(populate_by_name=True)

    product_id: int = Field(alias="productId", gt=0)
    customer_id: str = Field(alias="customerId", min_length=1, max_length=200)
    rating: int = Field(ge=1, le=5)
    title: str = Field(default="", max_length=200)
    body: str = Field(default="", max_length=5000)


def serialize(row: dict) -> dict:
    return {
        "id": row["id"],
        "productId": row["product_id"],
        "customerId": row["customer_id"],
        "rating": row["rating"],
        "title": row["title"],
        "body": row["body"],
        "createdAt": row["created_at"],
        "updatedAt": row["updated_at"],
    }


@app.get("/health")
def health() -> dict:
    with database() as connection, connection.cursor() as cursor:
        cursor.execute("SELECT 1")
    return {"service": "reviews-service", "status": "UP", "language": "Python"}


@app.post("/reviews", status_code=201)
def create_or_update_review(payload: ReviewRequest) -> dict:
    with database() as connection, connection.cursor(cursor_factory=RealDictCursor) as cursor:
        cursor.execute(
            """
            INSERT INTO product_reviews(product_id, customer_id, rating, title, body)
            VALUES (%s, %s, %s, %s, %s)
            ON CONFLICT (product_id, customer_id)
            DO UPDATE SET rating=EXCLUDED.rating, title=EXCLUDED.title,
                          body=EXCLUDED.body, updated_at=NOW()
            RETURNING *
            """,
            (
                payload.product_id,
                payload.customer_id.strip(),
                payload.rating,
                payload.title.strip(),
                payload.body.strip(),
            ),
        )
        row = cursor.fetchone()
    return serialize(row)


@app.get("/reviews")
def list_reviews(
    product_id: int = Query(alias="productId", gt=0),
    limit: int = Query(default=50, ge=1, le=100),
    offset: int = Query(default=0, ge=0),
) -> list[dict]:
    with database() as connection, connection.cursor(cursor_factory=RealDictCursor) as cursor:
        cursor.execute(
            "SELECT * FROM product_reviews WHERE product_id=%s ORDER BY created_at DESC LIMIT %s OFFSET %s",
            (product_id, limit, offset),
        )
        rows = cursor.fetchall()
    return [serialize(row) for row in rows]


@app.get("/reviews/summary")
def review_summary(product_id: int = Query(alias="productId", gt=0)) -> dict:
    with database() as connection, connection.cursor(cursor_factory=RealDictCursor) as cursor:
        cursor.execute(
            """
            SELECT COUNT(*) AS count, COALESCE(AVG(rating), 0)::NUMERIC(4,2) AS average,
                   COUNT(*) FILTER (WHERE rating=1) AS one_star,
                   COUNT(*) FILTER (WHERE rating=2) AS two_star,
                   COUNT(*) FILTER (WHERE rating=3) AS three_star,
                   COUNT(*) FILTER (WHERE rating=4) AS four_star,
                   COUNT(*) FILTER (WHERE rating=5) AS five_star
            FROM product_reviews WHERE product_id=%s
            """,
            (product_id,),
        )
        row = cursor.fetchone()
    return {
        "productId": product_id,
        "count": row["count"],
        "averageRating": row["average"],
        "ratingBreakdown": {
            "1": row["one_star"],
            "2": row["two_star"],
            "3": row["three_star"],
            "4": row["four_star"],
            "5": row["five_star"],
        },
    }


@app.delete("/reviews/{review_id}", status_code=204)
def delete_review(review_id: int) -> None:
    with database() as connection, connection.cursor() as cursor:
        cursor.execute("DELETE FROM product_reviews WHERE id=%s", (review_id,))
        if cursor.rowcount == 0:
            raise HTTPException(status_code=404, detail="review not found")

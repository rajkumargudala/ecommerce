import json
import logging
import os
from decimal import Decimal

import boto3
import psycopg2
from kafka import KafkaConsumer

logging.basicConfig(
    level=os.getenv("LOG_LEVEL", "INFO"),
    format="%(asctime)s %(levelname)s %(message)s",
)
logger = logging.getLogger("kafka-notification-worker")

AWS_REGION = os.getenv("AWS_REGION", os.getenv("AWS_DEFAULT_REGION", "us-east-1"))
KAFKA_BOOTSTRAP_SERVERS = os.environ["KAFKA_BOOTSTRAP_SERVERS"]
KAFKA_SECRET_ARN = os.environ["KAFKA_SECRET_ARN"]
KAFKA_ORDERS_TOPIC = os.getenv("KAFKA_ORDERS_TOPIC", "orders.created")
KAFKA_GROUP_ID = os.getenv("KAFKA_GROUP_ID", "notification-service")
NOTIFICATION_DB_URL = os.environ["NOTIFICATION_DB_URL"]


def kafka_credentials() -> dict[str, str]:
    response = boto3.client("secretsmanager", region_name=AWS_REGION).get_secret_value(
        SecretId=KAFKA_SECRET_ARN
    )
    return json.loads(response["SecretString"])


def initialize_database() -> None:
    connection = psycopg2.connect(NOTIFICATION_DB_URL)
    try:
        with connection, connection.cursor() as cursor:
            cursor.execute("ALTER TABLE notifications ADD COLUMN IF NOT EXISTS event_id UUID")
            cursor.execute("""
                CREATE UNIQUE INDEX IF NOT EXISTS notifications_event_id_uidx
                ON notifications(event_id)
            """)
    finally:
        connection.close()


def store_order_notification(event: dict) -> None:
    data = event["data"]
    order_id = data["order_id"]
    total = Decimal(str(data["total"]))
    connection = psycopg2.connect(NOTIFICATION_DB_URL)
    try:
        with connection, connection.cursor() as cursor:
            cursor.execute("""
                INSERT INTO notifications(event_id,recipient,type,subject,message)
                VALUES(%s,%s,%s,%s,%s)
                ON CONFLICT (event_id) DO NOTHING
            """, (
                event["event_id"],
                data["user_email"],
                "ORDER",
                f"Order #{order_id} created",
                f"Your order was created successfully. Total: ${total:.2f}",
            ))
    finally:
        connection.close()


def handle_event(event: dict) -> None:
    if event.get("event_type") == "order.created":
        store_order_notification(event)
    else:
        logger.info("Skipping unsupported event type %s", event.get("event_type"))


def main() -> None:
    initialize_database()
    credentials = kafka_credentials()
    consumer = KafkaConsumer(
        KAFKA_ORDERS_TOPIC,
        bootstrap_servers=[server.strip() for server in KAFKA_BOOTSTRAP_SERVERS.split(",") if server.strip()],
        group_id=KAFKA_GROUP_ID,
        security_protocol="SASL_SSL",
        sasl_mechanism="SCRAM-SHA-512",
        sasl_plain_username=credentials["username"],
        sasl_plain_password=credentials["password"],
        auto_offset_reset="earliest",
        enable_auto_commit=False,
        value_deserializer=lambda value: json.loads(value.decode("utf-8")),
    )

    logger.info("Consuming order events from topic %s", KAFKA_ORDERS_TOPIC)
    try:
        for message in consumer:
            handle_event(message.value)
            consumer.commit()
    finally:
        consumer.close()


if __name__ == "__main__":
    main()

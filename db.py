import os
from pathlib import Path

from catalog import CATALOG

try:
    from dotenv import load_dotenv
except ModuleNotFoundError:
    load_dotenv = None

try:
    import psycopg2
except ModuleNotFoundError:
    psycopg2 = None

if load_dotenv is not None:
    env_path = Path(__file__).resolve().parent / ".env"
    load_dotenv(dotenv_path=env_path, override=True)


def get_connection():
    if psycopg2 is None:
        raise RuntimeError("psycopg2 is not installed")
    database_url = os.getenv("DATABASE_URL")
    if not database_url:
        raise RuntimeError("DATABASE_URL is not set")
    return psycopg2.connect(database_url)


def initialize_database() -> None:
    with get_connection() as conn:
        with conn.cursor() as cur:
            cur.execute(
                """
                CREATE TABLE IF NOT EXISTS products (
                    product_id TEXT PRIMARY KEY,
                    name TEXT,
                    category TEXT,
                    availability TEXT
                )
                """
            )
            cur.execute(
                """
                CREATE TABLE IF NOT EXISTS orders (
                    order_id TEXT PRIMARY KEY,
                    product_name TEXT,
                    category TEXT,
                    delay_days INTEGER,
                    region TEXT
                )
                """
            )
            cur.execute(
                """
                CREATE TABLE IF NOT EXISTS customers (
                    customer_id TEXT PRIMARY KEY,
                    history TEXT
                )
                """
            )
            cur.executemany(
                """
                INSERT INTO products (product_id, name, category, availability)
                VALUES (%s, %s, %s, %s)
                ON CONFLICT (product_id) DO NOTHING
                """,
                [
                    (
                        product["product_id"],
                        product["name"],
                        product["category"],
                        product["availability"],
                    )
                    for product in CATALOG
                ],
            )

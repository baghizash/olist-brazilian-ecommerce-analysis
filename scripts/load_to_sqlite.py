"""Load 8 CSV dataset Olist Brazilian E Commerce ke SQLite.

Jalankan dari folder ~/workspace/olist-ecommerce :
    ~/workspace/mienv/bin/python scripts/load_to_sqlite.py

Output : data/olist.db (file ini diabaikan git lewat .gitignore)
"""
import sqlite3
from pathlib import Path

import pandas as pd

BASE = Path(__file__).resolve().parent.parent
RAW = BASE / "data" / "raw"
DB_PATH = BASE / "data" / "olist.db"

TABLES = {
    "olist_customers_dataset.csv": "customers",
    "olist_geolocation_dataset.csv": "geolocation",
    "olist_order_items_dataset.csv": "order_items",
    "olist_order_payments_dataset.csv": "payments",
    "olist_order_reviews_dataset.csv": "reviews",
    "olist_orders_dataset.csv": "orders",
    "olist_products_dataset.csv": "products",
    "olist_sellers_dataset.csv": "sellers",
}

EXPECTED_ROWS = {
    "customers": 99441,
    "geolocation": 1000163,
    "order_items": 112650,
    "payments": 103886,
    "reviews": 99224,
    "orders": 99441,
    "products": 32951,
    "sellers": 3095,
}


def main():
    if DB_PATH.exists():
        DB_PATH.unlink()
        print(f"Menghapus db lama : {DB_PATH}")

    con = sqlite3.connect(DB_PATH)

    for csv_name, table in TABLES.items():
        path = RAW / csv_name
        print(f"Load {csv_name} ...")
        df = pd.read_csv(path)
        df.to_sql(table, con, index=False)
        n = con.execute(f"SELECT COUNT(*) FROM {table}").fetchone()[0]
        status = "OK" if n == EXPECTED_ROWS[table] else "MISMATCH"
        print(f"  tabel {table} : {n} baris (ekspektasi {EXPECTED_ROWS[table]}) [{status}]")
        assert n == EXPECTED_ROWS[table], f"Row count {table} tidak sesuai"

    print("Membuat index untuk join ...")
    con.executescript(
        """
        CREATE INDEX idx_orders_customer ON orders(customer_id);
        CREATE INDEX idx_orders_status ON orders(order_status);
        CREATE INDEX idx_items_order ON order_items(order_id);
        CREATE INDEX idx_items_product ON order_items(product_id);
        CREATE INDEX idx_items_seller ON order_items(seller_id);
        CREATE INDEX idx_payments_order ON payments(order_id);
        CREATE INDEX idx_reviews_order ON reviews(order_id);
        CREATE INDEX idx_products_category ON products(product_category_name);
        """
    )
    con.commit()

    print("Verifikasi akhir row count tiap tabel :")
    for table, expected in EXPECTED_ROWS.items():
        n = con.execute(f"SELECT COUNT(*) FROM {table}").fetchone()[0]
        print(f"  {table:12s} : {n:>8,}  [{'OK' if n == expected else 'MISMATCH'}]")

    con.close()
    print(f"Selesai. Database tersimpan di {DB_PATH}")


if __name__ == "__main__":
    main()

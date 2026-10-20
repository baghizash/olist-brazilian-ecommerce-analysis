# Bangun CSV kit Power BI Olist dari data mentah (join di pandas).
# Jalankan: ~/workspace/mienv/bin/python powerbi/build_kit_csv.py
# Grain: fact_pesanan = 1 baris per order; fact_item_pesanan = 1 baris per order-item.
# Kedua fakta DIPISAH per grain; tidak ada baris agregat di fakta mana pun.
import pandas as pd
import numpy as np
from pathlib import Path

BASE = Path(__file__).resolve().parent.parent / "data" / "raw"
OUT = Path(__file__).resolve().parent

orders = pd.read_csv(BASE / "olist_orders_dataset.csv",
                     parse_dates=["order_purchase_timestamp", "order_delivered_customer_date",
                                  "order_estimated_delivery_date"])
items = pd.read_csv(BASE / "olist_order_items_dataset.csv")
pay = pd.read_csv(BASE / "olist_order_payments_dataset.csv")
rev = pd.read_csv(BASE / "olist_order_reviews_dataset.csv",
                  parse_dates=["review_creation_date"])
cust = pd.read_csv(BASE / "olist_customers_dataset.csv")
prod = pd.read_csv(BASE / "olist_products_dataset.csv")
trans = pd.read_csv(BASE / "category_translation.csv")

# --- Agregasi per order ---
pay_o = pay.groupby("order_id").agg(total_pembayaran=("payment_value", "sum")).reset_index()
items_o = items.groupby("order_id").agg(
    jumlah_item=("order_item_id", "count"),
    total_harga_produk=("price", "sum"),
    total_ongkir=("freight_value", "sum")).reset_index()
# Skor review: 551 order punya lebih dari 1 review (547 punya 2, 4 punya 3);
# untuk grain 1 baris per order dipakai review PERTAMA menurut review_creation_date.
rev_first = (rev.sort_values("review_creation_date")
               .drop_duplicates("order_id", keep="first")[["order_id", "review_score"]]
               .rename(columns={"review_score": "skor_review"}))

o = orders.merge(cust[["customer_id", "customer_unique_id", "customer_state"]],
                 on="customer_id", how="left")
o = o.merge(pay_o, on="order_id", how="left")
o = o.merge(items_o, on="order_id", how="left")
o = o.merge(rev_first, on="order_id", how="left")

fact = pd.DataFrame({
    "order_id": o["order_id"],
    "tanggal_beli": o["order_purchase_timestamp"].dt.date,
    "customer_unique_id": o["customer_unique_id"],
    "customer_state": o["customer_state"],
    "order_status": o["order_status"],
    "total_pembayaran": o["total_pembayaran"].round(2),
    "total_harga_produk": o["total_harga_produk"].round(2),
    "total_ongkir": o["total_ongkir"].round(2),
    "jumlah_item": o["jumlah_item"],
    # hari_pengiriman: selisih tanggal terima aktual dan tanggal beli, dalam hari desimal (2 desimal).
    "hari_pengiriman": ((o["order_delivered_customer_date"] - o["order_purchase_timestamp"])
                        .dt.total_seconds() / 86400).round(2),
    # estimasi_hari: selisih estimasi terima dan tanggal beli, dalam hari desimal (2 desimal).
    "estimasi_hari": ((o["order_estimated_delivery_date"] - o["order_purchase_timestamp"])
                      .dt.total_seconds() / 86400).round(2),
    # terlambat_flag: 1 bila terima aktual melewati estimasi, 0 bila tepat waktu, kosong bila belum diterima.
    "terlambat_flag": np.where(
        o["order_delivered_customer_date"].isna(), np.nan,
        (o["order_delivered_customer_date"] > o["order_estimated_delivery_date"]).astype(int)),
    "skor_review": o["skor_review"],
})
# Tipe bilangan bulat nullable supaya CSV tidak menampilkan ,0 pada kolom hitung/flag/skor
for col in ["jumlah_item", "terlambat_flag", "skor_review"]:
    fact[col] = fact[col].astype("Int64")
fact.to_csv(OUT / "fact_pesanan.csv", index=False)

# --- Fact item (1 baris per order-item) ---
prod2 = prod.merge(trans, on="product_category_name", how="left")
prod2["kategori"] = prod2["category_en"].fillna("tidak_diketahui")
fi = items.merge(o[["order_id", "order_purchase_timestamp", "customer_state", "order_status"]],
                 on="order_id", how="left")
fi = fi.merge(prod2[["product_id", "kategori"]], on="product_id", how="left")
fact_item = pd.DataFrame({
    "order_id": fi["order_id"],
    "product_id": fi["product_id"],
    "kategori": fi["kategori"].fillna("tidak_diketahui"),
    "price": fi["price"].round(2),
    "freight_value": fi["freight_value"].round(2),
    "tanggal_beli": fi["order_purchase_timestamp"].dt.date,
    "customer_state": fi["customer_state"],
    "order_status": fi["order_status"],
})
fact_item = fact_item.sort_values(["order_id"]).reset_index(drop=True)
fact_item.to_csv(OUT / "fact_item_pesanan.csv", index=False)

# --- Dimensi ---
tgl = pd.date_range(fact["tanggal_beli"].min(), fact["tanggal_beli"].max(), freq="D")
nama_bulan = {1:"Januari",2:"Februari",3:"Maret",4:"April",5:"Mei",6:"Juni",7:"Juli",
              8:"Agustus",9:"September",10:"Oktober",11:"November",12:"Desember"}
nama_hari = {0:"Senin",1:"Selasa",2:"Rabu",3:"Kamis",4:"Jumat",5:"Sabtu",6:"Minggu"}
dim_tanggal = pd.DataFrame({
    "tanggal": tgl.date,
    "tahun": tgl.year,
    "kuartal": tgl.quarter,
    "bulan": tgl.month,
    "nama_bulan": [nama_bulan[m] for m in tgl.month],
    "tahun_bulan": tgl.strftime("%Y-%m"),
    "nama_hari": [nama_hari[d] for d in tgl.dayofweek],
})
dim_tanggal.to_csv(OUT / "dim_tanggal.csv", index=False)

dim_kategori = (prod2[["kategori", "product_category_name"]]
                .drop_duplicates().sort_values("kategori")
                .rename(columns={"product_category_name": "kategori_portugis"}))
# pastikan kategori yang muncul di fact_item semuanya ada di dimensi
extra = set(fact_item["kategori"]) - set(dim_kategori["kategori"])
for k in sorted(extra):
    dim_kategori = pd.concat([dim_kategori, pd.DataFrame(
        [{"kategori": k, "kategori_portugis": ""}])], ignore_index=True)
dim_kategori = dim_kategori.sort_values("kategori").reset_index(drop=True)
dim_kategori.to_csv(OUT / "dim_kategori.csv", index=False)

pd.DataFrame({"order_status": sorted(fact["order_status"].dropna().unique())}) \
    .to_csv(OUT / "dim_status.csv", index=False)
pd.DataFrame({"customer_state": sorted(fact["customer_state"].dropna().unique())}) \
    .to_csv(OUT / "dim_negara_bagian.csv", index=False)

print("fact_pesanan", len(fact), "| fact_item_pesanan", len(fact_item),
      "| dim_tanggal", len(dim_tanggal), "| dim_kategori", len(dim_kategori))

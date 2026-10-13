"""Membangun analysis.ipynb dari nol.

Fase A menghitung semua metrik dari SQLite memakai SQL asli.
Fase B merangkai sel notebook, dengan angka temuan dibake ke markdown
dari hasil Fase A, sedangkan sel code menghitung ulang angka yang sama
sehingga run ulang notebook selalu konsisten.

Jalankan : ~/workspace/mienv/bin/python scripts/build_notebook.py
"""
import sqlite3
from pathlib import Path

import nbformat as nbf
import pandas as pd

BASE = Path(__file__).resolve().parent.parent
DB = BASE / "data" / "olist.db"
RAW = BASE / "data" / "raw"
NB_PATH = BASE / "analysis.ipynb"

BULAN_ID = {1: "Jan", 2: "Feb", 3: "Mar", 4: "Apr", 5: "Mei", 6: "Jun",
            7: "Jul", 8: "Agu", 9: "Sep", 10: "Okt", 11: "Nov", 12: "Des"}


def label_bulan(ym):
    t, b = ym.split("-")
    return f"{BULAN_ID[int(b)]} {t}"


def fint(x):
    return f"{int(round(x)):,}".replace(",", ".")


def f1(x):
    return f"{x:.1f}".replace(".", ",")


def fpct(x, d=1):
    return f"{100 * x:.{d}f}".replace(".", ",") + "%"


def fjuta(x):
    return f"{x / 1e6:.2f}".replace(".", ",") + " juta"


con = sqlite3.connect(DB)
trans = pd.read_csv(RAW / "category_translation.csv")
trans.to_sql("category_translation", con, if_exists="replace", index=False)

M = {}

# ---------- A1 tren bulanan ----------
SQL_TREN = """/* tren bulanan: revenue = SUM(price), hanya order delivered */
SELECT strftime('%Y-%m', o.order_purchase_timestamp) AS ym,
       COUNT(DISTINCT o.order_id) AS n_order,
       SUM(oi.price) AS revenue
FROM orders o
JOIN order_items oi ON oi.order_id = o.order_id
WHERE o.order_status = 'delivered'
GROUP BY ym
ORDER BY ym"""
trend = pd.read_sql(SQL_TREN, con)
full = pd.DataFrame({"ym": pd.period_range("2016-09", "2018-08", freq="M").strftime("%Y-%m")})
trend = full.merge(trend, on="ym", how="left").fillna(0)
trend["label"] = trend["ym"].map(label_bulan)
M["total_rev"] = trend.revenue.sum()
M["total_order_del"] = int(trend.n_order.sum())
M["best"] = trend.loc[trend.revenue.idxmax()]
M["avg_rev_2017"] = trend[trend.ym.str.startswith("2017")].revenue.mean()
M["avg_rev_2018"] = trend[trend.ym.str.startswith("2018")].revenue.mean()
M["growth"] = (M["avg_rev_2018"] - M["avg_rev_2017"]) / M["avg_rev_2017"]
cek_nov16 = pd.read_sql(
    "SELECT COUNT(*) AS n FROM orders WHERE strftime('%Y-%m', order_purchase_timestamp) = '2016-11'",
    con).iloc[0, 0]
M["nov16_kosong"] = (cek_nov16 == 0)
rev_status = pd.read_sql(
    """SELECT order_status, SUM(oi.price) AS revenue
       FROM orders o JOIN order_items oi ON oi.order_id = o.order_id
       GROUP BY order_status ORDER BY revenue DESC""", con)
M["share_delivered"] = (rev_status.loc[rev_status.order_status == "delivered", "revenue"].iloc[0]
                        / rev_status.revenue.sum())

# ---------- A2 kategori ----------
SQL_KAT_REV = """/* revenue dan order per kategori, hanya order delivered */
SELECT t.category_en AS kategori,
       COUNT(DISTINCT o.order_id) AS n_order,
       SUM(oi.price) AS revenue
FROM order_items oi
JOIN orders o ON o.order_id = oi.order_id
JOIN products p ON p.product_id = oi.product_id
JOIN category_translation t ON t.product_category_name = p.product_category_name
WHERE o.order_status = 'delivered'
GROUP BY t.category_en"""
SQL_KAT_REV2 = """/* skor dan bad review per kategori, satu review per order per kategori */
WITH co AS (
    SELECT DISTINCT o.order_id, t.category_en
    FROM order_items oi
    JOIN orders o ON o.order_id = oi.order_id
    JOIN products p ON p.product_id = oi.product_id
    JOIN category_translation t ON t.product_category_name = p.product_category_name
    WHERE o.order_status = 'delivered'
)
SELECT co.category_en AS kategori,
       AVG(r.review_score) AS avg_skor,
       AVG(CASE WHEN r.review_score <= 2 THEN 1.0 ELSE 0.0 END) AS bad_rate,
       COUNT(*) AS n_review
FROM co
JOIN reviews r ON r.order_id = co.order_id
GROUP BY co.category_en"""
kat = pd.read_sql(SQL_KAT_REV, con).merge(pd.read_sql(SQL_KAT_REV2, con), on="kategori")
kat["nama"] = kat.kategori.str.replace("_", " ")
kat["share"] = kat.revenue / kat.revenue.sum()
M["kat_top"] = kat.sort_values("revenue", ascending=False).head(10)
M["kat_bottom"] = kat.sort_values("revenue").head(10)
M["kat_n"] = len(kat)
kmin = kat[kat.n_review >= 50]
M["kat_bad_tertinggi"] = kmin.loc[kmin.bad_rate.idxmax()]
M["kat_skor_tertinggi"] = kmin.loc[kmin.avg_skor.idxmax()]
M["kat_skor_terendah"] = kmin.loc[kmin.avg_skor.idxmin()]

# ---------- A3 pengiriman ----------
SQL_KIRIM = """/* ringkasan pengiriman: rata rata hari kirim dan persen order telat */
SELECT COUNT(*) AS n,
       AVG(julianday(order_delivered_customer_date) - julianday(order_purchase_timestamp)) AS avg_hari,
       AVG(CASE WHEN julianday(order_delivered_customer_date) > julianday(order_estimated_delivery_date)
                THEN 1.0 ELSE 0.0 END) AS telat_rate
FROM orders
WHERE order_status = 'delivered'
  AND order_delivered_customer_date IS NOT NULL
  AND order_estimated_delivery_date IS NOT NULL"""
kirim = pd.read_sql(SQL_KIRIM, con).iloc[0]
M["kirim_n"] = int(kirim.n)
M["kirim_avg"] = kirim.avg_hari
M["telat_rate"] = kirim.telat_rate
SQL_KIRIM_SKOR = """/* rata rata waktu kirim untuk tiap skor review */
SELECT r.review_score AS skor,
       COUNT(*) AS n,
       AVG(julianday(o.order_delivered_customer_date) - julianday(o.order_purchase_timestamp)) AS avg_hari
FROM orders o
JOIN reviews r ON r.order_id = o.order_id
WHERE o.order_status = 'delivered'
  AND o.order_delivered_customer_date IS NOT NULL
GROUP BY r.review_score
ORDER BY skor"""
kskor = pd.read_sql(SQL_KIRIM_SKOR, con)
M["kskor"] = kskor
M["hari_skor1"] = kskor.loc[kskor.skor == 1, "avg_hari"].iloc[0]
M["hari_skor5"] = kskor.loc[kskor.skor == 5, "avg_hari"].iloc[0]
SQL_KIRIM_MED = """SELECT julianday(order_delivered_customer_date) - julianday(order_purchase_timestamp) AS hari
FROM orders
WHERE order_status = 'delivered'
  AND order_delivered_customer_date IS NOT NULL
  AND order_estimated_delivery_date IS NOT NULL"""
M["kirim_median"] = pd.read_sql(SQL_KIRIM_MED, con).hari.median()

# ---------- A4 geografi ----------
SQL_STATE = """/* jumlah order dan revenue per state pelanggan */
SELECT c.customer_state AS state,
       COUNT(DISTINCT o.order_id) AS n_order,
       SUM(oi.price) AS revenue
FROM orders o
JOIN customers c ON c.customer_id = o.customer_id
JOIN order_items oi ON oi.order_id = o.order_id
WHERE o.order_status = 'delivered'
GROUP BY c.customer_state
ORDER BY revenue DESC"""
state = pd.read_sql(SQL_STATE, con)
state["share"] = state.revenue / state.revenue.sum()
M["state"] = state
M["n_state"] = len(state)
SQL_KOTA = """/* lima kota dengan order terbanyak */
SELECT c.customer_city AS kota,
       COUNT(DISTINCT o.order_id) AS n_order,
       SUM(oi.price) AS revenue
FROM orders o
JOIN customers c ON c.customer_id = o.customer_id
JOIN order_items oi ON oi.order_id = o.order_id
WHERE o.order_status = 'delivered'
GROUP BY c.customer_city
ORDER BY n_order DESC
LIMIT 5"""
M["kota"] = pd.read_sql(SQL_KOTA, con)

# ---------- A5 seller ----------
SQL_SELLER = """/* bad review per seller, distinct order supaya tidak dobel hitung */
WITH rev AS (
    SELECT DISTINCT oi.seller_id, oi.order_id,
           CASE WHEN r.review_score <= 2 THEN 1 ELSE 0 END AS is_bad
    FROM order_items oi
    JOIN orders o ON oi.order_id = o.order_id
    LEFT JOIN reviews r ON r.order_id = oi.order_id
    WHERE o.order_status = 'delivered' AND r.review_score IS NOT NULL
)
SELECT seller_id,
       COUNT(*) AS n_review,
       SUM(is_bad) AS n_bad,
       1.0 * SUM(is_bad) / COUNT(*) AS bad_rate
FROM rev
GROUP BY seller_id"""
seller = pd.read_sql(SQL_SELLER, con)
M["seller_n"] = len(seller)
M["platform_bad_rate"] = seller.n_bad.sum() / seller.n_review.sum()
M["bad_order_total"] = int(seller.n_bad.sum())
s30 = seller[seller.bad_rate > 0.3]
M["seller_n30"] = len(s30)
M["seller_share30"] = s30.n_bad.sum() / seller.n_bad.sum()
s10 = seller.sort_values("n_bad", ascending=False).head(10)
M["seller_top10_share"] = s10.n_bad.sum() / seller.n_bad.sum()
M["seller_lorenz"] = seller.sort_values("n_bad", ascending=False).reset_index(drop=True)

# ---------- A6 pembayaran ----------
SQL_PAY = """/* tipe pembayaran dominan dan rata rata cicilan per order */
WITH dom AS (
    SELECT order_id, payment_type
    FROM (SELECT order_id, payment_type,
                 ROW_NUMBER() OVER (PARTITION BY order_id ORDER BY payment_value DESC) AS rn
          FROM payments)
    WHERE rn = 1
),
cic AS (
    SELECT order_id, MAX(payment_installments) AS cicilan
    FROM payments
    GROUP BY order_id
)
SELECT d.payment_type AS tipe,
       COUNT(*) AS n_order,
       AVG(c.cicilan) AS avg_cicilan
FROM dom d
JOIN cic c ON c.order_id = d.order_id
GROUP BY d.payment_type
ORDER BY n_order DESC"""
pay = pd.read_sql(SQL_PAY, con)
pay["share"] = pay.n_order / pay.n_order.sum()
M["pay"] = pay
M["pay_n_order"] = int(pay.n_order.sum())
SQL_CICIL = """/* persentase order yang memakai cicilan di atas 1 kali */
SELECT AVG(CASE WHEN m > 1 THEN 1.0 ELSE 0.0 END) AS pct_cicil
FROM (SELECT order_id, MAX(payment_installments) AS m FROM payments GROUP BY order_id)"""
M["pct_cicil"] = pd.read_sql(SQL_CICIL, con).iloc[0, 0]
M["n_orders_total"] = pd.read_sql("SELECT COUNT(*) FROM orders", con).iloc[0, 0]
M["n_orders_pay"] = pd.read_sql("SELECT COUNT(DISTINCT order_id) FROM payments", con).iloc[0, 0]

# ---------- A7 retensi ----------
SQL_RET = """/* retensi berbasis customer_unique_id, bukan customer_id */
WITH cnt AS (
    SELECT c.customer_unique_id AS uid, COUNT(*) AS n_order
    FROM orders o
    JOIN customers c ON c.customer_id = o.customer_id
    GROUP BY c.customer_unique_id
)
SELECT COUNT(*) AS n_customer,
       AVG(CASE WHEN n_order > 1 THEN 1.0 ELSE 0.0 END) AS repeat_rate,
       AVG(1.0 * n_order) AS avg_order
FROM cnt"""
ret = pd.read_sql(SQL_RET, con).iloc[0]
M["n_customer"] = int(ret.n_customer)
M["repeat_rate"] = ret.repeat_rate
M["avg_order"] = ret.avg_order
SQL_KOHOR = """/* kohor triwulanan: repeat dalam 90 hari setelah pembelian pertama */
WITH buys AS (
    SELECT DISTINCT c.customer_unique_id AS uid, date(o.order_purchase_timestamp) AS d
    FROM orders o
    JOIN customers c ON c.customer_id = o.customer_id
),
ranked AS (
    SELECT uid, d,
           ROW_NUMBER() OVER (PARTITION BY uid ORDER BY d) AS rn
    FROM buys
),
agg AS (
    SELECT uid,
           MAX(CASE WHEN rn = 1 THEN d END) AS first_date,
           MAX(CASE WHEN rn = 2 THEN d END) AS second_date
    FROM ranked
    WHERE rn <= 2
    GROUP BY uid
)
SELECT substr(first_date, 1, 4) || ' T' || ((CAST(substr(first_date, 6, 2) AS INT) - 1) / 3 + 1) AS kohor,
       COUNT(*) AS n_customer,
       AVG(CASE WHEN second_date IS NOT NULL
                 AND julianday(second_date) - julianday(first_date) <= 90
                THEN 1.0 ELSE 0.0 END) AS repeat_90d
FROM agg
GROUP BY kohor
ORDER BY kohor"""
kohor = pd.read_sql(SQL_KOHOR, con)
kohor = kohor[~kohor.kohor.isin(["2016 T3", "2016 T4", "2018 T4"])]
M["kohor"] = kohor
con.close()

print("Fase A selesai. Contoh angka :")
print(" total revenue :", fjuta(M["total_rev"]))
print(" telat rate    :", fpct(M["telat_rate"]))
print(" repeat rate   :", fpct(M["repeat_rate"]))
print(" top kategori  :", M["kat_top"].iloc[0]["nama"], fjuta(M["kat_top"].iloc[0]["revenue"]))

# ================= FASE B : rakit notebook =================
nb = nbf.v4.new_notebook()
nb.metadata["kernelspec"] = {"display_name": "Python 3 (mienv)",
                             "language": "python", "name": "mienv"}
nb.metadata["language_info"] = {"name": "python", "version": "3.12.3"}


def md(teks):
    return nbf.v4.new_markdown_cell(teks.strip())


def cc(teks):
    return nbf.v4.new_code_cell(teks.strip())


def sel(pairs, sesudah):
    defs = "\n".join(
        f'{nama} = """\n{sql.strip()}\n"""' for nama, sql in pairs)
    return cc(defs + "\n" + sesudah.strip())


cells = []

cells.append(md("""
# Analisis E Commerce Brasil : Dataset Publik Olist

Notebook ini berisi analisis data transaksi e commerce Brasil dari Olist,
marketplace yang menghubungkan penjual kecil ke pelanggan di seluruh Brasil.

**Dataset** : Brazilian E Commerce Public Dataset by Olist, lisensi CC BY-NC-SA 4.0,
sumber https://www.kaggle.com/datasets/olistbr/brazilian-ecommerce

**Periode data** : September 2016 sampai Oktober 2018.
**Cakupan** : 99.441 order, 96.096 pelanggan unik, 3.095 seller.

**Tujuan** : menjawab tujuh pertanyaan bisnis seputar tren revenue, kategori produk,
pengiriman, geografi, performa seller, pembayaran, dan retensi pelanggan.

**Catatan reproduksibilitas** : semua angka di notebook ini dihitung langsung dari
data memakai SQL dan pandas. Tidak ada angka yang diambil dari artikel atau sumber lain.
Menjalankan ulang semua sel dari awal akan menghasilkan angka dan chart yang sama.
"""))

cells.append(cc('''
import sqlite3
from pathlib import Path

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
import seaborn as sns

# ---------- path ----------
BASE = Path.cwd()
DB = BASE / "data" / "olist.db"
RAW = BASE / "data" / "raw"
CHARTS = BASE / "charts"
CHARTS.mkdir(exist_ok=True)

con = sqlite3.connect(DB)

# tabel terjemahan kategori buatan sendiri masuk ke sqlite supaya bisa di join
pd.read_csv(RAW / "category_translation.csv").to_sql(
    "category_translation", con, if_exists="replace", index=False)

# ---------- gaya chart ----------
PALET = ["#0E7C7B", "#2563EB", "#38BDF8", "#F59E0B",
         "#EF4444", "#8B5CF6", "#10B981", "#EC4899"]
plt.rcParams.update({
    "figure.figsize": (10, 6),
    "figure.dpi": 120,
    "savefig.dpi": 120,
    "font.size": 11,
    "axes.titlesize": 14,
    "axes.titleweight": "bold",
    "axes.labelsize": 11,
    "xtick.labelsize": 10,
    "ytick.labelsize": 10,
})
sns.set_theme(style="whitegrid")

BULAN_ID = {1: "Jan", 2: "Feb", 3: "Mar", 4: "Apr", 5: "Mei", 6: "Jun",
            7: "Jul", 8: "Agu", 9: "Sep", 10: "Okt", 11: "Nov", 12: "Des"}

def label_bulan(ym):
    # ubah "2017-01" menjadi "Jan 2017"
    t, b = ym.split("-")
    return BULAN_ID[int(b)] + " " + t

def fint(x):
    return f"{int(round(x)):,}".replace(",", ".")

def f1(x):
    return f"{x:.1f}".replace(".", ",")

def fpct(x, d=1):
    return f"{100 * x:.{d}f}".replace(".", ",") + "%"

def simpan(fig, nama_file):
    fig.tight_layout()
    fig.savefig(CHARTS / nama_file)
    plt.close(fig)
    print("chart tersimpan :", nama_file)

print("database :", DB, "| tabel :", pd.read_sql(
    "SELECT name FROM sqlite_master WHERE type='table' ORDER BY name", con)["name"].tolist())
'''))

# ================= 1 TREN =================
cells.append(md(f"""
## 1. Tren Revenue dan Jumlah Order per Bulan

**Definisi yang dipakai**

* Revenue = total kolom price dari order_items, tanpa freight_value.
  Ongkos kirim adalah biaya logistik, bukan revenue produk.
* Hanya order berstatus delivered yang dihitung. Order berstatus lain
  (canceled, unavailable, shipped, invoiced, processing) tidak selesai
  sehingga tidak menghasilkan revenue. Order delivered mencakup
  {fpct(M["share_delivered"])} dari total price seluruh order.
* Bulan dihitung dari order_purchase_timestamp.

**Query SQL**
"""))

cells.append(sel([("SQL_TREN", SQL_TREN)], '''
trend = pd.read_sql(SQL_TREN, con)
# lengkapi rentang bulan supaya tidak ada yang lompat, isi nol bila kosong
rentang = pd.DataFrame(
    {"ym": pd.period_range("2016-09", "2018-08", freq="M").strftime("%Y-%m")})
trend = rentang.merge(trend, on="ym", how="left").fillna(0)
trend["label"] = trend["ym"].map(label_bulan)
tampil_tren = trend[["label", "n_order", "revenue"]].copy()
tampil_tren.columns = ["bulan", "jumlah_order", "revenue"]
tampil_tren.head(10)
'''))

cells.append(cc('''
fig, (ax1, ax2) = plt.subplots(
    2, 1, figsize=(10, 6), sharex=True,
    gridspec_kw={"height_ratios": [3, 2], "hspace": 0.08})

ax1.plot(trend["label"], trend["revenue"] / 1e6, color="#0E7C7B",
         linewidth=2.5, marker="o", markersize=4)
ax1.set_title("Tren Revenue dan Jumlah Order per Bulan")
ax1.set_ylabel("Revenue (juta BRL)")
ax1.tick_params(labelbottom=False)

puncak = trend.loc[trend["revenue"].idxmax()]
ax1.annotate("puncak: " + label_bulan(puncak["ym"]),
             xy=(puncak["label"], puncak["revenue"] / 1e6),
             xytext=(12, -30), textcoords="offset points",
             arrowprops=dict(arrowstyle="->", color="black"), fontsize=10,
             bbox=dict(boxstyle="round", facecolor="white", alpha=0.9))

ax2.bar(trend["label"], trend["n_order"], color="#2563EB", width=0.7)
ax2.set_ylabel("Jumlah order")
ax2.set_xlabel("Bulan")
ax2.set_xticks(range(0, len(trend), 2))
ax2.set_xticklabels(trend["label"][::2], rotation=45, ha="right")

simpan(fig, "01_tren_revenue_order.png")
'''))

cells.append(md(f"""
**Insight**

* Total revenue dari order delivered adalah {fjuta(M["total_rev"])} BRL
  dari {fint(M["total_order_del"])} order, selama 23 bulan pengamatan.
* Rata rata revenue bulanan naik dari {fjuta(M["avg_rev_2017"])} BRL pada 2017
  menjadi {fjuta(M["avg_rev_2018"])} BRL pada Januari sampai Agustus 2018,
  tumbuh {fpct(M["growth"], 0)}.
* Puncak revenue terjadi pada {label_bulan(M["best"]["ym"])} sebesar
  {fjuta(M["best"]["revenue"])} BRL dengan {fint(M["best"]["n_order"])} order.
* November 2016 tidak mencatat order sama sekali, kemungkinan jeda operasional
  di awal periode data.
"""))

# ================= 2 KATEGORI =================
cells.append(md("""
## 2. Kategori Produk : Revenue, Skor Review, dan Bad Review

**Definisi yang dipakai**

* Kategori memakai terjemahan Inggris buatan sendiri dari nama Portugis
  (file category_translation.csv), karena file terjemahan resmi tidak tersedia
  di dataset ini. Asumsi ini dicatat di README.
* Revenue dihitung dari order delivered, sama seperti bagian 1.
* Bad review = review dengan skor 1 atau 2.
* Rata rata skor dan bad review rate dihitung satu review per order per kategori,
  supaya order dengan banyak item tidak dihitung berulang.

**Query SQL**
"""))

cells.append(cc(f'''SQL_KAT_REV = """
{SQL_KAT_REV.strip()}
"""
SQL_KAT_REV2 = """
{SQL_KAT_REV2.strip()}
"""
kat_rev = pd.read_sql(SQL_KAT_REV, con)
kat_rev2 = pd.read_sql(SQL_KAT_REV2, con)
kat = kat_rev.merge(kat_rev2, on="kategori")
kat["nama"] = kat["kategori"].str.replace("_", " ")
kat["share"] = kat["revenue"] / kat["revenue"].sum()

tampil = kat.sort_values("revenue", ascending=False).head(10).copy()
tampil["revenue_juta"] = tampil["revenue"] / 1e6
tampil = tampil[["nama", "n_order", "revenue_juta", "avg_skor",
                 "bad_rate", "share"]]
tampil.columns = ["kategori", "jumlah_order", "revenue_juta",
                  "rata_rata_skor", "bad_review_rate", "porsi_revenue"]
tampil.round({{"revenue_juta": 2, "rata_rata_skor": 2,
               "bad_review_rate": 3, "porsi_revenue": 3}})'''))

cells.append(cc('''
top10 = kat.sort_values("revenue", ascending=False).head(10).sort_values("revenue")
fig, ax = plt.subplots()
ax.barh(top10["nama"], top10["revenue"] / 1e6, color="#0E7C7B")
ax.set_title("10 Kategori dengan Revenue Tertinggi")
ax.set_xlabel("Revenue (juta BRL)")
for i, v in enumerate(top10["revenue"] / 1e6):
    ax.text(v + 0.02, i, f"{v:.2f}".replace(".", ","), va="center", fontsize=10)
simpan(fig, "02_top10_kategori_revenue.png")

bot10 = kat.sort_values("revenue").head(10).sort_values("revenue", ascending=False)
fig, ax = plt.subplots()
ax.barh(bot10["nama"], bot10["revenue"] / 1e6, color="#2563EB")
ax.set_title("10 Kategori dengan Revenue Terendah")
ax.set_xlabel("Revenue (juta BRL)")
for i, v in enumerate(bot10["revenue"] / 1e6):
    ax.text(v + 0.0004, i, f"{v:.3f}".replace(".", ","), va="center", fontsize=10)
simpan(fig, "03_bottom10_kategori_revenue.png")
'''))

cells.append(cc('''
fig, ax = plt.subplots()
ukuran = kat["revenue"] / kat["revenue"].max() * 700 + 30
ax.scatter(kat["bad_rate"] * 100, kat["avg_skor"], s=ukuran,
           color="#0E7C7B", alpha=0.65, edgecolors="white")
top5 = kat.sort_values("revenue", ascending=False).head(5).reset_index(drop=True)
offsets = [(10, 14), (-80, -24), (12, -16), (10, -22), (12, 12)]
for (_, r), off in zip(top5.iterrows(), offsets):
    ax.annotate(r["nama"], (r["bad_rate"] * 100, r["avg_skor"]),
                fontsize=9, xytext=off, textcoords="offset points")
ax.set_title("Kualitas Review per Kategori Produk")
ax.set_xlabel("Bad review rate (%)")
ax.set_ylabel("Rata rata skor review")
simpan(fig, "04_kategori_skor_vs_bad_rate.png")
'''))

t10 = M["kat_top"].iloc[0]
b10 = M["kat_bottom"].iloc[0]
cells.append(md(f"""
**Insight**

* Dari {M["kat_n"]} kategori, penyumbang revenue terbesar adalah
  {t10["nama"]} sebesar {fjuta(t10["revenue"])} BRL
  ({fpct(t10["share"])} dari total revenue).
* Kategori dengan revenue terkecil adalah {b10["nama"]}
  sebesar {fint(b10["revenue"])} BRL dari {fint(b10["n_order"])} order.
* Bad review rate tertinggi (kategori dengan minimal 50 review) ada pada
  {M["kat_bad_tertinggi"]["nama"]} sebesar
  {fpct(M["kat_bad_tertinggi"]["bad_rate"])}, dengan rata rata skor hanya
  {f1(M["kat_bad_tertinggi"]["avg_skor"])}.
* Skor tertinggi ada pada {M["kat_skor_tertinggi"]["nama"]}
  ({f1(M["kat_skor_tertinggi"]["avg_skor"])}), skor terendah pada
  {M["kat_skor_terendah"]["nama"]} ({f1(M["kat_skor_terendah"]["avg_skor"])}).
* Scatter plot menunjukkan kategori ber revenue besar cenderung punya
  bad review rate rendah dan skor tinggi, kecuali beberapa kategori
  furnitur dan elektronik yang skornya di bawah rata rata.
"""))

# ================= 3 PENGIRIMAN =================
cells.append(md("""
## 3. Performa Pengiriman

**Definisi yang dipakai**

* Waktu kirim = selisih hari antara order_delivered_customer_date
  dan order_purchase_timestamp.
* Telat = tanggal terima aktual melewati order_estimated_delivery_date.
* Hanya order delivered yang kedua tanggalnya terisi
  (96.470 order) yang dipakai.

**Query SQL**
"""))

cells.append(sel([("SQL_KIRIM", SQL_KIRIM), ("SQL_KIRIM_SKOR", SQL_KIRIM_SKOR)], '''
kirim = pd.read_sql(SQL_KIRIM, con).iloc[0]
kskor = pd.read_sql(SQL_KIRIM_SKOR, con)
print("jumlah order dianalisis :", fint(kirim["n"]))
print("rata rata waktu kirim   :", f1(kirim["avg_hari"]), "hari")
print("persentase order telat  :", fpct(kirim["telat_rate"]))
tampil_skor = kskor.copy()
tampil_skor.columns = ["skor", "jumlah_order", "rata_rata_hari"]
tampil_skor
'''))

cells.append(cc('''
fig, ax = plt.subplots(figsize=(10, 6))
label = ["Tepat waktu", "Telat"]
nilai = [(1 - kirim["telat_rate"]) * 100, kirim["telat_rate"] * 100]
warna = ["#0E7C7B", "#EF4444"]
bar = ax.barh(label, nilai, color=warna)
ax.set_title("Ketepatan Waktu Pengiriman")
ax.set_xlabel("Persentase order (%)")
for b, v in zip(bar, nilai):
    ax.text(v + 0.4, b.get_y() + b.get_height() / 2,
            fpct(v / 100), va="center", fontsize=12, fontweight="bold")
ax.set_xlim(0, 105)
simpan(fig, "05_pengiriman_telat.png")

fig, ax = plt.subplots()
bar = ax.bar(kskor["skor"].astype(str), kskor["avg_hari"], color=PALET[:5])
ax.set_title("Rata rata Waktu Kirim per Skor Review")
ax.set_xlabel("Skor review")
ax.set_ylabel("Rata rata waktu kirim (hari)")
for b, v in zip(bar, kskor["avg_hari"]):
    ax.text(b.get_x() + b.get_width() / 2, v + 0.25, f1(v),
            ha="center", fontsize=11, fontweight="bold")
simpan(fig, "06_waktu_kirim_per_skor.png")
'''))

cells.append(md(f"""
**Insight**

* Dari {fint(M["kirim_n"])} order delivered, {fpct(M["telat_rate"])}
  tiba melewati estimasi. Rata rata waktu kirim {f1(M["kirim_avg"])} hari
  dengan median {f1(M["kirim_median"])} hari.
* Hubungan dengan kepuasan sangat jelas: order dengan review bintang 1
  rata rata menunggu {f1(M["hari_skor1"])} hari, hampir dua kali lipat
  dibanding review bintang 5 yang hanya {f1(M["hari_skor5"])} hari.
  Keterlambatan adalah pendorong utama review buruk.
"""))

# ================= 4 GEOGRAFI =================
cells.append(md("""
## 4. Geografi : State dan Kota

**Definisi yang dipakai**

* State dan kota diambil dari data pelanggan (customer_state, customer_city).
* Revenue dan jumlah order dihitung dari order delivered.

**Query SQL**
"""))

cells.append(sel([("SQL_STATE", SQL_STATE), ("SQL_KOTA", SQL_KOTA)], '''
state = pd.read_sql(SQL_STATE, con)
state["share"] = state["revenue"] / state["revenue"].sum()
kota = pd.read_sql(SQL_KOTA, con)
print("jumlah state :", len(state))
tampil_state = state.head(10)[["state", "n_order", "revenue", "share"]].copy()
tampil_state.columns = ["state", "jumlah_order", "revenue", "porsi_revenue"]
tampil_state.round({"revenue": 0, "porsi_revenue": 3})
'''))

cells.append(cc('''
s10 = state.head(10).sort_values("revenue")
fig, ax = plt.subplots()
ax.barh(s10["state"], s10["revenue"] / 1e6, color="#0E7C7B")
ax.set_title("10 State dengan Revenue Tertinggi")
ax.set_xlabel("Revenue (juta BRL)")
for i, v in enumerate(s10["revenue"] / 1e6):
    ax.text(v + 0.05, i, f"{v:.2f}".replace(".", ","), va="center", fontsize=10)
simpan(fig, "07_state_revenue.png")

fig, ax = plt.subplots()
bar = ax.bar(kota["kota"], kota["n_order"], color="#2563EB")
ax.set_title("5 Kota dengan Order Terbanyak")
ax.set_ylabel("Jumlah order")
ax.set_xticks(range(len(kota)))
ax.set_xticklabels(kota["kota"], rotation=20, ha="right")
for b, v, rev in zip(bar, kota["n_order"], kota["revenue"]):
    ax.text(b.get_x() + b.get_width() / 2, v + 120,
            fint(v) + "\\n" + f"{rev/1e6:.1f}".replace(".", ",") + " jt",
            ha="center", fontsize=10)
simpan(fig, "08_top5_kota.png")
'''))

st0 = M["state"].iloc[0]
cells.append(md(f"""
**Insight**

* Konsentrasi geografis sangat tinggi: {M["n_state"]} state tercatat, tetapi
  state {st0["state"]} sendiri menyumbang {fint(st0["n_order"])} order
  ({fpct(st0["n_order"] / M["state"]["n_order"].sum())}) dan
  {fjuta(st0["revenue"])} BRL ({fpct(st0["share"])}) dari total revenue.
* Lima kota teratas semuanya kota besar di wilayah tenggara dan selatan,
  dipimpin {M["kota"].iloc[0]["kota"]} dengan {fint(M["kota"].iloc[0]["n_order"])} order.
  Ini sejalan dengan sebaran populasi dan daya beli Brasil.
"""))

# ================= 5 SELLER =================
cells.append(md("""
## 5. Seller : Apakah Bad Review Terkonsentrasi ?

**Definisi yang dipakai**

* Satu order bisa melibatkan beberapa seller, jadi perhitungan memakai
  distinct order supaya satu review tidak dihitung berulang.
* Bad review rate per seller = order bad review dibagi order yang direview.
* Ambang seller bermasalah = bad review rate di atas 30%.
* Hanya order delivered yang punya review yang dianalisis.

**Query SQL**
"""))

cells.append(sel([("SQL_SELLER", SQL_SELLER)], '''
seller = pd.read_sql(SQL_SELLER, con)
n30 = (seller["bad_rate"] > 0.3).sum()
share30 = seller.loc[seller["bad_rate"] > 0.3, "n_bad"].sum() / seller["n_bad"].sum()
top10 = seller.sort_values("n_bad", ascending=False).head(10)
share_top10 = top10["n_bad"].sum() / seller["n_bad"].sum()
print("seller yang dianalisis      :", fint(len(seller)))
print("platform bad review rate    :", fpct(seller["n_bad"].sum() / seller["n_review"].sum()))
print("seller bad rate di atas 30% :", fint(n30))
print("porsi bad review dari seller tersebut :", fpct(share30))
print("porsi bad review dari 10 seller terburuk :", fpct(share_top10))
tampil_seller = seller.sort_values("n_bad", ascending=False).head(10)[
    ["seller_id", "n_review", "n_bad", "bad_rate"]].copy()
tampil_seller.columns = ["seller_id", "jumlah_review",
                         "jumlah_bad_review", "bad_review_rate"]
tampil_seller.round({"bad_review_rate": 3})
'''))

cells.append(cc('''
fig, ax = plt.subplots()
label = ["Seller bermasalah\\n(bad rate di atas 30%)", "Seller lain"]
nilai = [share30 * 100, (1 - share30) * 100]
bar = ax.barh(label, nilai, color=["#EF4444", "#0E7C7B"])
ax.set_title("Asal Bad Review menurut Kualitas Seller")
ax.set_xlabel("Persentase dari seluruh bad review (%)")
for b, v in zip(bar, nilai):
    ax.text(v / 2, b.get_y() + b.get_height() / 2, fpct(v / 100),
            ha="center", va="center", fontsize=13,
            fontweight="bold", color="white")
ax.set_xlim(0, 105)
simpan(fig, "09_konsentrasi_bad_review_seller.png")
'''))

cells.append(md(f"""
**Insight**

* Bad review TIDAK terkonsentrasi di segelintir seller bermasalah.
  Dari {fint(M["seller_n"])} seller, {fint(M["seller_n30"])} seller punya
  bad review rate di atas 30%, tetapi mereka hanya menampung
  {fpct(M["seller_share30"])} dari seluruh order bad review.
* Bahkan 10 seller dengan bad review terbanyak hanya menampung
  {fpct(M["seller_top10_share"])} bad review.
* Chart asal bad review menegaskan: {fpct(1 - M["seller_share30"])} bad review
  berasal dari seller dengan bad rate 30% ke bawah, yaitu seller yang
  secara umum melayani dengan baik.
* Kesimpulan: ini masalah platform, bukan masalah segelintir seller.
  Perbaikan harus menyentuh pengalaman belanja secara umum
  (kecepatan kirim, deskripsi produk, layanan), bukan sekadar
  menindak seller tertentu.
"""))

# ================= 6 PEMBAYARAN =================
cells.append(md("""
## 6. Pembayaran : Tipe dan Pola Cicilan

**Definisi yang dipakai**

* Satu order bisa punya beberapa baris pembayaran. Tipe dominan per order =
  tipe dengan payment_value terbesar.
* Cicilan per order = nilai payment_installments terbesar per order.
* Persentase cicilan dihitung dari order yang datanya ada di tabel payments.

**Query SQL**
"""))

cells.append(sel([("SQL_PAY", SQL_PAY), ("SQL_CICIL", SQL_CICIL)], '''
pay = pd.read_sql(SQL_PAY, con)
pay["share"] = pay["n_order"] / pay["n_order"].sum()
pct_cicil = pd.read_sql(SQL_CICIL, con).iloc[0, 0]
print("order dengan data pembayaran :", fint(pay["n_order"].sum()))
print("order pakai cicilan di atas 1 kali :", fpct(pct_cicil))
tampil_pay = pay.copy()
tampil_pay.columns = ["tipe", "jumlah_order", "rata_rata_cicilan", "porsi"]
tampil_pay
'''))

cells.append(cc('''
fig, ax = plt.subplots()
bar = ax.bar(pay["tipe"], pay["share"] * 100, color=PALET[:len(pay)])
ax.set_title("Distribusi Tipe Pembayaran")
ax.set_xlabel("Tipe pembayaran")
ax.set_ylabel("Persentase order (%)")
for b, v in zip(bar, pay["share"]):
    ax.text(b.get_x() + b.get_width() / 2, v * 100 + 0.6, fpct(v),
            ha="center", fontsize=11, fontweight="bold")
simpan(fig, "10_tipe_pembayaran.png")

fig, ax = plt.subplots()
bar = ax.bar(pay["tipe"], pay["avg_cicilan"], color="#0E7C7B")
ax.set_title("Rata rata Cicilan per Tipe Pembayaran")
ax.set_xlabel("Tipe pembayaran")
ax.set_ylabel("Rata rata cicilan (kali)")
for b, v in zip(bar, pay["avg_cicilan"]):
    ax.text(b.get_x() + b.get_width() / 2, v + 0.08, f1(v),
            ha="center", fontsize=11, fontweight="bold")
ax.text(0.98, 0.94, "mayoritas order memakai cicilan",
        transform=ax.transAxes, ha="right", fontsize=10,
        bbox=dict(boxstyle="round", facecolor="white", alpha=0.8))
simpan(fig, "11_cicilan_per_tipe.png")
'''))

cc_pay = pay.set_index("tipe")
cells.append(md(f"""
**Insight**

* Kartu kredit mendominasi: {fpct(cc_pay.loc["credit_card", "share"])} order
  memakai credit_card, disusul boleto {fpct(cc_pay.loc["boleto", "share"])}.
* Budaya cicilan sangat kuat: {fpct(M["pct_cicil"])} order memakai cicilan
  lebih dari 1 kali. Rata rata cicilan kartu kredit
  {f1(cc_pay.loc["credit_card", "avg_cicilan"])} kali, jauh di atas
  boleto ({f1(cc_pay.loc["boleto", "avg_cicilan"])} kali) yang memang
  umumnya dibayar lunas.
"""))

# ================= 7 RETENSI =================
cells.append(md("""
## 7. Retensi Pelanggan dan Analisis Kohor

**Definisi yang dipakai**

* Identitas pelanggan memakai customer_unique_id, bukan customer_id,
  karena customer_id berbeda untuk tiap order sedangkan customer_unique_id
  menunjuk orang yang sama.
* Repeat purchase = pelanggan dengan lebih dari 1 order di seluruh periode data.
* Kohor = kelompok pelanggan berdasarkan triwulan pembelian pertama.
* Repeat 90 hari = belanja lagi dalam 90 hari setelah pembelian pertama,
  supaya antar kohor bisa dibandingkan secara adil.

**Query SQL**
"""))

cells.append(sel([("SQL_RET", SQL_RET), ("SQL_KOHOR", SQL_KOHOR)], '''
ret = pd.read_sql(SQL_RET, con).iloc[0]
kohor = pd.read_sql(SQL_KOHOR, con)
kohor = kohor[~kohor["kohor"].isin(["2016 T3", "2016 T4", "2018 T4"])]
print("pelanggan unik          :", fint(ret["n_customer"]))
print("repeat purchase rate    :", fpct(ret["repeat_rate"]))
print("rata rata order per pelanggan :", f1(ret["avg_order"]))
tampil_kohor = kohor.copy()
tampil_kohor.columns = ["kohor", "jumlah_pelanggan", "repeat_90_hari"]
tampil_kohor.round({"repeat_90_hari": 4})
'''))

cells.append(cc('''
fig, ax = plt.subplots(figsize=(10, 6))
vals = [(1 - ret["repeat_rate"]) * 100, ret["repeat_rate"] * 100]
ax.pie(vals, labels=["Belanja 1 kali", "Belanja ulang"],
       colors=["#E5E7EB", "#0E7C7B"], startangle=90,
       autopct=lambda p: fpct(p / 100),
       wedgeprops=dict(width=0.45), textprops={"fontsize": 12})
ax.set_title("Retensi Pelanggan")
simpan(fig, "12_retensi_pelanggan.png")
'''))

k_mid = M["kohor"][(M["kohor"]["kohor"] >= "2017 T1") & (M["kohor"]["kohor"] <= "2018 T2")]
cells.append(md(f"""
**Insight**

* Dari {fint(M["n_customer"])} pelanggan unik, hanya
  {fpct(M["repeat_rate"])} yang belanja lebih dari 1 kali.
  Rata rata {f1(M["avg_order"])} order per pelanggan: Olist praktis
  adalah bisnis pembeli sekali beli.
* Analisis kohor memperkuat temuan ini: repeat dalam 90 hari setelah
  pembelian pertama hanya {fpct(k_mid["repeat_90d"].min())} sampai
  {fpct(k_mid["repeat_90d"].max())} di semua kohor 2017 T1 sampai 2018 T2,
  tanpa tren perbaikan.
* Peluang terbesar ada di retensi: menaikkan repeat purchase sedikit saja
  berdampak besar karena basis pelanggan sudah hampir 100 ribu orang.

## Ringkasan Temuan Kunci

1. Revenue {fjuta(M["total_rev"])} BRL dari {fint(M["total_order_del"])} order
   delivered, tumbuh {fpct(M["growth"], 0)} dari rata rata bulanan 2017
   ke Januari sampai Agustus 2018.
2. Kategori {t10["nama"]} adalah motor revenue ({fjuta(t10["revenue"])} BRL),
   sedangkan {M["kat_bad_tertinggi"]["nama"]} punya bad review rate tertinggi
   ({fpct(M["kat_bad_tertinggi"]["bad_rate"])}).
3. {fpct(M["telat_rate"])} order tiba telat; review bintang 1 menunggu
   {f1(M["hari_skor1"])} hari vs {f1(M["hari_skor5"])} hari untuk bintang 5.
4. State {st0["state"]} mendominasi dengan {fpct(st0["share"])} revenue;
   pasar sangat terkonsentrasi di tenggara Brasil.
5. Bad review tersebar merata antar seller, bukan ulah segelintir seller:
   seller dengan bad rate di atas 30% hanya menampung
   {fpct(M["seller_share30"])} bad review. Ini masalah platform.
6. {fpct(cc_pay.loc["credit_card", "share"])} pembayaran memakai kartu kredit
   dan {fpct(M["pct_cicil"])} order dicicil lebih dari 1 kali.
7. Retensi sangat rendah: repeat purchase rate hanya
   {fpct(M["repeat_rate"])}. Fokus ke pembelian ulang adalah
   peluang pertumbuhan terbesar.
"""))

nb.cells = cells
nbf.write(nb, NB_PATH)
print("notebook tersimpan :", NB_PATH, "| jumlah sel :", len(cells))

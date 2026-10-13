/* ============================================================
   Query SQL utama analisis E Commerce Brasil dataset Olist.
   Semua query memakai SQLite. Komentar memakai Bahasa Indonesia.
   Hasil query diolah lanjut memakai pandas di analysis.ipynb.
   ============================================================ */

/* ========== verifikasi jumlah baris tiap tabel ========== */
SELECT 'customers'   AS tabel, COUNT(*) AS n FROM customers
UNION ALL SELECT 'geolocation', COUNT(*) FROM geolocation
UNION ALL SELECT 'order_items', COUNT(*) FROM order_items
UNION ALL SELECT 'payments',    COUNT(*) FROM payments
UNION ALL SELECT 'reviews',     COUNT(*) FROM reviews
UNION ALL SELECT 'orders',      COUNT(*) FROM orders
UNION ALL SELECT 'products',    COUNT(*) FROM products
UNION ALL SELECT 'sellers',     COUNT(*) FROM sellers;

/* ========== 1a tren revenue dan order per bulan ==========
   Definisi : revenue = SUM(price) dari order_items, tanpa freight_value.
   Hanya order berstatus delivered, karena order berstatus lain tidak
   selesai dan tidak menghasilkan revenue. */
SELECT strftime('%Y-%m', o.order_purchase_timestamp) AS ym,
       COUNT(DISTINCT o.order_id) AS n_order,
       SUM(oi.price) AS revenue
FROM orders o
JOIN order_items oi ON oi.order_id = o.order_id
WHERE o.order_status = 'delivered'
GROUP BY ym
ORDER BY ym;

/* ========== 1b pembanding revenue per status ==========
   dipakai untuk menjustifikasi pilihan hanya order delivered */
SELECT o.order_status AS status,
       COUNT(DISTINCT o.order_id) AS n_order,
       SUM(oi.price) AS revenue
FROM orders o
JOIN order_items oi ON oi.order_id = o.order_id
GROUP BY o.order_status
ORDER BY revenue DESC;

/* ========== 2a revenue dan order per kategori ==========
   category_translation adalah tabel terjemahan Inggris buatan sendiri
   dari nama kategori Portugis, karena file resmi tidak tersedia */
SELECT t.category_en AS kategori,
       COUNT(DISTINCT o.order_id) AS n_order,
       SUM(oi.price) AS revenue
FROM order_items oi
JOIN orders o ON o.order_id = oi.order_id
JOIN products p ON p.product_id = oi.product_id
JOIN category_translation t
  ON t.product_category_name = p.product_category_name
WHERE o.order_status = 'delivered'
GROUP BY t.category_en;

/* ========== 2b skor review dan bad review per kategori ==========
   Satu review dihitung satu kali per order per kategori supaya order
   dengan banyak item tidak dihitung berulang.
   Bad review = skor 1 atau 2. */
WITH co AS (
    SELECT DISTINCT o.order_id, t.category_en
    FROM order_items oi
    JOIN orders o ON o.order_id = oi.order_id
    JOIN products p ON p.product_id = oi.product_id
    JOIN category_translation t
      ON t.product_category_name = p.product_category_name
    WHERE o.order_status = 'delivered'
)
SELECT co.category_en AS kategori,
       AVG(r.review_score) AS avg_skor,
       AVG(CASE WHEN r.review_score <= 2 THEN 1.0 ELSE 0.0 END) AS bad_rate,
       COUNT(*) AS n_review
FROM co
JOIN reviews r ON r.order_id = co.order_id
GROUP BY co.category_en;

/* ========== 3a ringkasan performa pengiriman ==========
   Waktu kirim dalam hari. Telat = terima aktual melewati estimasi. */
SELECT COUNT(*) AS n,
       AVG(julianday(order_delivered_customer_date)
           - julianday(order_purchase_timestamp)) AS avg_hari,
       AVG(CASE WHEN julianday(order_delivered_customer_date)
                     > julianday(order_estimated_delivery_date)
                THEN 1.0 ELSE 0.0 END) AS telat_rate
FROM orders
WHERE order_status = 'delivered'
  AND order_delivered_customer_date IS NOT NULL
  AND order_estimated_delivery_date IS NOT NULL;

/* ========== 3b rata rata waktu kirim per skor review ========== */
SELECT r.review_score AS skor,
       COUNT(*) AS n,
       AVG(julianday(o.order_delivered_customer_date)
           - julianday(o.order_purchase_timestamp)) AS avg_hari
FROM orders o
JOIN reviews r ON r.order_id = o.order_id
WHERE o.order_status = 'delivered'
  AND o.order_delivered_customer_date IS NOT NULL
GROUP BY r.review_score
ORDER BY skor;

/* ========== 4a order dan revenue per state ========== */
SELECT c.customer_state AS state,
       COUNT(DISTINCT o.order_id) AS n_order,
       SUM(oi.price) AS revenue
FROM orders o
JOIN customers c ON c.customer_id = o.customer_id
JOIN order_items oi ON oi.order_id = o.order_id
WHERE o.order_status = 'delivered'
GROUP BY c.customer_state
ORDER BY revenue DESC;

/* ========== 4b lima kota teratas ========== */
SELECT c.customer_city AS kota,
       COUNT(DISTINCT o.order_id) AS n_order,
       SUM(oi.price) AS revenue
FROM orders o
JOIN customers c ON c.customer_id = o.customer_id
JOIN order_items oi ON oi.order_id = o.order_id
WHERE o.order_status = 'delivered'
GROUP BY c.customer_city
ORDER BY n_order DESC
LIMIT 5;

/* ========== 5 bad review per seller ==========
   Distinct order supaya satu review tidak dihitung berulang ketika
   satu order melibatkan beberapa seller atau beberapa item. */
WITH rev AS (
    SELECT DISTINCT oi.seller_id, oi.order_id,
           CASE WHEN r.review_score <= 2 THEN 1 ELSE 0 END AS is_bad
    FROM order_items oi
    JOIN orders o ON oi.order_id = o.order_id
    LEFT JOIN reviews r ON r.order_id = oi.order_id
    WHERE o.order_status = 'delivered'
      AND r.review_score IS NOT NULL
)
SELECT seller_id,
       COUNT(*) AS n_review,
       SUM(is_bad) AS n_bad,
       1.0 * SUM(is_bad) / COUNT(*) AS bad_rate
FROM rev
GROUP BY seller_id;

/* ========== 6a tipe pembayaran dominan per order ==========
   Satu order bisa punya beberapa baris pembayaran. Tipe dominan =
   tipe dengan payment_value terbesar. */
WITH dom AS (
    SELECT order_id, payment_type
    FROM (SELECT order_id, payment_type,
                 ROW_NUMBER() OVER (
                     PARTITION BY order_id ORDER BY payment_value DESC) AS rn
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
ORDER BY n_order DESC;

/* ========== 6b persentase order yang memakai cicilan ========== */
SELECT AVG(CASE WHEN m > 1 THEN 1.0 ELSE 0.0 END) AS pct_cicil
FROM (SELECT order_id, MAX(payment_installments) AS m
      FROM payments
      GROUP BY order_id);

/* ========== 7a retensi pelanggan ==========
   Identitas memakai customer_unique_id, bukan customer_id, karena
   customer_id berbeda tiap order sedangkan customer_unique_id
   menunjuk orang yang sama. */
WITH cnt AS (
    SELECT c.customer_unique_id AS uid, COUNT(*) AS n_order
    FROM orders o
    JOIN customers c ON c.customer_id = o.customer_id
    GROUP BY c.customer_unique_id
)
SELECT COUNT(*) AS n_customer,
       AVG(CASE WHEN n_order > 1 THEN 1.0 ELSE 0.0 END) AS repeat_rate,
       AVG(1.0 * n_order) AS avg_order
FROM cnt;

/* ========== 7b kohor triwulanan, repeat dalam 90 hari ==========
   Repeat 90 hari dipakai supaya antar kohor bisa dibandingkan adil. */
WITH buys AS (
    SELECT DISTINCT c.customer_unique_id AS uid,
           date(o.order_purchase_timestamp) AS d
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
SELECT substr(first_date, 1, 4) || ' T'
       || ((CAST(substr(first_date, 6, 2) AS INT) - 1) / 3 + 1) AS kohor,
       COUNT(*) AS n_customer,
       AVG(CASE WHEN second_date IS NOT NULL
                 AND julianday(second_date) - julianday(first_date) <= 90
                THEN 1.0 ELSE 0.0 END) AS repeat_90d
FROM agg
GROUP BY kohor
ORDER BY kohor;

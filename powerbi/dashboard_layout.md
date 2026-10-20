# Dashboard Layout — Olist Brazilian E-commerce (4 halaman, 16:9)

Palet: teal gelap `#0E7C7B` (primer), amber `#D9A441` (aksen), slate `#3A6EA5`, bata `#C1553B` (khusus terlambat dan review buruk).
Font: Segoe UI / Calibri. Satu ide per halaman, judul rata kiri, angka kunci besar. Satuan uang selalu BRL, persen 1 desimal, hari 1 desimal.

## Halaman 1 — Ringkasan Eksekutif
- **KPI cards (4)**: Total Pesanan 99.441 (di bawahnya: 96.478 delivered); Total Revenue Produk 13.221.498 BRL (tampilkan sebagai 13,22 juta BRL); Rata-rata Nilai Pesanan 137,04 BRL; Pertumbuhan Revenue Persen +81,6% (rata-rata bulanan Jan–Agu 2018 vs 2017).
- **Line + column chart**: tren bulanan — sumbu X `dim_tanggal[tahun_bulan]`, kolom `Total Pesanan Delivered`, garis `Total Revenue Produk`. Sorot November 2017 sebagai bulan puncak (987.765,37 BRL, 7.289 order).
- **Slicers**: Tahun (`dim_tanggal[tahun]`), State (`dim_negara_bagian[customer_state]`). (Sumber: `fact_pesanan`.)
- Catatan kaki: "Sumber: dataset publik Olist (CC BY-NC-SA 4.0), order Sep 2016 – Okt 2018. Revenue = total harga produk order delivered, tidak termasuk ongkir."

## Halaman 2 — Kategori Produk
- **Bar chart horizontal**: Revenue Item Delivered per kategori, 10 teratas. Acuan: health_beauty 1.233.131,72 BRL; watches_gifts 1.166.176,98 BRL; bed_bath_table 1.023.434,76 BRL.
- **Tabel**: Kategori | Revenue Item Delivered | Persen Share Revenue Kategori | Total Item Terjual | Rata-rata Harga Item. Urutkan menurun menurut revenue.
- **KPI kecil**: Total Item Terjual 112.650 baris item (semua status; angka ini akan turun bila slicer status dipasang — biarkan halaman ini tanpa slicer status).
- **Slicers**: Kategori (`dim_kategori[kategori]`), State. (Sumber: `fact_item_pesanan` SAJA. Jangan tarik kolom dari `fact_pesanan` ke halaman ini.)

## Halaman 3 — Pengiriman & Review
- **KPI cards (3)**: Rata-rata Hari Pengiriman 12,6 hari; Persen Tepat Waktu 91,9%; Persen Terlambat 8,1% (warna bata).
- **Bar chart**: Rata-rata Hari Pengiriman per skor review — sumbu kategori memakai kolom `fact_pesanan[skor_review]` (bukan dimensi), nilai: bintang 1 = 21,3 hari; bintang 2 = 16,7 hari; bintang 3 = 14,2 hari; bintang 4 = 12,3 hari; bintang 5 = 10,7 hari. Ini visual kunci halaman ini: makin lama menunggu, makin buruk skornya.
- **Bar chart kedua**: Persen Review Buruk per state (slicer Tahun boleh dipasang; ingat angka nasional semua status = 14,7%, khusus delivered = 12,8%).
- **Slicers**: Tahun, State. (Sumber: `fact_pesanan` SAJA.)

## Halaman 4 — Geografi, Retensi & Metodologi
- **Peta (filled map)**: Total Revenue Produk per `dim_negara_bagian[customer_state]`, gradasi teal. Acuan: SP 5.067.633,16 BRL; RJ 1.759.651,13 BRL; MG 1.552.481,83 BRL.
- **Bar chart**: Total Pesanan Delivered per state, 10 teratas. Acuan: SP 40.501 order (42,0% dari semua order delivered).
- **KPI retensi (3)**: Jumlah Pelanggan Unik 96.096; Pelanggan Repeat 2.997; Persen Repeat Purchase 3,1%. Tampilkan TANPA filter status dan TANPA filter tahun (konteks penuh), dan beri label konteks itu di bawah kartu.
- **Tabel metodologi**: sumber data dan atribusi Olist; definisi revenue (harga produk, delivered, tanpa ongkir) vs total pembayaran (termasuk ongkir); aturan review pertama per order untuk 551 order multi-review; periode data Sep 2016 – Okt 2018, dengan catatan 2016 dan akhir 2018 adalah tahun parsial.
- **Tombol navigasi** kembali ke Halaman 1.

## Aturan konsisten
- Judul halaman: 20pt bold, rata kiri, warna slate gelap.
- Angka KPI: 28pt bold teal; satuan BRL; persen 1 desimal; tanggal mengikuti `dim_tanggal` yang sudah ditandai sebagai tabel tanggal.
- Halaman 2 hanya `fact_item_pesanan`; Halaman 3 hanya `fact_pesanan`; jangan mencampur kedua fakta dalam satu visual.
- Warna bata hanya untuk terlambat dan review buruk; jangan dipakai untuk kategori atau state.
- Setiap halaman yang menampilkan angka repeat purchase atau review buruk wajib menyebut konteks filternya (semua status vs delivered).

# Panduan Membangun Dashboard — Power BI Desktop

## 1. Persiapan (5 menit)
1. Buka Power BI Desktop → Get Data → Text/CSV → impor keenam CSV di folder ini:
   `fact_pesanan.csv`, `fact_item_pesanan.csv`, `dim_tanggal.csv`, `dim_kategori.csv`, `dim_status.csv`, `dim_negara_bagian.csv`.
   File CSV pembangun kit (`build_kit_csv.py`) dan file markdown di folder ini TIDAK perlu diimpor.
2. Pastikan tipe data:
   - `fact_pesanan`: `tanggal_beli` = Date; `total_pembayaran`, `total_harga_produk`, `total_ongkir`, `hari_pengiriman`, `estimasi_hari` = Decimal Number; `jumlah_item`, `terlambat_flag`, `skor_review` = Whole Number; sisanya Text.
   - `fact_item_pesanan`: `tanggal_beli` = Date; `price`, `freight_value` = Decimal Number; sisanya Text.
   - `dim_tanggal`: `tanggal` = Date; `tahun`, `kuartal`, `bulan` = Whole Number; sisanya Text.
   - Atur format mata uang measure uang ke BRL (atau tulis "BRL" di label visual) supaya tidak tertukar dengan Rupiah.
3. Buka Model view. Buat relasi (semuanya satu-ke-banyak, single direction):
   - `dim_tanggal[tanggal]` → `fact_pesanan[tanggal_beli]`
   - `dim_tanggal[tanggal]` → `fact_item_pesanan[tanggal_beli]`
   - `dim_status[order_status]` → `fact_pesanan[order_status]`
   - `dim_status[order_status]` → `fact_item_pesanan[order_status]`
   - `dim_negara_bagian[customer_state]` → `fact_pesanan[customer_state]`
   - `dim_negara_bagian[customer_state]` → `fact_item_pesanan[customer_state]`
   - `dim_kategori[kategori]` → `fact_item_pesanan[kategori]`
4. Klik kanan `dim_tanggal` → Mark as Date Table (kolom `tanggal`).

## 2. Measures (10 menit)
1. Salin seluruh blok DAX dari `measures_dax.md` ke dalam model (buat dua tabel measure atau gunakan folder display: "Pesanan" dan "Item Pesanan").
2. Baca bagian "Catatan level" dan "Definisi kunci" di `measures_dax.md` SEBELUM membuat visual — terutama perbedaan revenue produk vs total pembayaran.
3. Uji cepat: buat card dengan `Total Revenue Produk` tanpa filter apa pun → harus **13.221.498,11 BRL**. Buat card kedua dengan `Revenue Item Delivered` → harus **sama persis**. Jika beda, cek relasi `dim_status` ke kedua fakta.

## 3. Bangun 4 halaman (30–45 menit)
Ikuti `dashboard_layout.md` halaman per halaman:
- Halaman 1: ringkasan eksekutif dari `fact_pesanan`.
- Halaman 2: HANYA field dari `fact_item_pesanan` + measures ITEM PESANAN.
- Halaman 3: HANYA field dari `fact_pesanan` + measures PESANAN.
- Halaman 4: geografi dan retensi dari `fact_pesanan` + tabel metodologi (ketik manual dari `dashboard_layout.md`).

## 4. Verifikasi akhir (10 menit)
- [ ] Halaman 1 KPI: Total Pesanan 99.441; Total Revenue Produk 13.221.498,11 BRL; Rata-rata Nilai Pesanan 137,04 BRL; Pertumbuhan Revenue +81,6%.
- [ ] Halaman 2: kategori teratas health_beauty 1.233.131,72 BRL; `Revenue Item Delivered` total sama dengan `Total Revenue Produk`.
- [ ] Halaman 3: Rata-rata Hari Pengiriman 12,6 hari; Persen Tepat Waktu 91,9%; Persen Terlambat 8,1%; bintang 1 = 21,3 hari dan bintang 5 = 10,7 hari.
- [ ] Halaman 4: SP 40.501 order delivered dan revenue 5.067.633,16 BRL; Persen Repeat Purchase 3,1% pada konteks tanpa filter status dan tanpa filter tahun.
- [ ] Tidak ada visual yang mencampur `fact_pesanan` dan `fact_item_pesanan` dalam satu agregasi, dan tidak ada visual berlabel revenue yang memakai `total_pembayaran`.
- [ ] Simpan sebagai `Olist-Ecommerce-Analysis.pbix` (file .pbix tidak di-push ke GitHub — GitHub tidak bisa me-render-nya; simpan screenshot dashboard sebagai gantinya bila perlu).

## Troubleshooting
- **Revenue tampil 15,4 juta, bukan 13,2 juta**: visual memakai `total_pembayaran` (termasuk ongkir). Ganti ke measure `Total Revenue Produk` atau `Revenue Item Delivered`.
- **Persen Repeat Purchase tampil 3,0%, bukan 3,1%**: halaman atau visual sedang terfilter status `delivered`. Angka acuan 3,1% memakai semua status; lepaskan filter status untuk kartu retensi.
- **Persen Review Buruk beda dari acuan**: cek konteks statusnya. Semua status = 14,7%; khusus delivered = 12,8%. Keduanya benar pada konteksnya masing-masing.
- **Skor review tampil sebagai desimal aneh di sumbu**: pastikan `skor_review` bertipe Whole Number dan agregasi visual untuk kolom ini dimatikan bila dipakai sebagai kategori sumbu (dipakai sebagai label, bukan dijumlahkan).
- **Tanggal tidak urut di sumbu X**: pastikan `dim_tanggal` ditandai sebagai date table dan sumbu memakai `dim_tanggal[tahun_bulan]` atau `dim_tanggal[tanggal]`, bukan kolom tanggal dari tabel fakta.
- **Kategori `tidak_diketahui` muncul di chart**: itu penanda produk tanpa kategori di dataset mentah. Sembunyikan lewat filter visual bila mengganggu, tetapi jangan hapus barisnya dari fakta (revenue total akan berubah).

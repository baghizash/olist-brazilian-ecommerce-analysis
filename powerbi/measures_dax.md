# DAX Measures — Olist Brazilian E-commerce

## Catatan level (PENTING — baca dulu)

Model ini memakai **dua tabel fakta terpisah per grain** (prinsip yang sama dengan proyek Harga Pangan):

| Tabel fakta | Grain (1 baris =) | Untuk visual... |
|---|---|---|
| `fact_pesanan` | 1 order | Pesanan, pembayaran, pengiriman, review, retensi pelanggan |
| `fact_item_pesanan` | 1 order-item (1 baris item di dalam order) | Revenue dan harga per kategori produk |

**Tidak ada baris agregat di kedua tabel fakta** (tidak ada baris "total", tidak ada baris ringkasan per kategori atau per state). Karena itu setiap measure di bawah membaca tepat satu grain. Jangan menjumlahkan kolom dari kedua fakta dalam satu visual: `total_harga_produk` di `fact_pesanan` dan `price` di `fact_item_pesanan` adalah dua jalan ke revenue yang sama dan hanya boleh dipakai lewat measure masing-masing.

Definisi kunci yang WAJIB dijaga:

| Istilah | Definisi di kit ini |
|---|---|
| Revenue produk | `SUM(price)` dari item, HANYA order berstatus `delivered`. Di `fact_pesanan` tersedia sebagai kolom `total_harga_produk`; di `fact_item_pesanan` sebagai kolom `price`. |
| Total pembayaran | `SUM(payment_value)` per order, tersedia sebagai `total_pembayaran`. Ini BUKAN revenue: pembayaran mencakup harga produk DITAMBAH ongkir (dan selisih kecil dari order tanpa item). Jangan pernah menampilkan `total_pembayaran` dengan label revenue. |
| Skor review per order | Dataset mentah punya 99.224 baris review untuk 98.673 order: 551 order punya lebih dari 1 review (547 order punya 2 review, 4 order punya 3 review). Untuk grain 1 baris per order, `fact_pesanan[skor_review]` memakai review PERTAMA menurut tanggal pembuatan review. |
| Hari pengiriman | `order_delivered_customer_date` dikurangi `order_purchase_timestamp`, dalam hari desimal (2 angka desimal). Kolom `estimasi_hari` memakai cara yang sama terhadap `order_estimated_delivery_date`. |
| Terlambat | `terlambat_flag` = 1 bila tanggal terima aktual melewati estimasi, 0 bila tepat waktu, kosong bila order belum diterima (belum ada tanggal terima aktual). |

Relasi: `dim_tanggal[tanggal]` 1—* `fact_pesanan[tanggal_beli]` dan 1—* `fact_item_pesanan[tanggal_beli]`; `dim_status[order_status]` 1—* kedua fakta; `dim_negara_bagian[customer_state]` 1—* kedua fakta; `dim_kategori[kategori]` 1—* `fact_item_pesanan[kategori]`. `dim_tanggal` ditandai sebagai tabel tanggal. `dim_kategori` berisi 73 kategori asli plus 1 penanda `tidak_diketahui` untuk produk tanpa kategori di dataset mentah.

## Verifikasi angka (dihitung ulang dari CSV kit ini)

| Angka | Nilai dari kit | Catatan |
|---|---|---|
| Total pesanan | 99.441 order | Semua status |
| Pesanan delivered | 96.478 order | 97,0% dari total pesanan |
| Total Revenue Produk (delivered) | 13.221.498,11 BRL | Dari `fact_pesanan` DAN dari `fact_item_pesanan` hasilnya sama persis: 13,22 juta BRL, cocok dengan README |
| Total Pembayaran (delivered) | 15.422.461,77 BRL | Berbeda dari revenue dan memang harus berbeda: pembayaran = harga produk + ongkir. Harga produk + ongkir delivered = 15.424.463,65 BRL; selisih 2.001,88 BRL (0,01%) berasal dari order yang punya pembayaran tetapi tidak punya baris item yang cocok |
| Total Pembayaran (semua status) | 16.008.872,12 BRL | Untuk konteks pembayaran saja, jangan dicampur dengan revenue |
| Rata-rata Nilai Pesanan (delivered) | 137,04 BRL | Revenue produk dibagi 96.478 order delivered |
| Rata-rata pembayaran per order delivered | 159,85 BRL | Lebih tinggi dari nilai pesanan karena termasuk ongkir |
| Rata-rata revenue bulanan 2017 | 496.908,50 BRL | Total revenue delivered 2017 dibagi 12 bulan |
| Rata-rata revenue bulanan Jan–Agu 2018 | 902.265,64 BRL | Total revenue delivered Jan–Agu 2018 dibagi 8 bulan |
| Pertumbuhan revenue | +81,6% | Rata-rata bulanan Jan–Agu 2018 vs rata-rata bulanan 2017; dibulatkan menjadi +82% di README |
| Bulan puncak revenue | November 2017: 987.765,37 BRL, 7.289 order | Cocok dengan README |
| Rata-rata hari pengiriman | 12,6 hari (median 10,2 hari) | Order delivered |
| Rata-rata hari pengiriman, review bintang 1 | 21,3 hari | Dari `fact_pesanan` (skor review pertama per order): 21,32 hari |
| Rata-rata hari pengiriman, review bintang 5 | 10,7 hari | Dari `fact_pesanan` (skor review pertama per order): 10,68 hari |
| Persen tepat waktu | 91,9% | Order delivered dengan `terlambat_flag` = 0 |
| Persen terlambat | 8,1% | Order delivered dengan `terlambat_flag` = 1; cocok dengan README |
| Rata-rata skor review | 4,09 (semua order yang punya review); 4,16 (khusus delivered) | Perhatikan konteks status saat membandingkan angka ini |
| Persen review buruk (skor 1–2) | 14,7% (semua order yang punya review); 12,8% (khusus delivered) | Order non-delivered jauh lebih negatif, jadi angka ini sensitif terhadap filter status |
| Pelanggan unik | 96.096 | Berdasarkan `customer_unique_id` |
| Pelanggan repeat | 2.997 pelanggan | `customer_unique_id` dengan lebih dari 1 order (semua status) |
| Persen Repeat Purchase | 3,1% | 2.997 / 96.096 = 3,12%; cocok dengan README. Bila dashboard difilter khusus `delivered`, hasilnya turun menjadi 3,0% — itu bukan kesalahan, itu perubahan konteks |
| Kategori revenue terbesar | health_beauty: 1.233.131,72 BRL | Dari `fact_item_pesanan`, order delivered |
| State terbesar | SP: 40.501 order delivered, revenue 5.067.633,16 BRL | 42,0% order delivered dan 38,3% revenue; cocok dengan README |

Visual WAJIB cocok dengan tabel di atas pada konteks yang tertulis. Jika berbeda, cek dulu: (1) visual memakai tabel fakta yang benar, (2) konteks statusnya (semua status vs khusus delivered), (3) relasi ke `dim_status` dan `dim_tanggal` sudah dibuat.

## Measures — PESANAN (tabel `fact_pesanan`)

```dax
Total Pesanan =
DISTINCTCOUNT ( fact_pesanan[order_id] )

Total Pesanan Delivered =
CALCULATE ( [Total Pesanan], dim_status[order_status] = "delivered" )

Total Revenue Produk =
CALCULATE (
    SUM ( fact_pesanan[total_harga_produk] ),
    dim_status[order_status] = "delivered"
)

Total Pembayaran =
SUM ( fact_pesanan[total_pembayaran] )

Total Pembayaran Delivered =
CALCULATE (
    SUM ( fact_pesanan[total_pembayaran] ),
    dim_status[order_status] = "delivered"
)

Rata-rata Nilai Pesanan =
DIVIDE ( [Total Revenue Produk], [Total Pesanan Delivered] )

Rata-rata Hari Pengiriman =
AVERAGE ( fact_pesanan[hari_pengiriman] )

Rata-rata Estimasi Hari =
AVERAGE ( fact_pesanan[estimasi_hari] )

Rata-rata Skor Review =
AVERAGE ( fact_pesanan[skor_review] )

Persen Review Buruk =
VAR JumlahBuruk =
    CALCULATE (
        COUNT ( fact_pesanan[skor_review] ),
        fact_pesanan[skor_review] <= 2
    )
VAR JumlahReview =
    COUNT ( fact_pesanan[skor_review] )
RETURN
    DIVIDE ( JumlahBuruk, JumlahReview ) * 100

Persen Tepat Waktu =
VAR JumlahTepat =
    CALCULATE (
        COUNT ( fact_pesanan[terlambat_flag] ),
        fact_pesanan[terlambat_flag] = 0
    )
VAR JumlahAdaFlag =
    COUNT ( fact_pesanan[terlambat_flag] )
RETURN
    DIVIDE ( JumlahTepat, JumlahAdaFlag ) * 100

Persen Terlambat =
VAR JumlahTelat =
    CALCULATE (
        COUNT ( fact_pesanan[terlambat_flag] ),
        fact_pesanan[terlambat_flag] = 1
    )
VAR JumlahAdaFlag =
    COUNT ( fact_pesanan[terlambat_flag] )
RETURN
    DIVIDE ( JumlahTelat, JumlahAdaFlag ) * 100

Jumlah Pelanggan Unik =
DISTINCTCOUNT ( fact_pesanan[customer_unique_id] )

Pelanggan Repeat =
SUMX (
    VALUES ( fact_pesanan[customer_unique_id] ),
    IF ( CALCULATE ( COUNTROWS ( fact_pesanan ) ) > 1, 1, 0 )
)

Persen Repeat Purchase =
DIVIDE ( [Pelanggan Repeat], [Jumlah Pelanggan Unik] ) * 100

Rata-rata Revenue Bulanan 2017 =
DIVIDE (
    CALCULATE ( [Total Revenue Produk], dim_tanggal[tahun] = 2017 ),
    12
)

Rata-rata Revenue Bulanan Jan Agu 2018 =
DIVIDE (
    CALCULATE (
        [Total Revenue Produk],
        dim_tanggal[tahun] = 2018,
        dim_tanggal[bulan] <= 8
    ),
    8
)

Pertumbuhan Revenue Persen =
DIVIDE (
    [Rata-rata Revenue Bulanan Jan Agu 2018] - [Rata-rata Revenue Bulanan 2017],
    [Rata-rata Revenue Bulanan 2017]
) * 100
```

Catatan measure pesanan:

1. `Total Revenue Produk` dan `Total Pesanan Delivered` sudah mengunci status `delivered` di dalam definisinya, jadi slicer status tidak akan mengubah definisi revenue. Measure lain (skor review, review buruk, repeat purchase) TIDAK dikunci: angka mereka mengikuti konteks filter, dan tabel verifikasi di atas menuliskan konteksnya secara eksplisit.
2. `Rata-rata Hari Pengiriman` aman tanpa filter status karena `hari_pengiriman` hanya terisi untuk order yang benar-benar diterima pelanggan.
3. `Persen Review Buruk` memakai `COUNT` (menghitung nilai yang tidak kosong), jadi order tanpa review tidak masuk pembilang maupun penyebut.

## Measures — ITEM PESANAN (tabel `fact_item_pesanan`)

```dax
Total Item Terjual =
COUNTROWS ( fact_item_pesanan )

Revenue Item Delivered =
CALCULATE (
    SUM ( fact_item_pesanan[price] ),
    dim_status[order_status] = "delivered"
)

Total Ongkir Delivered =
CALCULATE (
    SUM ( fact_item_pesanan[freight_value] ),
    dim_status[order_status] = "delivered"
)

Rata-rata Harga Item =
AVERAGE ( fact_item_pesanan[price] )

Persen Share Revenue Kategori =
DIVIDE (
    [Revenue Item Delivered],
    CALCULATE ( [Revenue Item Delivered], ALL ( dim_kategori[kategori] ) )
) * 100
```

Catatan measure item:

1. `Revenue Item Delivered` HARUS menghasilkan angka yang sama dengan `Total Revenue Produk` (13.221.498,11 BRL) pada konteks tanpa filter kategori dan state. Ini uji silang utama model: bila keduanya berbeda, ada relasi yang salah.
2. Pakai measure item HANYA untuk visual per kategori. Untuk KPI total revenue di halaman ringkasan, pakai `Total Revenue Produk` dari `fact_pesanan`.
3. `fact_item_pesanan` tidak punya kolom review, jadi tidak ada measure skor atau review buruk per kategori di kit ini. Analisis kategori vs review di proyek asli dihitung per order per kategori di notebook, dan tidak dipaksakan masuk ke model bintang ini.

## Aturan pakai

1. Satu visual = satu tabel fakta. Visual pesanan, pengiriman, review, dan retensi pakai measures PESANAN; visual kategori pakai measures ITEM PESANAN.
2. Jangan pernah menjumlahkan `total_pembayaran` lalu melabelinya revenue. Bila visual menampilkan pembayaran, labelnya harus "Total Pembayaran" dan satuannya BRL.
3. Slicer Tahun, State, dan Status boleh dipakai lintas halaman lewat dimensi, tetapi ingat: measure repeat purchase dan review buruk berubah nilainya mengikuti konteks. Angka acuan 3,1% dan 14,7% hanya berlaku pada konteks semua status dan semua tahun.
4. Uji tiap measure pada satu potongan kecil dulu sebelum membangun halaman penuh (contoh: tanpa filter apa pun, `Total Revenue Produk` harus 13.221.498,11 BRL dan `Revenue Item Delivered` harus sama persis).
5. Nama measure di file ini ditulis sebagai teks biasa tanpa tanda sama dengan di dalam nama dan tanpa kurung berisi tanda sama dengan; tanda sama dengan hanya muncul satu kali sebagai pemisah nama dan rumus DAX.

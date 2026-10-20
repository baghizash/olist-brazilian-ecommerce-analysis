# Analisis E Commerce Brasil : Dataset Publik Olist

Project portofolio data analyst: analisis end to end data transaksi
e commerce Brasil memakai SQL dan Python. Seluruh angka dihitung langsung
dari data, bukan diambil dari artikel atau sumber lain.

## Ringkasan

Dataset Olist mencatat 99.441 order dari 96.096 pelanggan unik dan
3.095 seller selama September 2016 sampai Oktober 2018. Analisis menjawab
tujuh pertanyaan bisnis: tren revenue, kategori produk, performa pengiriman,
geografi, konsentrasi bad review antar seller, pola pembayaran, dan
retensi pelanggan.

Temuan paling menonjol: revenue tumbuh 82% dari rata rata bulanan 2017
ke Januari sampai Agustus 2018; keterlambatan kirim adalah pendorong utama
review buruk; bad review tersebar merata antar seller sehingga ini masalah
platform bukan segelintir seller; dan retensi sangat rendah dengan repeat
purchase rate hanya 3,1%.

## Sumber Data dan Atribusi

* Dataset: Brazilian E Commerce Public Dataset by Olist
* Sumber: https://www.kaggle.com/datasets/olistbr/brazilian-ecommerce
* Lisensi: CC BY-NC-SA 4.0
* Atribusi: data disediakan oleh Olist, marketplace Brasil yang
  menghubungkan penjual kecil ke pelanggan di seluruh Brasil.

## Struktur Repo

```
.
├── analysis.ipynb              # notebook analisis utama (Bahasa Indonesia)
├── charts/                     # 12 chart PNG hasil analisis
├── data/
│   ├── olist.db                # database SQLite (dibuat lokal, tidak masuk git)
│   └── raw/
│       ├── olist_*_dataset.csv # 8 file CSV mentah (tidak masuk git)
│       └── category_translation.csv  # terjemahan kategori buatan sendiri
├── sql/
│   └── queries.sql             # query SQL utama dengan komentar Indonesia
├── scripts/
│   ├── load_to_sqlite.py       # load 8 CSV ke SQLite + verifikasi
│   └── build_notebook.py       # generator analysis.ipynb
├── requirements.txt
└── .gitignore
```

## Deskripsi Data

| Tabel | Baris | Isi |
|---|---|---|
| customers | 99.441 | data pelanggan dan lokasi |
| geolocation | 1.000.163 | koordinat per kode pos |
| order_items | 112.650 | item per order: harga, ongkir, seller |
| payments | 103.886 | pembayaran per order: tipe, cicilan |
| reviews | 99.224 | skor dan teks review |
| orders | 99.441 | status dan tanggal tiap order |
| products | 32.951 | katalog produk dan kategori |
| sellers | 3.095 | data seller dan lokasi |

Catatan: file reviews tercatat 104.719 baris teks, tetapi setelah parsing
CSV yang benar jumlah record logisnya 99.224, karena banyak teks review
mengandung baris baru di dalam tanda kutip. Angka 99.224 yang dipakai.

## Yang Dikerjakan

1. Load 8 file CSV ke SQLite (`data/olist.db`) memakai
   `scripts/load_to_sqlite.py`, lengkap dengan verifikasi jumlah baris
   tiap tabel dan index untuk join.
2. Membuat tabel terjemahan kategori Portugis ke Inggris
   (`data/raw/category_translation.csv`) karena file terjemahan resmi
   tidak tersedia di dataset.
3. Menjawab tujuh pertanyaan bisnis dengan query SQL asli di SQLite,
   diolah lanjut dengan pandas. Definisi tiap metrik ditulis di tiap
   section notebook.
4. Membuat 12 chart PNG konsisten (palet biru teal, 1200x720, dpi 120)
   di folder `charts/`.
5. Merangkai semuanya di `analysis.ipynb`: penjelasan, query SQL,
   output tabel, chart, dan insight per section.

## Temuan Kunci

Angka di bawah adalah hasil perhitungan langsung dari data.

1. **Tren**: total revenue 13,22 juta BRL dari 96.478 order delivered
   selama 23 bulan. Rata rata revenue bulanan naik dari 0,50 juta BRL
   pada 2017 menjadi 0,90 juta BRL pada Januari sampai Agustus 2018
   (tumbuh 82%). Puncak pada November 2017: 0,99 juta BRL, 7.289 order.
2. **Kategori**: dari 73 kategori, health beauty penyumbang revenue
   terbesar (1,23 juta BRL, 9,4% total). Revenue terkecil:
   insurance services (283 BRL, 2 order). Bad review rate tertinggi:
   mens fashion (22,9%, rata rata skor 3,8). Skor tertinggi:
   general interest books (4,5).
3. **Pengiriman**: 8,1% order tiba melewati estimasi. Rata rata waktu
   kirim 12,6 hari (median 10,2 hari). Review bintang 1 rata rata
   menunggu 21,3 hari, hampir dua kali lipat review bintang 5
   (10,7 hari). Keterlambatan adalah pendorong utama review buruk.
4. **Geografi**: 27 state tercatat, tetapi state SP sendiri menyumbang
   40.501 order (42,0%) dan 5,07 juta BRL (38,3%) revenue. Kota teratas:
   sao paulo (15.045 order).
5. **Seller**: bad review tidak terkonsentrasi. Dari 2.965 seller,
   350 seller punya bad review rate di atas 30%, tetapi hanya menampung
   9,7% order bad review. Sepuluh seller terburuk menampung 15,6%.
   Kesimpulan: ini masalah platform, bukan segelintir seller.
6. **Pembayaran**: 75,4% order memakai credit_card, disusul boleto
   19,9%. Sebanyak 51,5% order memakai cicilan lebih dari 1 kali;
   rata rata cicilan kartu kredit 3,6 kali vs boleto 1,0 kali.
7. **Retensi**: dari 96.096 pelanggan unik, hanya 3,1% yang belanja
   lebih dari 1 kali (rata rata 1,0 order per pelanggan). Repeat dalam
   90 hari setelah pembelian pertama hanya 1,1% sampai 1,5% di semua
   kohor 2017 T1 sampai 2018 T2, tanpa tren perbaikan.

## Definisi Metrik Penting

* **Revenue** = total kolom price dari order_items, tanpa freight_value
  (ongkir adalah biaya logistik, bukan revenue produk).
* Hanya order berstatus **delivered** yang dihitung untuk revenue,
  kategori, geografi, dan pembayaran, karena order berstatus lain tidak
  selesai. Order delivered mencakup 97,3% total price.
* **Bad review** = review dengan skor 1 atau 2.
* **Telat** = tanggal terima aktual melewati order_estimated_delivery_date.
* **Seller bermasalah** = bad review rate di atas 30%, dihitung dari
  distinct order supaya satu review tidak dihitung berulang.
* **Tipe pembayaran dominan** = tipe dengan payment_value terbesar
  per order.
* **Pelanggan** diidentifikasi dengan customer_unique_id, bukan
  customer_id, karena customer_id berbeda tiap order sedangkan
  customer_unique_id menunjuk orang yang sama.

## Cara Reproduce

Data mentah tidak ikut di push karena besar (total sekitar 120 MB,
file geolocation 61 MB). Langkah reproduce:

1. Download 8 file CSV dari
   https://www.kaggle.com/datasets/olistbr/brazilian-ecommerce
   lalu taruh di `data/raw/`.
2. Install dependensi (Python 3.12):
   `pip install -r requirements.txt`
3. Bangun database SQLite:
   `python scripts/load_to_sqlite.py`
4. (Opsional) Bangun ulang notebook dari generator:
   `python scripts/build_notebook.py`
5. Buka dan jalankan `analysis.ipynb` dari awal sampai akhir
   (restart kernel lalu run all). Semua chart akan dibuat ulang
   di folder `charts/`.

## Catatan Asumsi

* File `product_category_name_translation.csv` tidak tersedia di dataset,
  sehingga pemetaan Portugis ke Inggris dibuat sendiri berdasarkan
  pengetahuan bahasa dan disimpan di
  `data/raw/category_translation.csv`. File kecil ini ikut di git.
* Kategori `casa_conforto_2` dan `eletrodomesticos_2` diterjemahkan apa
  adanya dengan akhiran 2 karena arti pembedanya tidak diketahui.
* Review dihitung satu kali per order per kategori pada analisis kategori.
* Analisis kohor memakai jendela 90 hari setelah pembelian pertama
  supaya antar kohor bisa dibandingkan adil.
* Format angka memakai konvensi Indonesia (koma desimal, titik ribuan).

## Dashboard Power BI

Kit Power BI untuk project ini ada di folder `powerbi/`, siap dibangun
menjadi dashboard interaktif di Power BI Desktop:

* `fact_pesanan.csv` (1 baris per order) dan `fact_item_pesanan.csv`
  (1 baris per order item), dipisah per grain, plus dimensi
  `dim_tanggal.csv`, `dim_kategori.csv`, `dim_status.csv`, dan
  `dim_negara_bagian.csv`. CSV dibangun dari data mentah memakai
  `powerbi/build_kit_csv.py`.
* `measures_dax.md`: measures DAX lengkap dengan catatan level dan
  tabel verifikasi angka. Penting: revenue adalah total harga produk
  order delivered (13,22 juta BRL, tanpa ongkir); kolom total
  pembayaran di fakta adalah pembayaran termasuk ongkir dan bukan
  revenue.
* `dashboard_layout.md` dan `build_guide.md`: rancangan dan panduan
  membangun dashboard 4 halaman (16:9): (1) Ringkasan Eksekutif,
  (2) Kategori Produk, (3) Pengiriman dan Review, (4) Geografi,
  Retensi dan Metodologi. Pratinjau halaman 1 ada di
  `powerbi/dashboard_preview_halaman1.png`.

File `.pbix` dibangun lokal di Power BI Desktop (nama yang disarankan:
`Olist-Ecommerce-Analysis.pbix`) dan tidak disimpan di repo ini karena
GitHub tidak bisa menampilkan file `.pbix`; screenshot dashboard akan
ditambahkan setelah file `.pbix` selesai dibangun.

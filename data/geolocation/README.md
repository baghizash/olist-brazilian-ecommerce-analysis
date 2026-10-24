# Data Geolocation Olist per State

Folder ini berisi dataset geolocation Olist yang dipecah per state
(negara bagian Brasil), supaya dataset lengkapnya akhirnya bisa ikut
disimpan di repo ini.

## Kenapa dipecah

File aslinya, `olist_geolocation_dataset.csv`, berukuran sekitar 61 MB
dengan 1.000.163 baris. File sebesar itu ditolak oleh GitHub Contents API
yang dipakai untuk push ke repo ini, jadi selama ini file geolocation
menjadi satu satunya file raw yang tidak ikut masuk repo. Dengan dipecah
per state, file terbesar (SP) hanya sekitar 24 MB dan semua file bisa
di-push. File asli yang utuh dan belum dipecah sengaja TIDAK di-push.

## Isi

Satu file per kode UF di kolom `geolocation_state`, dengan nama
`geolocation_<UF>.csv`. Semua file memakai header dan format kolom yang
persis sama dengan file asli:

`geolocation_zip_code_prefix, geolocation_lat, geolocation_lng, geolocation_city, geolocation_state`

| File | Baris |
|---|---|
| geolocation_AC.csv | 1.301 |
| geolocation_AL.csv | 4.183 |
| geolocation_AM.csv | 2.432 |
| geolocation_AP.csv | 853 |
| geolocation_BA.csv | 36.045 |
| geolocation_CE.csv | 11.674 |
| geolocation_DF.csv | 12.986 |
| geolocation_ES.csv | 16.748 |
| geolocation_GO.csv | 20.139 |
| geolocation_MA.csv | 7.853 |
| geolocation_MG.csv | 126.336 |
| geolocation_MS.csv | 10.431 |
| geolocation_MT.csv | 12.031 |
| geolocation_PA.csv | 10.853 |
| geolocation_PB.csv | 5.538 |
| geolocation_PE.csv | 16.432 |
| geolocation_PI.csv | 4.549 |
| geolocation_PR.csv | 57.859 |
| geolocation_RJ.csv | 121.169 |
| geolocation_RN.csv | 5.041 |
| geolocation_RO.csv | 3.478 |
| geolocation_RR.csv | 646 |
| geolocation_RS.csv | 61.851 |
| geolocation_SC.csv | 38.328 |
| geolocation_SE.csv | 3.563 |
| geolocation_SP.csv | 404.268 |
| geolocation_TO.csv | 3.576 |
| **Total (27 file)** | **1.000.163** |

Total baris seluruh file pecahan adalah 1.000.163 baris, persis sama
dengan jumlah baris file aslinya.

## Verifikasi

Penggabungan semua file pecahan sudah diverifikasi terhadap file asli
dengan cara mengurutkan seluruh baris data dari kedua sisi lalu
membandingkan hash SHA-256 nya. Hasilnya identik
(`179c96c27bb80820a1ecfccf9df26529e3d665a3eb19afa6d36db2d3736afa85`),
artinya union file pecahan mereproduksi file asli baris demi baris,
tanpa ada baris yang hilang, berubah, atau dobel.

## Cara menggabungkan kembali

Satu baris pandas dari root repo:

```python
import pandas as pd, glob; pd.concat([pd.read_csv(f, dtype={"geolocation_zip_code_prefix": str}) for f in sorted(glob.glob("data/geolocation/geolocation_*.csv"))]).to_csv("olist_geolocation_dataset.csv", index=False)
```

Kolom `geolocation_zip_code_prefix` dibaca sebagai string supaya angka
nol di depan kode pos (misalnya `01037`) tidak hilang.

## Sumber

Dataset: Brazilian E Commerce Public Dataset by Olist,
https://www.kaggle.com/datasets/olistbr/brazilian-ecommerce
(Lisensi CC BY-NC-SA 4.0). File asli lokal yang dipecah:
`data/raw/olist_geolocation_dataset.csv` (disimpan lokal, tidak di-push).

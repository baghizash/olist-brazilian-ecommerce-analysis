#!/usr/bin/env python3
"""Build Portofolio-Analisis-Ecommerce-Olist.pptx (16:9, 10 slides, ID).

Redesign design-taste: Tema T4 (muted red, oat, pumpkin), varian Editorial.
Headline Liberation Serif bold, body dan angka Noto Sans.
Konten dan semua angka identik dengan deck lama (build_ppt_legacy.py).
"""
from pptx import Presentation
from pptx.util import Inches, Pt
from pptx.dml.color import RGBColor
from pptx.enum.text import PP_ALIGN
from pptx.enum.shapes import MSO_SHAPE
from pptx.oxml.ns import qn

GROUND = RGBColor(0xF1, 0xE9, 0xDA)    # oat
SURFACE = RGBColor(0xF8, 0xF2, 0xE5)   # permukaan terang
INK = RGBColor(0x33, 0x23, 0x1C)
RED = RGBColor(0xA3, 0x4A, 0x38)       # muted red, primary
PUMPKIN = RGBColor(0xDE, 0x7A, 0x2D)   # aksen
REDLT = RGBColor(0xC9, 0x7B, 0x63)     # red muda
MUTED = RGBColor(0x6E, 0x5B, 0x4D)     # teks sekunder
CREAM = RGBColor(0xE8, 0xDC, 0xC8)     # teks terang di atas red
WHITE = RGBColor(0xFF, 0xFF, 0xFF)

SERIF = "Liberation Serif"
SANS = "Noto Sans"
CHARTS = "/home/hatch/workspace/olist-ecommerce/charts"

prs = Presentation()
prs.slide_width = Inches(13.333)
prs.slide_height = Inches(7.5)
blank = prs.slide_layouts[6]


def solid_bg(slide, color):
    fill = slide.background.fill
    fill.solid()
    fill.fore_color.rgb = color


def rect(slide, x, y, w, h, color):
    sh = slide.shapes.add_shape(MSO_SHAPE.RECTANGLE, Inches(x), Inches(y),
                                Inches(w), Inches(h))
    sh.fill.solid()
    sh.fill.fore_color.rgb = color
    sh.line.fill.background()
    sh.shadow.inherit = False
    return sh


def textbox(slide, x, y, w, h):
    tx = slide.shapes.add_textbox(Inches(x), Inches(y), Inches(w), Inches(h))
    tf = tx.text_frame
    tf.word_wrap = True
    tf.margin_left = 0
    tf.margin_right = 0
    tf.margin_top = 0
    tf.margin_bottom = 0
    return tf


def add_par(tf, text, size, color, bold=False, italic=False, first=False,
            font=SANS, align=None, space_after=8, line=None):
    p = tf.paragraphs[0] if first else tf.add_paragraph()
    p.space_after = Pt(space_after)
    if line is not None:
        p.line_spacing = line
    if align is not None:
        p.alignment = align
    r = p.add_run()
    r.text = text
    r.font.size = Pt(size)
    r.font.bold = bold
    r.font.italic = italic
    r.font.name = font
    r.font.color.rgb = color
    return p


def add_bullet(tf, text, size=16, first=False, color=INK, space_after=12):
    p = add_par(tf, text, size, color, first=first, space_after=space_after,
                line=1.12)
    pPr = p._p.get_or_add_pPr()
    bu = pPr.makeelement(qn("a:buChar"), {"char": "•"})
    pPr.append(bu)
    pPr.set("marL", "171450")
    pPr.set("indent", "-171450")
    return p


def bullets(slide, x, y, w, h, items, size=16):
    tf = textbox(slide, x, y, w, h)
    for i, b in enumerate(items):
        add_bullet(tf, b, size=size, first=(i == 0))
    return tf


def title_block(slide, text):
    tf = textbox(slide, 0.7, 0.42, 11.9, 1.0)
    add_par(tf, text, 32, INK, bold=True, first=True, font=SERIF)
    rect(slide, 0.72, 1.34, 1.5, 0.07, PUMPKIN)


def caption(slide, x, y, w, text):
    tf = textbox(slide, x, y, w, 0.4)
    add_par(tf, text, 12, MUTED, italic=True, first=True, align=PP_ALIGN.CENTER)


def chart_pic(slide, name, x, y, w):
    h = w * 0.6
    slide.shapes.add_picture(f"{CHARTS}/{name}.png", Inches(x), Inches(y),
                             width=Inches(w), height=Inches(h))
    return h


# ---------- Slide 1: Cover (Asymmetric Split + Data Hero) ----------
s = prs.slides.add_slide(blank)
solid_bg(s, GROUND)
rect(s, 8.1, 0, 5.233, 7.5, RED)
rect(s, 8.62, 1.5, 0.55, 0.09, PUMPKIN)
tf = textbox(s, 8.62, 1.95, 4.3, 1.9)
add_par(tf, "13,22", 88, WHITE, bold=True, first=True, space_after=0)
tf = textbox(s, 8.62, 3.85, 4.3, 1.6)
add_par(tf, "juta BRL", 24, GROUND, bold=True, first=True, space_after=4)
add_par(tf, "total revenue dari 96.478 order delivered", 14, CREAM,
        space_after=0, line=1.15)
tf = textbox(s, 0.7, 1.55, 7.0, 2.5)
add_par(tf, "Analisis Ecommerce Brazil dengan SQL dan Python", 40, INK,
        bold=True, first=True, font=SERIF, line=1.08, space_after=0)
tf = textbox(s, 0.7, 4.3, 6.9, 0.8)
add_par(tf, "Studi Kasus: Brazilian Ecommerce Public Dataset by Olist", 17,
        MUTED, first=True, line=1.2)
rect(s, 0.72, 5.55, 1.5, 0.07, RED)
tf = textbox(s, 0.7, 5.8, 7.0, 1.2)
add_par(tf, "BAGHIZ ASSHIDDIQIE ARASYA", 20, RED, bold=True, first=True,
        space_after=4)
add_par(tf, "Data Analyst Portfolio Project", 13, MUTED, space_after=0)

# ---------- Slide 2: Latar Belakang ----------
s = prs.slides.add_slide(blank)
solid_bg(s, GROUND)
title_block(s, "Latar Belakang")
bullets(s, 0.7, 1.75, 7.9, 5.2, [
    "Brazilian Ecommerce Public Dataset by Olist: 99.441 order dari 9 tabel relasional",
    "Periode data September 2016 sampai Agustus 2018, fokus analisis pada order dengan status delivered",
    "Tujuan: menjawab 7 pertanyaan bisnis seputar revenue, kategori, pengiriman, seller, geografi, pembayaran, dan retensi pelanggan",
    "Hasil akhir: rekomendasi bisnis berbasis bukti untuk pertumbuhan marketplace",
], size=16.5)
rect(s, 8.95, 1.75, 3.68, 4.85, SURFACE)
rect(s, 8.95, 1.75, 3.68, 0.09, PUMPKIN)
tf = textbox(s, 9.3, 2.1, 3.0, 1.5)
add_par(tf, "7", 64, RED, bold=True, first=True, space_after=0)
tf = textbox(s, 9.3, 3.45, 3.0, 2.9)
add_par(tf, "pertanyaan bisnis dijawab dalam analisis ini", 15, INK,
        bold=True, first=True, line=1.15, space_after=14)
add_par(tf, "99.441 order", 15, INK, space_after=2)
add_par(tf, "9 tabel relasional", 15, INK, space_after=2)
add_par(tf, "Fokus: order delivered", 15, INK, space_after=0)

# ---------- Slide 3: Data dan Metodologi ----------
s = prs.slides.add_slide(blank)
solid_bg(s, GROUND)
title_block(s, "Data dan Metodologi")
bullets(s, 0.7, 1.75, 7.55, 5.2, [
    "File CSV dimuat ke SQLite, lalu dianalisis dengan query SQL berisi JOIN antar tabel dan pandas untuk agregasi lanjutan",
    "Revenue didefinisikan sebagai total harga barang tanpa ongkos kirim, dihitung hanya dari order berstatus delivered",
    "Bad review didefinisikan sebagai ulasan dengan skor 1 atau 2 dari skala 1 sampai 5",
    "Repeat purchase rate adalah persentase pelanggan unik yang berbelanja lebih dari satu kali",
], size=16.5)
tf = textbox(s, 8.6, 1.7, 4.03, 0.5)
add_par(tf, "Alur Analisis", 18, INK, bold=True, first=True, font=SERIF)
steps = ["File CSV", "SQLite", "Query SQL dan pandas", "Rekomendasi berbasis bukti"]
sy = 2.3
for i, st in enumerate(steps):
    rect(s, 8.6, sy, 4.03, 0.72, SURFACE)
    rect(s, 8.6, sy, 0.09, 0.72, RED if i < 3 else PUMPKIN)
    tf = textbox(s, 8.9, sy + 0.19, 3.6, 0.4)
    add_par(tf, st, 14.5, INK, bold=True, first=True, space_after=0)
    if i < 3:
        tf = textbox(s, 8.6, sy + 0.74, 4.03, 0.3)
        add_par(tf, "↓", 13, PUMPKIN, bold=True, first=True,
                align=PP_ALIGN.CENTER, space_after=0)
    sy += 1.06

# ---------- Slide 4: Temuan 1, Tren Revenue ----------
s = prs.slides.add_slide(blank)
solid_bg(s, GROUND)
title_block(s, "Temuan 1: Tren Revenue Terus Tumbuh")
tf = textbox(s, 0.7, 1.62, 4.5, 1.15)
add_par(tf, "+82%", 52, RED, bold=True, first=True, space_after=0)
tf = textbox(s, 0.7, 2.72, 4.5, 0.75)
add_par(tf, "pertumbuhan rata rata revenue bulanan, 2017 ke 2018", 13,
        MUTED, first=True, line=1.15, space_after=0)
bullets(s, 0.7, 3.6, 4.5, 3.5, [
    "Total revenue 13.22 juta BRL dari 96.478 order delivered selama 23 bulan",
    "Rata rata revenue bulanan naik dari 0.50 juta BRL pada 2017 menjadi 0.90 juta BRL pada Januari sampai Agustus 2018, tumbuh 82 persen",
    "Puncak terjadi pada November 2017 dengan 0.99 juta BRL dan 7.289 order; pada November 2016 belum ada order sama sekali",
], size=14.5)
h = chart_pic(s, "01_tren_revenue_order", 5.5, 1.62, 7.13)
caption(s, 5.5, 1.62 + h + 0.12, 7.13, "Tren revenue dan jumlah order bulanan")

# ---------- Slide 5: Temuan 2, Kategori ----------
s = prs.slides.add_slide(blank)
solid_bg(s, GROUND)
title_block(s, "Temuan 2: Kinerja Kategori Produk")
h = chart_pic(s, "04_kategori_skor_vs_bad_rate", 0.7, 1.7, 6.9)
caption(s, 0.7, 1.7 + h + 0.12, 6.9, "Skor ulasan dan bad review rate per kategori")
bullets(s, 7.95, 1.75, 4.68, 5.2, [
    "Dari 73 kategori, health beauty memimpin revenue 1.23 juta BRL atau 9.4 persen dari total",
    "Kategori terkecil insurance services hanya 283 BRL dari 2 order",
    "Bad review rate tertinggi ada di mens fashion: 22.9 persen dengan skor rata rata 3.8",
    "Skor ulasan tertinggi general interest books 4.5, terendah office furniture 3.6",
], size=15.5)

# ---------- Slide 6: Temuan 3, Pengiriman ----------
s = prs.slides.add_slide(blank)
solid_bg(s, GROUND)
title_block(s, "Temuan 3: Pengiriman Pendorong Review Buruk")
bullets(s, 0.7, 1.7, 5.9, 3.4, [
    "Sebesar 8.1 persen order tiba melewati estimasi, dengan waktu kirim rata rata 12.6 hari dan median 10.2 hari",
    "Pelanggan pemberi bintang 1 menunggu 21.3 hari, hampir dua kali lipat dibanding pemberi bintang 5 yang hanya 10.7 hari",
    "Pola ini konsisten: semakin lama waktu kirim, semakin rendah skor ulasan yang diberikan",
], size=15.5)
h = chart_pic(s, "06_waktu_kirim_per_skor", 6.9, 1.62, 5.73)
caption(s, 6.9, 1.62 + h + 0.1, 5.73, "Rata rata waktu kirim per skor ulasan")
rect(s, 0.7, 5.52, 11.93, 1.5, SURFACE)
rect(s, 0.7, 5.52, 11.93, 0.07, RED)
tf = textbox(s, 1.15, 5.82, 5.2, 1.15)
add_par(tf, "21,3 hari", 38, RED, bold=True, first=True, space_after=2)
add_par(tf, "rata rata tunggu pelanggan bintang 1", 13, MUTED, space_after=0)
rect(s, 6.65, 5.87, 0.03, 0.85, REDLT)
tf = textbox(s, 7.05, 5.82, 5.2, 1.15)
add_par(tf, "10,7 hari", 38, RED, bold=True, first=True, space_after=2)
add_par(tf, "rata rata tunggu pelanggan bintang 5", 13, MUTED, space_after=0)

# ---------- Slide 7: Temuan 4, Seller dan Geografi ----------
s = prs.slides.add_slide(blank)
solid_bg(s, GROUND)
title_block(s, "Temuan 4: Masalah Platform, Bukan Segelintir Seller")
bullets(s, 0.7, 1.7, 6.2, 5.3, [
    "Dari 2.965 seller, 350 seller memiliki bad review rate di atas 30 persen namun hanya menampung 9.7 persen dari seluruh bad review",
    "Bahkan 10 seller terburuk hanya menampung 15.6 persen bad review: masalah tersebar di seluruh platform",
    "Geografi sangat terkonsentrasi: Sao Paulo mencatat 40.501 order atau 42.0 persen, dengan revenue 5.07 juta BRL atau 38.3 persen",
    "Kota dengan order terbanyak adalah sao paulo dengan 15.045 order",
], size=15.5)
h = chart_pic(s, "09_konsentrasi_bad_review_seller", 7.2, 1.7, 5.43)
caption(s, 7.2, 1.7 + h + 0.12, 5.43, "Konsentrasi bad review di antara seller")

# ---------- Slide 8: Temuan 5, Pembayaran dan Retensi ----------
s = prs.slides.add_slide(blank)
solid_bg(s, GROUND)
title_block(s, "Temuan 5: Cicilan Dominan, Retensi Rendah")
h = chart_pic(s, "10_tipe_pembayaran", 0.7, 1.85, 5.9)
caption(s, 0.7, 1.85 + h + 0.12, 5.9, "Distribusi tipe pembayaran")
tf = textbox(s, 6.95, 1.66, 5.68, 1.05)
add_par(tf, "3,1%", 46, RED, bold=True, first=True, space_after=0)
tf = textbox(s, 6.95, 2.68, 5.68, 0.45)
add_par(tf, "repeat purchase rate dari 96.096 pelanggan unik", 13, MUTED,
        first=True, space_after=0)
bullets(s, 6.95, 3.25, 5.68, 3.8, [
    "Kartu kredit dipakai di 75.4 persen order, boleto di 19.9 persen",
    "Sebanyak 51.5 persen order memakai cicilan lebih dari 1 kali; rata rata cicilan kartu kredit 3.6 kali dibanding boleto 1.0 kali",
    "Dari 96.096 pelanggan unik, repeat purchase rate hanya 3.1 persen",
    "Retensi kohor 90 hari stabil di 1.1 sampai 1.5 persen tanpa tren perbaikan",
], size=15)

# ---------- Slide 9: Rekomendasi (grid 2x2) ----------
s = prs.slides.add_slide(blank)
solid_bg(s, GROUND)
title_block(s, "Rekomendasi Bisnis")
recs = [
    "Perbaiki SLA pengiriman untuk kategori bulky dan fashion seperti office furniture dan mens fashion, karena keterlambatan adalah pendorong utama review buruk",
    "Bangun program retensi pelanggan: repeat purchase hanya 3.1 persen dan retensi kohor stagnan di 1.1 sampai 1.5 persen",
    "Diversifikasi pasar di luar Sao Paulo yang kini menampung 42.0 persen order, untuk mengurangi risiko konsentrasi geografis",
    "Dorong pembayaran kartu kredit dengan cicilan karena 51.5 persen order sudah terbiasa mencicil, sekaligus pantau kategori berisiko tinggi",
]
pos = [(0.7, 1.7), (6.85, 1.7), (0.7, 4.35), (6.85, 4.35)]
for (x, y), txt in zip(pos, recs):
    rect(s, x, y, 5.78, 2.45, SURFACE)
    rect(s, x, y, 0.09, 2.45, RED)
    tf = textbox(s, x + 0.38, y + 0.3, 5.1, 1.9)
    add_par(tf, txt, 15, INK, first=True, line=1.18, space_after=0)

# ---------- Slide 10: Penutup (Designed Close) ----------
s = prs.slides.add_slide(blank)
solid_bg(s, RED)
tf = textbox(s, 0.9, 0.65, 11.5, 0.9)
add_par(tf, "Penutup", 34, WHITE, bold=True, first=True, font=SERIF)
tf = textbox(s, 0.9, 1.85, 11.5, 1.3)
add_par(tf, "Revenue tumbuh 82 persen dalam setahun, namun pertumbuhan dibayangi pengiriman lambat, retensi rendah, dan konsentrasi di satu wilayah",
        21, GROUND, first=True, font=SERIF, line=1.2, space_after=0)
tf = textbox(s, 0.9, 3.35, 11.5, 1.2)
add_par(tf, "Analisis SQL dan Python atas 99.441 order ini menghasilkan 4 rekomendasi prioritas: SLA pengiriman, program retensi, diversifikasi geografis, dan optimalisasi pembayaran",
        15.5, CREAM, first=True, line=1.25, space_after=0)
rect(s, 0.92, 4.95, 1.5, 0.07, PUMPKIN)
tf = textbox(s, 0.9, 5.2, 11.5, 0.7)
add_par(tf, "BAGHIZ ASSHIDDIQIE ARASYA", 26, WHITE, bold=True, first=True,
        space_after=0)
tf = textbox(s, 0.9, 6.0, 11.5, 0.5)
add_par(tf, "github.com/baghizash/olist-brazilian-ecommerce-analysis", 15,
        GROUND, bold=True, first=True, space_after=0)
tf = textbox(s, 0.9, 6.55, 11.5, 0.4)
add_par(tf, "Dataset: Brazilian Ecommerce Public Dataset by Olist, lisensi CC BY NC SA 4.0",
        12, CREAM, first=True, space_after=0)

out = "/home/hatch/workspace/your_files/Portofolio-Analisis-Ecommerce-Olist.pptx"
prs.save(out)
print("saved:", out, "| slides:", len(prs.slides._sldIdLst))

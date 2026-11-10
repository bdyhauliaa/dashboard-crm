# CRM Dashboard — Olist Brazilian E-Commerce

Dashboard Customer Relationship Management berbasis **Streamlit + Plotly** untuk menjawab enam pertanyaan bisnis: pelanggan terbaik, asal pelanggan, nilai transaksi, potensi churn, loyalitas, dan strategi pemasaran.

## Cara Menjalankan

```bash
pip install -r requirements.txt
python src/prepare_data.py     # membangun data olahan (sekali saja)
streamlit run app.py
```

Dashboard terbuka otomatis di `http://localhost:8501`.

## Deploy (Streamlit Community Cloud)

File yang perlu di-commit: `app.py`, `ui.py`, `requirements.txt`, `README.md`, `data/data_processed/`, `assets/`, dan `.streamlit/config.toml`. Folder `data/raw/` tidak ikut di-commit (lihat `.gitignore`).

1. Push project ke repository GitHub.
2. Buka [share.streamlit.io](https://share.streamlit.io), pilih **New app**.
3. Pilih repository, branch `main`, dan main file `app.py`.
4. Deploy, lalu cek log build dan tampilan aplikasi.

## Struktur Proyek

```
Tugas 1/
├── data/
│   ├── raw/                    # 9 CSV Olist (mentah, tidak diubah)
│   └── data_processed/         # output pipeline
│       ├── master_orders.parquet
│       ├── customers_rfm.parquet
│       ├── cohort_retention.parquet
│       ├── geo_agg.parquet
│       └── kpi_summary.json
├── assets/
│   └── brazil_states.geojson   # peta choropleth Brazil (offline)
├── src/prepare_data.py         # ETL + RFM + cohort
├── ui.py                       # design system & komponen UI reusable
├── app.py                      # dashboard 3 sheet
└── requirements.txt
```

## Metodologi

- **Basis revenue**: order berstatus `delivered`, `payment_value` diagregasi per order agar tidak double-count.
- **Snapshot date**: 2018-10-18 (hari setelah transaksi terakhir).
- **RFM** per `customer_unique_id`:
  - Recency = hari sejak pembelian terakhir
  - Frequency = jumlah order unik
  - Monetary = total pembayaran
  - Skor 1–5 berbasis kuantil; segmen: Champions, Loyal, Potensial Loyal, Pelanggan Baru, Perlu Perhatian, Tidak Boleh Hilang, Berisiko, Hibernasi, Hilang.
- **CLV**: `est_annual_value = AOV × (frekuensi / tenure bulan) × 12`.
- **Churn**: `recency > P75 (395 hari)` **dan** `frekuensi ≤ 2`.
- **Cohort retention**: dikelompokkan berdasarkan bulan pembelian pertama.

## Isi Dashboard (3 Sheet)

1. **Ringkasan & Asal Pelanggan** — 6 KPI card, tren revenue bulanan, choropleth peta Brazil per state, top 10 kota, revenue per state.
2. **Pelanggan Terbaik & Nilai Transaksi** — 20 pelanggan teratas, kurva Pareto, distribusi monetary, revenue per segmen, kategori produk, metode pembayaran, cicilan.
3. **Churn, Loyalitas & Strategi** — segmen RFM, distribusi recency, daftar pelanggan berisiko + nilai terancam, cohort retention, repeat vs one-time, review vs keterlambatan, matriks strategi per segmen.

Filter berada di card horizontal di atas konten: rentang tanggal, state, kategori produk, segmen RFM.

## Design System (Financial Green)

Redesign UI menggunakan tema **Financial Green** dengan komponen reusable di `ui.py`:

| Token | Warna |
|---|---|
| Dark Green | `#14532D` |
| Green | `#16A34A` |
| Mint Green | `#A7DDB5` |
| Light Green | `#DCFCE7` |
| Background | `#F1F8F2` |
| Text Primary | `#1F2937` |
| Text Secondary | `#64748B` |

- Font **Inter** (fallback system font), card putih radius 16px, border mint, shadow halus.
- Header hero dark green dengan judul terpusat; kata “Analytics” disorot mint.
- KPI card custom dengan ikon SVG, nilai besar, badge delta MoM.
- Chart card reusable (`panel`/`chart_card`) dengan judul + subtitle dan Plotly theme hijau.
- Tabel HTML custom dengan chip segmen/status dan highlight nilai penting.
- Tab berbentuk pill nav, responsif (stack otomatis di layar kecil).
- Peta choropleth memakai GeoJSON lokal sehingga tetap berjalan offline.

## Ringkasan Insight

| Metrik | Nilai |
|---|---|
| Total revenue (delivered) | R$ 15.422.462 |
| Order delivered | 96.478 |
| Pelanggan unik | 93.358 |
| AOV | R$ 159,86 |
| Repeat rate | 3,0% |
| Rating rata-rata | 4,16 / 5 |
| Pengiriman terlambat | 6,8% |
| Pelanggan berpotensi churn | 23.227 (24,9%) |
| Revenue at risk | R$ 3.807.015 |

**Temuan utama**

- **Konsentrasi revenue ekstrem**: 20 pelanggan teratas menyumbang 0,72% revenue, dan 80% revenue berasal dari sebagian kecil pelanggan (kurva Pareto sangat curam).
- **Dominasi wilayah**: São Paulo 37,4% revenue, disusul Rio de Janeiro 13,3% dan Minas Gerais 11,8% — fokus ekspansi tetap di Southeast Brazil.
- **Kategori teratas**: health_beauty (9,2%), watches_gifts (8,2%), bed_bath_table (8,0%).
- **Pembayaran**: credit card 78,6% (dominan cicilan), boleto 18,0%.
- **Loyalitas rendah**: hanya 3,0% pelanggan repeat; retention bulan ke-1 cohort rata-rata 5,5%. Model bisnis masih sangat akuisisi-driven.
- **Keterlambatan merusak kepuasan**: review 4,29 untuk pengiriman tepat waktu vs 2,27 untuk terlambat.
- **Nilai terancam**: segmen Berisiko + Tidak Boleh Hilang menyimpan ±24% revenue historis yang perlu di-win-back.

## Strategi Pemasaran

| Segmen | Fokus |
|---|---|
| Champions | Loyalty tier/VIP, early sale, bundling premium |
| Loyal | Upsell/cross-sell, poin reward |
| Potensial Loyal | Dorong transaksi ke-3, rekomendasi personal |
| Pelanggan Baru | Onboarding + voucher pembelian kedua |
| Perlu Perhatian | Reminder + diskon terbatas waktu |
| Tidak Boleh Hilang | Win-back personal bernominal besar |
| Berisiko | Kampanye reaktivasi email/WhatsApp |
| Hibernasi / Hilang | Reaktivasi massal hemat biaya |

## Catatan Data

- Data September–Oktober 2018 tidak lengkap; tren bulanan dipotong pada bulan dengan ≥50 order.
- Pelanggan tanpa order `delivered` tidak masuk perhitungan RFM.
- Filter tanggal hanya memengaruhi grafik level order; RFM dihitung dari seluruh riwayat pelanggan (filter state/kategori/segmen tetap berlaku).

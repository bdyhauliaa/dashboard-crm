from __future__ import annotations

import html
import json
from pathlib import Path

import numpy as np
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import streamlit as st

from ui import (
    DARK_GREEN,
    GREEN,
    GREEN_CONTINUOUS,
    GREEN_HEATMAP,
    GREEN_SEQ,
    LIGHT_GREEN,
    MINT,
    WHITE,
    chart_card,
    chip,
    inject_css,
    kpi_row,
    muted,
    page_header,
    panel,
    render_table,
    section_header,
    segment_chip,
    strong,
    theme,
)

BASE = Path(__file__).resolve().parent
OUT = BASE / "data" / "data_processed"
GEOJSON_PATH = BASE / "assets" / "brazil_states.geojson"
BRAZIL_GEO = (
    json.loads(GEOJSON_PATH.read_text(encoding="utf-8"))
    if GEOJSON_PATH.exists()
    else None
)

SEGMENT_ORDER = [
    "Champions",
    "Loyal",
    "Potensial Loyal",
    "Pelanggan Baru",
    "Perlu Perhatian",
    "Tidak Boleh Hilang",
    "Berisiko",
    "Hibernasi",
    "Hilang",
]

SEGMENT_COLORS = {
    "Champions": "#14532D",
    "Loyal": "#15803D",
    "Potensial Loyal": "#16A34A",
    "Pelanggan Baru": "#22C55E",
    "Perlu Perhatian": "#84CC16",
    "Tidak Boleh Hilang": "#CA8A04",
    "Berisiko": "#D97706",
    "Hibernasi": "#EA580C",
    "Hilang": "#B91C1C",
}

STRATEGI = [
    ("Champions", "Pembelian terakhir, frekuensi & nilai tertinggi", "Program VIP/loyalty tier, akses early sale, bundling produk premium", "Email personal + WhatsApp", "Retention >90%, AOV +10%"),
    ("Loyal", "Sering bertransaksi, nilai tinggi", "Upsell & cross-sell kategori terkait, poin reward", "Email + push notification", "Frekuensi +15%"),
    ("Potensial Loyal", "Baru mulai repeat, nilai menengah", "Penawaran pembelian ke-3, rekomendasi personal", "Email + retargeting ads", "Repeat rate +20%"),
    ("Pelanggan Baru", "Baru 1 transaksi, recency rendah", "Onboarding, voucher pembelian kedua, konten edukasi", "Email welcome + push", "Konversi ke-2 >25%"),
    ("Perlu Perhatian", "Recency menengah, mulai jarang", "Reminder keranjang, diskon terbatas waktu", "Retargeting + SMS", "Reaktivasi 15%"),
    ("Tidak Boleh Hilang", "Dulu bernilai tinggi, kini pasif", "Win-back personal, voucher nominal besar, survey kepuasan", "Account manager + telepon", "Reaktivasi 20%"),
    ("Berisiko", "Frekuensi cukup tapi lama tidak aktif", "Kampanye win-back, penawaran eksklusif", "Email + WhatsApp", "Reaktivasi 15%"),
    ("Hibernasi", "Jarang & sudah lama tidak aktif", "Diskon reaktivasi massal, produk entry-level", "Email blast + ads", "Reaktivasi 8%"),
    ("Hilang", "Recency & frekuensi terendah", "Kampanye reaktivasi massal / hentikan biaya akuisisi", "Email blast", "Reaktivasi 3%"),
]


def rp(value: float) -> str:
    return f"R$ {value:,.0f}".replace(",", ".")


def num(value: float) -> str:
    return f"{value:,.0f}".replace(",", ".")


def compact_rp(value: float) -> str:
    if value >= 1_000_000:
        text = f"{value / 1_000_000:.1f} jt"
    elif value >= 1_000:
        text = f"{value / 1_000:.0f} rb"
    else:
        text = f"{value:.0f}"
    return "R$ " + text.replace(".", ",")


@st.cache_data
def load_all():
    master = pd.read_parquet(OUT / "master_orders.parquet")
    rfm = pd.read_parquet(OUT / "customers_rfm.parquet")
    cohort = pd.read_parquet(OUT / "cohort_retention.parquet")
    kpi = json.loads((OUT / "kpi_summary.json").read_text(encoding="utf-8"))
    return master, rfm, cohort, kpi


st.set_page_config(
    page_title="CRM Analytics Dashboard - Olist",
    layout="wide",
)
inject_css()

if not (OUT / "master_orders.parquet").exists():
    st.error("Data olahan belum ada. Jalankan dulu: `python src/prepare_data.py`")
    st.stop()

master, rfm, cohort, kpi = load_all()

page_header()

# ----------------------------- Filter card -----------------------------
min_d = master["order_purchase_timestamp"].min().date()
max_d = master["order_purchase_timestamp"].max().date()
states = sorted(master["customer_state"].dropna().unique().tolist())
cats = sorted(master["top_category"].dropna().unique().tolist())
segments = [s for s in SEGMENT_ORDER if s in set(rfm["segment"].astype(str))]

with st.container():
    st.markdown(
        '<div class="chart-head"><span class="card-marker"></span><h3>Filter Data</h3></div>',
        unsafe_allow_html=True,
    )
    f1, f2, f3, f4 = st.columns([1.25, 1, 1, 1])
    with f1:
        date_range = st.date_input(
            "Rentang tanggal pembelian",
            value=(min_d, max_d),
            min_value=min_d,
            max_value=max_d,
        )
    with f2:
        sel_states = st.multiselect("State pelanggan", states, placeholder="Semua state")
    with f3:
        sel_cats = st.multiselect("Kategori produk", cats, placeholder="Semua kategori")
    with f4:
        sel_segments = st.multiselect("Segmen RFM", segments, placeholder="Semua segmen")

if isinstance(date_range, (tuple, list)):
    start = pd.Timestamp(date_range[0])
    end = pd.Timestamp(date_range[-1]) + pd.Timedelta(days=1)
else:
    start = pd.Timestamp(date_range)
    end = pd.Timestamp(date_range) + pd.Timedelta(days=1)

m = master[
    (master["order_purchase_timestamp"] >= start)
    & (master["order_purchase_timestamp"] < end)
]
if sel_states:
    m = m[m["customer_state"].isin(sel_states)]
if sel_cats:
    m = m[m["top_category"].isin(sel_cats)]

r = rfm.copy()
if sel_states:
    r = r[r["customer_state"].isin(sel_states)]
if sel_cats:
    r = r[r["main_category"].isin(sel_cats)]
if sel_segments:
    r = r[r["segment"].astype(str).isin(sel_segments)]

if m.empty:
    st.warning("Tidak ada order pada kombinasi filter ini.")
    st.stop()

d = m[m["is_delivered"]]
if d.empty:
    st.warning("Tidak ada order berstatus delivered pada kombinasi filter ini.")
    st.stop()

tabs = st.tabs(
    [
        "Ringkasan & Asal Pelanggan",
        "Pelanggan Terbaik & Nilai Transaksi",
        "Churn, Loyalitas & Strategi",
    ]
)

# =============================== TAB 1 ====================================
with tabs[0]:
    monthly_all = (
        d.groupby(d["order_purchase_timestamp"].dt.to_period("M"))
        .agg(revenue=("payment_value", "sum"), orders=("order_id", "nunique"))
        .reset_index()
    )
    monthly_all["month"] = monthly_all["order_purchase_timestamp"].dt.to_timestamp()
    monthly = monthly_all[monthly_all["orders"] >= 50]

    mom_revenue = mom_orders = None
    if len(monthly) >= 2:
        last, prev = monthly.iloc[-1], monthly.iloc[-2]
        if prev["revenue"]:
            mom_revenue = (last["revenue"] / prev["revenue"] - 1) * 100
        if prev["orders"]:
            mom_orders = (last["orders"] / prev["orders"] - 1) * 100

    kpi_row(
        [
            {
                "icon": "wallet",
                "label": "Total Revenue",
                "value": compact_rp(d["payment_value"].sum()),
                "note": "Order delivered",
                "delta": mom_revenue,
            },
            {
                "icon": "cart",
                "label": "Total Order",
                "value": num(d["order_id"].nunique()),
                "note": "Order unik",
                "delta": mom_orders,
            },
            {
                "icon": "users",
                "label": "Pelanggan",
                "value": num(d["customer_unique_id"].nunique()),
                "note": "Pelanggan unik",
            },
            {
                "icon": "receipt",
                "label": "AOV",
                "value": rp(d["payment_value"].mean()),
                "note": "Average Order Value",
            },
            {
                "icon": "repeat",
                "label": "Repeat Rate",
                "value": f"{kpi['repeat_rate']:.1f}%",
                "note": "Pelanggan >1 order",
            },
            {
                "icon": "star",
                "label": "Rating",
                "value": f"{d['review_score'].mean():.2f} / 5",
                "note": "Rata-rata review",
            },
        ]
    )

    section_header("Performa Bisnis")

    fig = px.area(
        monthly,
        x="month",
        y="revenue",
        markers=True,
        labels={"month": "Bulan", "revenue": "Revenue (R$)"},
    )
    fig.update_traces(
        line=dict(color=GREEN, width=2.5),
        marker=dict(size=5, color=GREEN),
        fillcolor="rgba(22,163,74,0.10)",
        hovertemplate="%{x|%b %Y}<br>Revenue: R$ %{y:,.0f}<extra></extra>",
    )
    fig.update_yaxes(tickprefix="R$ ", tickformat="~s")
    chart_card(
        "Tren Revenue Bulanan",
        "Revenue order delivered per bulan (minimal 50 order per bulan)",
        theme(fig, 300),
        key="revenue_trend",
    )

    section_header("Sebaran Pelanggan")

    state_agg = (
        d.groupby("customer_state")
        .agg(
            revenue=("payment_value", "sum"),
            orders=("order_id", "nunique"),
            customers=("customer_unique_id", "nunique"),
        )
        .reset_index()
    )
    cent = (
        rfm.groupby("customer_state")
        .agg(lat=("lat", "mean"), lng=("lng", "mean"))
        .reset_index()
    )
    state_agg = state_agg.merge(cent, on="customer_state", how="left").dropna(
        subset=["lat", "lng"]
    )

    left, right = st.columns([0.75, 1.25])
    with left:
        if BRAZIL_GEO is not None:
            fig = px.choropleth(
                state_agg,
                geojson=BRAZIL_GEO,
                locations="customer_state",
                featureidkey="properties.sigla",
                color="revenue",
                color_continuous_scale=GREEN_CONTINUOUS,
                hover_name="customer_state",
                hover_data={
                    "customers": ":,",
                    "orders": ":,",
                    "revenue": ":,.0f",
                    "lat": False,
                    "lng": False,
                },
            )
            fig.update_geos(
                projection_type="mercator",
                visible=False,
                lataxis_range=[-34.5, 5.5],
                lonaxis_range=[-74.5, -34],
            )
            fig.update_traces(marker_line_color=WHITE, marker_line_width=0.8)
            fig.update_coloraxes(showscale=False)
            fig.update_layout(margin=dict(l=0, r=0, t=0, b=0))
        else:
            fig = px.scatter_geo(
                state_agg,
                lat="lat",
                lon="lng",
                size="revenue",
                color="revenue",
                hover_name="customer_state",
                hover_data={
                    "customers": ":,",
                    "orders": ":,",
                    "revenue": ":,.0f",
                    "lat": False,
                    "lng": False,
                },
                color_continuous_scale=GREEN_CONTINUOUS,
                size_max=42,
            )
            fig.update_geos(
                fitbounds="locations",
                projection_type="mercator",
                showcountries=True,
                countrycolor="#DCFCE7",
                showcoastlines=False,
                showframe=False,
                showland=True,
                landcolor="#F1F8F2",
                bgcolor=WHITE,
            )
            fig.update_coloraxes(showscale=False)
        chart_card(
            "Sebaran Pelanggan per State",
            "Intensitas warna mewakili revenue; arahkan kursor untuk detail",
            theme(fig, 360),
            key="geo_state",
        )

    with right:
        city_agg = (
            d.groupby(["customer_city", "customer_state"])
            .agg(
                revenue=("payment_value", "sum"),
                customers=("customer_unique_id", "nunique"),
            )
            .reset_index()
            .nlargest(10, "revenue")
            .sort_values("revenue")
        )
        city_agg["label"] = (
            city_agg["customer_city"].str.title()
            + " ("
            + city_agg["customer_state"]
            + ")"
        )
        fig = px.bar(
            city_agg,
            x="revenue",
            y="label",
            orientation="h",
            text="revenue",
            color="revenue",
            color_continuous_scale=GREEN_CONTINUOUS,
            labels={"revenue": "Revenue (R$)", "label": ""},
        )
        fig.update_traces(
            texttemplate="%{text:,.0f}",
            textposition="outside",
            cliponaxis=False,
            marker_line_width=0,
            textfont=dict(size=10),
        )
        fig.update_coloraxes(showscale=False)
        fig.update_xaxes(
            tickprefix="R$ ",
            tickformat="~s",
            range=[0, city_agg["revenue"].max() * 1.3],
        )
        chart_card(
            "Top 10 Kota",
            "Kota dengan kontribusi revenue tertinggi",
            theme(fig, 360),
            key="top_cities",
        )

    section_header("Konsentrasi Wilayah")
    state_sorted = state_agg.sort_values("revenue", ascending=False)
    fig = px.bar(
        state_sorted,
        x="customer_state",
        y="revenue",
        color="revenue",
        color_continuous_scale=GREEN_CONTINUOUS,
        hover_data={"customers": ":,", "orders": ":,"},
        labels={"customer_state": "State", "revenue": "Revenue (R$)"},
    )
    fig.update_traces(marker_line_width=0)
    fig.update_coloraxes(showscale=False)
    fig.update_yaxes(tickprefix="R$ ", tickformat="~s")
    chart_card(
        "Revenue per State",
        "Kontribusi seluruh state di Brazil pada periode terfilter",
        theme(fig, 240),
        key="revenue_state",
    )

# =============================== TAB 2 ====================================
with tabs[1]:
    if r.empty:
        st.warning("Tidak ada pelanggan pada kombinasi filter ini.")
    else:
        top_customers = r.nlargest(20, "monetary")
        total_rev = r["monetary"].sum()
        share_top20 = top_customers["monetary"].sum() / total_rev * 100 if total_rev else 0

        kpi_row(
            [
                {
                    "icon": "wallet",
                    "label": "Total Nilai Pelanggan",
                    "value": compact_rp(total_rev),
                    "note": "Akumulasi monetary",
                },
                {
                    "icon": "users",
                    "label": "Rata-rata per Pelanggan",
                    "value": rp(r["monetary"].mean()),
                    "note": "Monetary rata-rata",
                },
                {
                    "icon": "receipt",
                    "label": "Median Transaksi",
                    "value": rp(r["monetary"].median()),
                    "note": "Nilai tengah monetary",
                },
                {
                    "icon": "target",
                    "label": "Top 20 Share",
                    "value": f"{share_top20:.2f}%",
                    "note": "Kontribusi 20 pelanggan terbesar",
                },
            ]
        )

        section_header("Analisis Nilai Pelanggan")

        c1, c2, c3 = st.columns(3)
        with c1:
            s = r["monetary"].sort_values(ascending=False).reset_index(drop=True)
            cum = s.cumsum() / s.sum() * 100
            x = (np.arange(len(s)) + 1) / len(s) * 100
            fig = go.Figure()
            fig.add_trace(
                go.Scatter(
                    x=x,
                    y=cum,
                    mode="lines",
                    line=dict(color=GREEN, width=3),
                    fill="tozeroy",
                    fillcolor="rgba(167,221,181,0.30)",
                    name="Kumulatif revenue",
                    hovertemplate="%{x:.1f}% pelanggan → %{y:.1f}% revenue<extra></extra>",
                )
            )
            idx80 = int(np.searchsorted(cum.values, 80))
            pct80 = (idx80 + 1) / len(s) * 100
            fig.add_hline(y=80, line_dash="dash", line_color=DARK_GREEN, line_width=1)
            fig.add_vline(x=pct80, line_dash="dash", line_color=DARK_GREEN, line_width=1)
            fig.add_annotation(
                x=pct80,
                y=80,
                text=f"{pct80:.0f}% pelanggan = 80% revenue",
                showarrow=True,
                arrowhead=2,
                ay=-30,
                bgcolor=WHITE,
                bordercolor=LIGHT_GREEN,
                font=dict(color=DARK_GREEN, size=10),
            )
            fig.update_layout(
                xaxis_title="% Pelanggan",
                yaxis_title="% Revenue kumulatif",
                xaxis_range=[0, 100],
                yaxis_range=[0, 105],
            )
            chart_card(
                "Kurva Pareto",
                "Konsentrasi revenue terhadap jumlah pelanggan",
                theme(fig, 320),
                key="pareto",
            )

        with c2:
            vals = r["monetary"].clip(lower=1)
            log_vals = np.log10(vals)
            counts, edges = np.histogram(log_vals, bins=40)
            centers = (edges[:-1] + edges[1:]) / 2
            fig = go.Figure(
                go.Bar(
                    x=centers,
                    y=counts,
                    width=np.diff(edges) * 0.92,
                    marker_color=GREEN,
                    marker_line_width=0,
                    customdata=10 ** centers,
                    hovertemplate=(
                        "Monetary ≈ R$ %{customdata:,.0f}<br>"
                        "%{y:,} pelanggan<extra></extra>"
                    ),
                )
            )
            fig.update_xaxes(
                tickvals=[0, 1, 2, 3, 4],
                ticktext=["R$ 1", "R$ 10", "R$ 100", "R$ 1 rb", "R$ 10 rb"],
                title="Monetary (log)",
            )
            chart_card(
                "Distribusi Nilai Transaksi",
                "Sebaran monetary per pelanggan (skala logaritmik)",
                theme(fig, 320),
                key="monetary_dist",
            )

        with c3:
            seg = (
                r.groupby("segment", observed=True)
                .agg(
                    revenue=("monetary", "sum"),
                    customers=("customer_unique_id", "nunique"),
                )
                .reset_index()
            )
            seg["segment"] = seg["segment"].astype(str)
            seg = seg.sort_values("revenue")
            fig = px.bar(
                seg,
                x="revenue",
                y="segment",
                orientation="h",
                text="revenue",
                color="revenue",
                color_continuous_scale=GREEN_CONTINUOUS,
                labels={"revenue": "Revenue (R$)", "segment": ""},
            )
            fig.update_traces(
                texttemplate="R$ %{text:,.0f}",
                textposition="outside",
                cliponaxis=False,
                marker_line_width=0,
                textfont=dict(size=9),
            )
            fig.update_coloraxes(showscale=False)
            fig.update_xaxes(
                tickprefix="R$ ",
                tickformat="~s",
                range=[0, seg["revenue"].max() * 1.32],
            )
            chart_card(
                "Revenue per Segmen RFM",
                "Kontribusi nilai historis tiap segmen",
                theme(fig, 320),
                key="segment_revenue",
            )

        section_header("Distribusi & Kontribusi Revenue")
        c4, c5, c6 = st.columns(3)
        with c4:
            cat_agg = (
                d.groupby("top_category")
                .agg(revenue=("payment_value", "sum"))
                .reset_index()
                .nlargest(10, "revenue")
                .sort_values("revenue")
            )
            cat_agg["label"] = (
                cat_agg["top_category"].str.replace("_", " ").str.title()
            )
            fig = px.bar(
                cat_agg,
                x="revenue",
                y="label",
                orientation="h",
                color="revenue",
                color_continuous_scale=GREEN_CONTINUOUS,
                labels={"revenue": "Revenue (R$)", "label": ""},
            )
            fig.update_traces(marker_line_width=0)
            fig.update_coloraxes(showscale=False)
            fig.update_xaxes(tickprefix="R$ ", tickformat="~s")
            chart_card(
                "Top Kategori Produk",
                "10 kategori dengan revenue tertinggi",
                theme(fig, 320),
                key="category_bar",
            )
        with c5:
            pay_agg = (
                d.groupby("payment_type")
                .agg(
                    revenue=("payment_value", "sum"),
                    orders=("order_id", "nunique"),
                )
                .reset_index()
            )
            fig = px.pie(
                pay_agg,
                names="payment_type",
                values="revenue",
                hole=0.55,
                color_discrete_sequence=GREEN_SEQ,
            )
            fig.update_traces(
                textinfo="percent",
                textposition="inside",
                marker=dict(line=dict(color=WHITE, width=2)),
            )
            top_pay = pay_agg.nlargest(1, "revenue").iloc[0]
            fig.add_annotation(
                text=(
                    f"<b>{top_pay['payment_type']}</b><br>"
                    f"{top_pay['revenue'] / pay_agg['revenue'].sum() * 100:.0f}% revenue"
                ),
                showarrow=False,
                font=dict(size=10, color=DARK_GREEN),
            )
            chart_card(
                "Metode Pembayaran",
                "Distribusi revenue berdasarkan metode pembayaran",
                theme(fig, 320, legend=True),
                key="payment_pie",
            )
        with c6:
            inst = (
                d.groupby("payment_installments")
                .agg(orders=("order_id", "nunique"))
                .reset_index()
                .sort_values("payment_installments")
            )
            inst = inst[inst["payment_installments"] <= 12]
            fig = px.bar(
                inst,
                x="payment_installments",
                y="orders",
                labels={"payment_installments": "Cicilan (x)", "orders": "Jumlah order"},
            )
            fig.update_traces(marker_color=MINT, marker_line_width=0)
            fig.update_xaxes(dtick=1)
            chart_card(
                "Jumlah Cicilan",
                "Preferensi tenor pembayaran pelanggan",
                theme(fig, 320),
                key="installments",
            )

        section_header("Pelanggan Terbaik")
        rows = []
        for _, row in top_customers.iterrows():
            rows.append(
                [
                    muted(str(row["customer_unique_id"])[:12] + "…"),
                    html.escape(str(row["customer_state"])),
                    html.escape(str(row["customer_city"]).title()),
                    strong(int(row["frequency"])),
                    strong(rp(row["monetary"])),
                    rp(row["aov"]),
                    f"{int(row['recency'])} hari",
                    segment_chip(str(row["segment"])),
                ]
            )
        with panel(
            "20 Pelanggan Terbaik",
            "Diurutkan berdasarkan total nilai transaksi",
        ):
            render_table(
                [
                    "ID Pelanggan",
                    "State",
                    "Kota",
                    "Order",
                    "Monetary",
                    "AOV",
                    "Recency",
                    "Segmen",
                ],
                rows,
                max_height=420,
                min_width=980,
            )

# =============================== TAB 3 ====================================
with tabs[2]:
    if r.empty:
        st.warning("Tidak ada pelanggan pada kombinasi filter ini.")
    else:
        churn = r[r["churn_flag"]]
        repeat_pct = (r["frequency"] > 1).mean() * 100

        kpi_row(
            [
                {
                    "icon": "alert",
                    "label": "Berpotensi Tidak Aktif",
                    "value": num(len(churn)),
                    "note": "Recency > P75 & frekuensi ≤ 2",
                },
                {
                    "icon": "shield",
                    "label": "Revenue at Risk",
                    "value": compact_rp(churn["monetary"].sum()),
                    "note": "Nilai historis pelanggan berisiko",
                },
                {
                    "icon": "target",
                    "label": "% Pelanggan Berisiko",
                    "value": f"{len(churn) / len(r) * 100:.1f}%",
                    "note": "Proporsi pelanggan terfilter",
                },
                {
                    "icon": "repeat",
                    "label": "Rata-rata Recency",
                    "value": f"{r['recency'].mean():.0f} hari",
                    "note": "Sejak pembelian terakhir",
                },
                {
                    "icon": "star",
                    "label": "Avg Review",
                    "value": f"{r['avg_review'].mean():.2f} / 5",
                    "note": "Kepuasan pelanggan",
                },
            ]
        )

        section_header("Churn & Loyalitas")

        c1, c2, c3 = st.columns(3)
        with c1:
            seg = (
                r.groupby("segment", observed=True)
                .agg(customers=("customer_unique_id", "nunique"))
                .reset_index()
            )
            seg["segment"] = seg["segment"].astype(str)
            seg = seg.sort_values("customers", ascending=False)
            fig = px.bar(
                seg,
                x="customers",
                y="segment",
                orientation="h",
                text="customers",
                color="segment",
                color_discrete_map=SEGMENT_COLORS,
                labels={"segment": "", "customers": "Jumlah pelanggan"},
            )
            fig.update_traces(
                marker_line_width=0,
                textposition="outside",
                cliponaxis=False,
                textfont=dict(size=9),
            )
            fig.update_xaxes(range=[0, seg["customers"].max() * 1.22])
            fig.update_layout(showlegend=False)
            chart_card(
                "Jumlah Pelanggan per Segmen",
                "Distribusi pelanggan pada tiap segmen RFM",
                theme(fig, 320),
                key="segment_bar",
            )
        with c2:
            fig = px.histogram(
                r,
                x="recency",
                nbins=50,
                labels={
                    "recency": "Hari sejak pembelian terakhir",
                    "count": "Pelanggan",
                },
            )
            fig.update_traces(
                marker_color=MINT, marker_line_color=WHITE, marker_line_width=1
            )
            fig.update_yaxes(title_text="Pelanggan")
            fig.add_vline(
                x=kpi["p75_recency"],
                line_dash="dash",
                line_color=DARK_GREEN,
                annotation_text=f"P75 = {kpi['p75_recency']:.0f} hari",
                annotation_position="top right",
                annotation_font=dict(color=DARK_GREEN, size=10),
            )
            chart_card(
                "Distribusi Recency",
                "Semakin ke kanan, semakin lama pelanggan tidak bertransaksi",
                theme(fig, 320),
                key="recency_hist",
            )
        with c3:
            rep = pd.DataFrame(
                {
                    "Tipe": ["One-time", "Repeat"],
                    "Pelanggan": [
                        int((r["frequency"] <= 1).sum()),
                        int((r["frequency"] > 1).sum()),
                    ],
                }
            )
            fig = px.pie(
                rep,
                names="Tipe",
                values="Pelanggan",
                hole=0.62,
                color="Tipe",
                color_discrete_map={"One-time": "#E5EFE7", "Repeat": GREEN},
            )
            fig.update_traces(
                textinfo="percent",
                textposition="inside",
                marker=dict(line=dict(color=WHITE, width=2)),
            )
            fig.add_annotation(
                text=f"<b>{repeat_pct:.1f}%</b><br>repeat",
                showarrow=False,
                font=dict(size=14, color=DARK_GREEN),
            )
            chart_card(
                "Repeat vs One-time",
                "Proporsi pelanggan yang bertransaksi lebih dari sekali",
                theme(fig, 320, legend=True),
                key="repeat_pie",
            )

        section_header("Analisis Pelanggan Berisiko")
        risk = churn.nlargest(20, "monetary")
        rows = []
        for _, row in risk.iterrows():
            rows.append(
                [
                    muted(str(row["customer_unique_id"])[:12] + "…"),
                    html.escape(str(row["customer_state"])),
                    html.escape(str(row["customer_city"]).title()),
                    strong(int(row["frequency"])),
                    strong(rp(row["monetary"])),
                    f"{int(row['recency'])} hari",
                    segment_chip(str(row["segment"])),
                    html.escape(str(row["main_category"])),
                    chip("Berisiko", "amber"),
                ]
            )
        with panel(
            "Pelanggan Berpotensi Tidak Aktif",
            "20 pelanggan dengan nilai historis terbesar yang perlu di-win-back",
        ):
            render_table(
                [
                    "ID Pelanggan",
                    "State",
                    "Kota",
                    "Order",
                    "Nilai Historis",
                    "Recency",
                    "Segmen",
                    "Kategori Utama",
                    "Status",
                ],
                rows,
                max_height=330,
                min_width=1020,
            )

        section_header("Retensi & Kepuasan")
        c4, c5 = st.columns([2, 1])
        with c4:
            pivot = cohort.pivot(
                index="cohort", columns="cohort_index", values="retention_rate"
            ).sort_index()
            z = pivot.values
            display = np.array(
                [
                    ["" if pd.isna(v) or v < 0.5 else f"{v:.0f}%" for v in row]
                    for row in z
                ],
                dtype=object,
            )
            fig = go.Figure(
                go.Heatmap(
                    z=z,
                    x=[f"Bulan {c}" for c in pivot.columns],
                    y=pivot.index,
                    colorscale=GREEN_HEATMAP,
                    zmin=0,
                    zmax=30,
                    text=display,
                    texttemplate="%{text}",
                    textfont=dict(color=DARK_GREEN, size=10),
                    hovertemplate="Cohort %{y}<br>%{x}: %{z:.0f}%<extra></extra>",
                    colorbar=dict(
                        title="%",
                        thickness=10,
                        outlinewidth=0,
                        tickfont=dict(size=10),
                    ),
                    xgap=2,
                    ygap=2,
                )
            )
            chart_card(
                "Cohort Retention",
                "Persentase pelanggan yang kembali bertransaksi per bulan sejak akuisisi",
                theme(fig, 360),
                key="cohort_heatmap",
            )
        with c5:
            box = d.dropna(subset=["review_score"]).copy()
            box["Pengiriman"] = np.where(box["is_late"], "Terlambat", "Tepat Waktu")
            fig = px.box(
                box,
                x="Pengiriman",
                y="review_score",
                color="Pengiriman",
                points=False,
                color_discrete_map={"Tepat Waktu": GREEN, "Terlambat": "#D97706"},
                labels={"review_score": "Skor Review"},
            )
            fig.update_layout(showlegend=False)
            fig.update_yaxes(range=[0, 5.3], dtick=1)
            chart_card(
                "Review vs Ketepatan Pengiriman",
                "Dampak keterlambatan terhadap kepuasan pelanggan",
                theme(fig, 340),
                key="review_box",
            )

        section_header("Strategi Pemasaran")
        strategy_rows = [
            [
                segment_chip(seg),
                html.escape(karakter),
                html.escape(strategi),
                html.escape(kanal),
                strong(target),
            ]
            for seg, karakter, strategi, kanal, target in STRATEGI
        ]
        with panel(
            "Matriks Strategi Pemasaran",
            "Rekomendasi aksi, kanal, dan target KPI untuk setiap segmen",
        ):
            render_table(
                ["Segmen", "Karakteristik", "Strategi", "Kanal", "Target KPI"],
                strategy_rows,
                min_width=980,
            )

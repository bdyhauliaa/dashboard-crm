from __future__ import annotations

import json
from pathlib import Path

import numpy as np
import pandas as pd

BASE = Path(__file__).resolve().parents[1]
DATA = BASE / "data" / "raw"
OUT = BASE / "data" / "data_processed"

DATE_COLS = [
    "order_purchase_timestamp",
    "order_approved_at",
    "order_delivered_carrier_date",
    "order_delivered_customer_date",
    "order_estimated_delivery_date",
]

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


def _score(series: pd.Series, ascending: bool) -> pd.Series:
    ranks = series.rank(method="first", ascending=ascending)
    return pd.qcut(ranks, 5, labels=[1, 2, 3, 4, 5]).astype(int)


def _segment(r: int, f: int, m: int) -> str:
    if r >= 4 and f >= 4 and m >= 4:
        return "Champions"
    if r >= 3 and f >= 4:
        return "Loyal"
    if r >= 4 and f == 1:
        return "Pelanggan Baru"
    if r >= 3 and 2 <= f <= 3:
        return "Potensial Loyal"
    if r == 3:
        return "Perlu Perhatian"
    if r <= 2 and f >= 4 and m >= 4:
        return "Tidak Boleh Hilang"
    if r <= 2 and f >= 3:
        return "Berisiko"
    if r == 1 and f <= 2:
        return "Hilang"
    if r <= 2 and f <= 2:
        return "Hibernasi"
    return "Hilang"


def load_data() -> dict[str, pd.DataFrame]:
    orders = pd.read_csv(DATA / "olist_orders_dataset.csv", parse_dates=DATE_COLS)
    customers = pd.read_csv(DATA / "olist_customers_dataset.csv")
    items = pd.read_csv(DATA / "olist_order_items_dataset.csv")
    payments = pd.read_csv(DATA / "olist_order_payments_dataset.csv")
    reviews = pd.read_csv(DATA / "olist_order_reviews_dataset.csv")
    products = pd.read_csv(DATA / "olist_products_dataset.csv")
    translation = pd.read_csv(DATA / "product_category_name_translation.csv")
    geo = pd.read_csv(
        DATA / "olist_geolocation_dataset.csv",
        usecols=[
            "geolocation_zip_code_prefix",
            "geolocation_lat",
            "geolocation_lng",
            "geolocation_city",
            "geolocation_state",
        ],
    )
    return {
        "orders": orders,
        "customers": customers,
        "items": items,
        "payments": payments,
        "reviews": reviews,
        "products": products,
        "translation": translation,
        "geo": geo,
    }


def build_geo(d: dict[str, pd.DataFrame]) -> pd.DataFrame:
    geo = d["geo"]
    agg = (
        geo.groupby("geolocation_zip_code_prefix")
        .agg(
            lat=("geolocation_lat", "mean"),
            lng=("geolocation_lng", "mean"),
            geo_city=("geolocation_city", "first"),
            geo_state=("geolocation_state", "first"),
        )
        .reset_index()
        .rename(columns={"geolocation_zip_code_prefix": "customer_zip"})
    )
    agg["customer_zip"] = agg["customer_zip"].astype(int)
    return agg


def build_master(d: dict[str, pd.DataFrame]) -> pd.DataFrame:
    orders = d["orders"]
    customers = d["customers"]

    pay = (
        d["payments"]
        .groupby("order_id")
        .agg(
            payment_value=("payment_value", "sum"),
            payment_type=("payment_type", "first"),
            payment_installments=("payment_installments", "max"),
            n_payments=("payment_sequential", "count"),
        )
        .reset_index()
    )

    prod = d["products"].merge(d["translation"], on="product_category_name", how="left")
    prod = prod.rename(columns={"product_category_name_english": "category_en"})
    prod["category_en"] = prod["category_en"].fillna("unknown")
    items = d["items"].merge(
        prod[["product_id", "category_en"]], on="product_id", how="left"
    )
    items["category_en"] = items["category_en"].fillna("unknown")

    item_agg = (
        items.groupby("order_id")
        .agg(
            price_sum=("price", "sum"),
            freight_sum=("freight_value", "sum"),
            n_items=("order_item_id", "count"),
            n_products=("product_id", "nunique"),
        )
        .reset_index()
    )

    cat = (
        items.groupby(["order_id", "category_en"])["price"]
        .sum()
        .reset_index()
        .sort_values(["order_id", "price"], ascending=[True, False])
        .drop_duplicates("order_id")[["order_id", "category_en"]]
        .rename(columns={"category_en": "top_category"})
    )

    rev = (
        d["reviews"]
        .groupby("order_id")
        .agg(review_score=("review_score", "mean"), n_reviews=("review_id", "count"))
        .reset_index()
    )
    rev["review_score"] = rev["review_score"].round(2)

    master = (
        orders.merge(customers, on="customer_id", how="left")
        .merge(pay, on="order_id", how="left")
        .merge(item_agg, on="order_id", how="left")
        .merge(cat, on="order_id", how="left")
        .merge(rev, on="order_id", how="left")
    )
    master["top_category"] = master["top_category"].fillna("unknown")
    master["payment_type"] = master["payment_type"].fillna("not_defined")

    master["delivery_days"] = (
        master["order_delivered_customer_date"] - master["order_purchase_timestamp"]
    ).dt.days
    master["late_days"] = (
        master["order_delivered_customer_date"] - master["order_estimated_delivery_date"]
    ).dt.days
    master["is_late"] = master["late_days"] > 0
    master["is_delivered"] = master["order_status"] == "delivered"

    master = master.rename(
        columns={
            "customer_unique_id": "customer_unique_id",
            "customer_zip_code_prefix": "customer_zip",
            "customer_city": "customer_city",
            "customer_state": "customer_state",
        }
    )
    keep = [
        "order_id",
        "customer_unique_id",
        "customer_zip",
        "customer_city",
        "customer_state",
        "order_status",
        "order_purchase_timestamp",
        "order_delivered_customer_date",
        "order_estimated_delivery_date",
        "delivery_days",
        "late_days",
        "is_late",
        "is_delivered",
        "payment_value",
        "payment_type",
        "payment_installments",
        "n_payments",
        "price_sum",
        "freight_sum",
        "n_items",
        "n_products",
        "top_category",
        "review_score",
        "n_reviews",
    ]
    return master[keep]


def build_rfm(master: pd.DataFrame, geo_agg: pd.DataFrame) -> pd.DataFrame:
    delivered = master[master["is_delivered"]].copy()
    snapshot = master["order_purchase_timestamp"].max().normalize() + pd.Timedelta(days=1)

    rfm = (
        delivered.groupby("customer_unique_id")
        .agg(
            recency=("order_purchase_timestamp", lambda s: (snapshot - s.max()).days),
            frequency=("order_id", "nunique"),
            monetary=("payment_value", "sum"),
            first_purchase=("order_purchase_timestamp", "min"),
            last_purchase=("order_purchase_timestamp", "max"),
            total_items=("n_items", "sum"),
            avg_review=("review_score", "mean"),
        )
        .reset_index()
    )

    base = master.drop_duplicates("customer_unique_id")[
        ["customer_unique_id", "customer_state", "customer_city", "customer_zip"]
    ]
    rfm = rfm.merge(base, on="customer_unique_id", how="left")

    main_cat = (
        delivered.groupby(["customer_unique_id", "top_category"])["payment_value"]
        .sum()
        .reset_index()
        .sort_values("payment_value", ascending=False)
        .drop_duplicates("customer_unique_id")[["customer_unique_id", "top_category"]]
        .rename(columns={"top_category": "main_category"})
    )
    rfm = rfm.merge(main_cat, on="customer_unique_id", how="left")
    rfm["main_category"] = rfm["main_category"].fillna("unknown")

    rfm = rfm.merge(geo_agg, on="customer_zip", how="left")

    rfm["r_score"] = _score(rfm["recency"], ascending=False)
    rfm["f_score"] = _score(rfm["frequency"], ascending=True)
    rfm["m_score"] = _score(rfm["monetary"], ascending=True)
    rfm["rfm_score"] = (
        rfm["r_score"].astype(str)
        + rfm["f_score"].astype(str)
        + rfm["m_score"].astype(str)
    )

    rfm["segment"] = [
        _segment(r, f, m)
        for r, f, m in zip(rfm["r_score"], rfm["f_score"], rfm["m_score"])
    ]
    rfm["segment"] = pd.Categorical(rfm["segment"], categories=SEGMENT_ORDER, ordered=True)

    rfm["aov"] = rfm["monetary"] / rfm["frequency"]
    tenure_days = (rfm["last_purchase"] - rfm["first_purchase"]).dt.days + 1
    tenure_months = np.maximum(tenure_days / 30.44, 1.0)
    rfm["est_annual_value"] = rfm["aov"] * (rfm["frequency"] / tenure_months) * 12
    rfm["avg_review"] = rfm["avg_review"].round(2)

    p75 = rfm["recency"].quantile(0.75)
    rfm["churn_flag"] = (rfm["recency"] > p75) & (rfm["frequency"] <= 2)
    rfm["risk_label"] = np.where(
        rfm["churn_flag"], "Berpotensi Tidak Aktif", "Aktif"
    )
    rfm.attrs["p75_recency"] = float(p75)

    rfm = rfm.sort_values("monetary", ascending=False).reset_index(drop=True)
    return rfm


def build_cohort(master: pd.DataFrame) -> pd.DataFrame:
    delivered = master[master["is_delivered"]][
        ["customer_unique_id", "order_purchase_timestamp"]
    ].copy()
    delivered["order_month"] = delivered["order_purchase_timestamp"].dt.to_period("M")
    cohort = delivered.groupby("customer_unique_id")["order_month"].min().rename("cohort")
    delivered = delivered.merge(cohort, on="customer_unique_id", how="left")
    delivered["cohort_index"] = (
        delivered["order_month"].astype(int) - delivered["cohort"].astype(int)
    )

    cohort_sizes = delivered.groupby("cohort")["customer_unique_id"].nunique()
    retention = (
        delivered.groupby(["cohort", "cohort_index"])["customer_unique_id"]
        .nunique()
        .reset_index()
    )
    retention["cohort_size"] = retention["cohort"].map(cohort_sizes)
    retention["retention_rate"] = (
        retention["customer_unique_id"] / retention["cohort_size"] * 100
    )
    retention = retention[retention["cohort_index"] <= 11]
    retention["cohort"] = retention["cohort"].astype(str)
    return retention


def build_kpi(master: pd.DataFrame, rfm: pd.DataFrame) -> dict:
    d = master[master["is_delivered"]]
    p75 = rfm.attrs.get("p75_recency", float(rfm["recency"].quantile(0.75)))
    return {
        "total_revenue": float(d["payment_value"].sum()),
        "total_orders": int(d["order_id"].nunique()),
        "total_customers": int(d["customer_unique_id"].nunique()),
        "aov": float(d["payment_value"].mean()),
        "repeat_rate": float((rfm["frequency"] > 1).mean() * 100),
        "avg_review": float(d["review_score"].mean()),
        "delivery_rate": float(master["is_delivered"].mean() * 100),
        "cancel_rate": float((master["order_status"] == "canceled").mean() * 100),
        "late_rate": float(d["is_late"].mean() * 100),
        "date_min": str(master["order_purchase_timestamp"].min().date()),
        "date_max": str(master["order_purchase_timestamp"].max().date()),
        "top_state": str(
            d.groupby("customer_state")["payment_value"].sum().idxmax()
        ),
        "churn_customers": int(rfm["churn_flag"].sum()),
        "revenue_at_risk": float(rfm.loc[rfm["churn_flag"], "monetary"].sum()),
        "p75_recency": p75,
    }


def main() -> None:
    OUT.mkdir(parents=True, exist_ok=True)
    print("Membaca dataset...")
    d = load_data()

    print("Membangun agregasi geolokasi...")
    geo_agg = build_geo(d)

    print("Membangun tabel master order...")
    master = build_master(d)

    print("Menghitung RFM...")
    rfm = build_rfm(master, geo_agg)

    print("Membangun cohort retention...")
    cohort = build_cohort(master)

    print("Menghitung KPI...")
    kpi = build_kpi(master, rfm)

    master.to_parquet(OUT / "master_orders.parquet", index=False)
    rfm.to_parquet(OUT / "customers_rfm.parquet", index=False)
    cohort.to_parquet(OUT / "cohort_retention.parquet", index=False)
    geo_agg.to_parquet(OUT / "geo_agg.parquet", index=False)
    with open(OUT / "kpi_summary.json", "w", encoding="utf-8") as f:
        json.dump(kpi, f, ensure_ascii=False, indent=2)

    print("\nSelesai. Output di:", OUT)
    print("master_orders :", master.shape)
    print("customers_rfm :", rfm.shape)
    print("cohort        :", cohort.shape)
    print("geo_agg       :", geo_agg.shape)
    print("\nKPI:", json.dumps(kpi, indent=2, ensure_ascii=False))
    print("\nSegmen RFM:")
    print(rfm["segment"].value_counts().to_string())


if __name__ == "__main__":
    main()

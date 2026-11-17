"""EDA and preprocessing for Kaggle Credit Card Fraud Detection dataset."""

import os
import pandas as pd
import numpy as np

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
CSV_PATH = os.path.join(BASE_DIR, "creditcard.csv")
CHART_PATH = os.path.join(BASE_DIR, "charts", "creditcard_eda.png")


def main() -> None:
    df = pd.read_csv(CSV_PATH)
    print(f"Shape: {df.shape[0]:,} rows x {df.shape[1]} cols")
    print(f"Missing values: {int(df.isna().sum().sum())}")
    print(f"Duplicate rows: {int(df.duplicated().sum()):,}")

    # Class distribution
    counts = df["Class"].value_counts().sort_index()
    total = len(df)
    legit = int(counts.get(0, 0))
    fraud = int(counts.get(1, 0))
    print(f"Class 0 (Legit): {legit:,} ({legit / total * 100:.4f}%)")
    print(f"Class 1 (Fraud): {fraud:,} ({fraud / total * 100:.4f}%)")

    # Preprocessing: derive hour_of_day and amount_bucket
    df["hour_of_day"] = ((df["Time"] // 3600) % 24).astype(int)
    df["day"] = (df["Time"] // 86400).astype(int) + 1

    # Amount statistics by Class
    print("\n--- Amount Summary by Class ---")
    for cls, label in [(0, "Legit"), (1, "Fraud")]:
        s = df.loc[df["Class"] == cls, "Amount"]
        print(
            f"{label}: mean={s.mean():.2f}, median={s.median():.2f}, "
            f"p95={s.quantile(0.95):.2f}, max={s.max():.2f}, "
            f"zero_amt={(s == 0).sum():,} ({(s == 0).mean() * 100:.2f}%)"
        )

    # Fraud rate by Amount bucket
    bins = [-0.01, 0, 10, 100, 500, float("inf")]
    labels = ["0", "(0, 10]", "(10, 100]", "(100, 500]", "> 500"]
    df["amt_bucket"] = pd.cut(df["Amount"], bins=bins, labels=labels)
    print("\n--- Fraud Rate by Amount Bucket ---")
    bucket_stats = (
        df.groupby("amt_bucket", observed=False)["Class"]
        .agg(total="count", fraud="sum")
        .assign(fraud_rate_pct=lambda x: x["fraud"] / x["total"] * 100)
    )
    print(bucket_stats.to_string())

    # Fraud rate by hour_of_day (top 5 highest fraud-rate hours)
    hourly = (
        df.groupby("hour_of_day")["Class"]
        .agg(total="count", fraud="sum")
        .assign(fraud_rate_pct=lambda x: x["fraud"] / x["total"] * 100)
    )
    print("\n--- Top 5 Highest Fraud-Rate Hours ---")
    print(hourly.sort_values("fraud_rate_pct", ascending=False).head(5).to_string())

    # Top correlated V-features with Class
    v_cols = [f"V{i}" for i in range(1, 29)]
    corrs = df[v_cols].corrwith(df["Class"]).sort_values()
    print("\n--- Top 5 Negative Correlations with Class ---")
    print(corrs.head(5).round(4).to_string())
    print("\n--- Top 5 Positive Correlations with Class ---")
    print(corrs.tail(5).iloc[::-1].round(4).to_string())

    # Plot summary chart
    try:
        import matplotlib.pyplot as plt

        os.makedirs(os.path.dirname(CHART_PATH), exist_ok=True)
        fig, axes = plt.subplots(1, 2, figsize=(12, 4.5))

        # Left: Hourly volume & fraud rate
        ax1 = axes[0]
        ax1.bar(hourly.index, hourly["total"], color="#4C78A8", alpha=0.75, label="Total Tx")
        ax1.set_xlabel("Hour of Day (0-23)")
        ax1.set_ylabel("Transaction Count", color="#4C78A8")
        ax1.set_title("Hourly Transaction Volume vs. Fraud Rate")
        ax2 = ax1.twinx()
        ax2.plot(hourly.index, hourly["fraud_rate_pct"], color="#E45756", marker="o", linewidth=2, label="Fraud Rate (%)")
        ax2.set_ylabel("Fraud Rate (%)", color="#E45756")

        # Right: Fraud rate by Amount bucket
        ax3 = axes[1]
        ax3.bar(bucket_stats.index.astype(str), bucket_stats["fraud_rate_pct"], color="#F58518")
        ax3.set_xlabel("Amount Bucket")
        ax3.set_ylabel("Fraud Rate (%)")
        ax3.set_title("Fraud Rate by Transaction Amount Bucket")

        plt.tight_layout()
        plt.savefig(CHART_PATH, dpi=150)
        print(f"\nSaved chart to: {CHART_PATH}")
    except Exception as exc:
        print(f"\nSkipping chart generation: {exc}")


if __name__ == "__main__":
    main()

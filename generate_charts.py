import sqlite3
import matplotlib.pyplot as plt
import os

os.makedirs("charts", exist_ok=True)
conn = sqlite3.connect("ewallet_analytics.db")
cur = conn.cursor()

# 1. Funnel data
cur.execute("SELECT COUNT(*) FROM merchant_orders")
created = cur.fetchone()[0]
cur.execute("SELECT COUNT(*) FROM merchant_orders WHERE status != 'Created'")
initiated = cur.fetchone()[0]
cur.execute("SELECT COUNT(*) FROM merchant_orders WHERE status = 'Paid'")
paid = cur.fetchone()[0]

# 2. Hourly latency data
cur.execute("""
    SELECT CAST(strftime('%H', trans_time) AS INTEGER) AS hr, ROUND(AVG(ipn_latency_ms), 0)
    FROM gateway_transactions
    WHERE ipn_latency_ms IS NOT NULL
    GROUP BY hr ORDER BY hr
""")
rows = cur.fetchall()
hours = [r[0] for r in rows]
latencies = [r[1] for r in rows]
conn.close()

fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(13, 5))
fig.suptitle("E-Wallet Post-Launch Analytics (30 Days • 10,500 Orders)", fontsize=14, fontweight="bold")

# Subplot 1: Checkout Funnel
steps = ["1. Order Created", "2. Gateway QR", "3. Paid"]
counts = [created, initiated, paid]
colors = ["#4f46e5", "#6366f1", "#10b981"]
bars = ax1.bar(steps, counts, color=colors, width=0.55)
ax1.set_title("Checkout Conversion Funnel")
ax1.set_ylabel("Orders")
ax1.set_ylim(0, created * 1.15)
for bar, cnt in zip(bars, counts):
    pct = cnt / created * 100
    ax1.text(bar.get_x() + bar.get_width()/2, cnt + 200, f"{cnt:,}\n({pct:.1f}%)", ha="center", fontsize=9, fontweight="bold")

# Subplot 2: Hourly IPN Latency
ax2.plot(hours, latencies, marker="o", color="#dc2626", linewidth=2)
ax2.axvspan(19, 21, color="#fee2e2", alpha=0.6, label="Peak Hours (19h–21h)")
ax2.set_title("Average IPN Latency by Hour of Day")
ax2.set_xlabel("Hour of Day (0–23)")
ax2.set_ylabel("Latency (ms)")
ax2.set_xticks(range(0, 24, 2))
ax2.grid(axis="y", linestyle="--", alpha=0.5)
ax2.legend()

plt.tight_layout()
plt.savefig("charts/dashboard_overview.png", dpi=150)
print("Saved charts/dashboard_overview.png")

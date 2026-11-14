import sqlite3
import random
from datetime import datetime, timedelta

DB_PATH = "ewallet_analytics.db"
NUM_ORDERS = 10500
random.seed(42)

def generate():
    conn = sqlite3.connect(DB_PATH)
    cur = conn.cursor()

    cur.executescript("""
    DROP TABLE IF EXISTS bank_settlements;
    DROP TABLE IF EXISTS gateway_transactions;
    DROP TABLE IF EXISTS merchant_orders;

    CREATE TABLE merchant_orders (
        order_id TEXT PRIMARY KEY,
        user_id TEXT NOT NULL,
        wallet_type TEXT NOT NULL, -- 'MOMO' or 'ZALOPAY'
        amount INTEGER NOT NULL,
        status TEXT NOT NULL,      -- 'Created', 'Paid', 'Expired', 'Failed'
        created_at TEXT NOT NULL,
        updated_at TEXT NOT NULL
    );

    CREATE TABLE gateway_transactions (
        trans_id TEXT PRIMARY KEY,
        order_id TEXT NOT NULL,
        wallet_type TEXT NOT NULL,
        gateway_amount INTEGER NOT NULL,
        ipn_status TEXT NOT NULL,  -- 'SUCCESS', 'TIMEOUT', 'FAILED', 'MISSING'
        ipn_latency_ms INTEGER,
        trans_time TEXT NOT NULL,
        FOREIGN KEY (order_id) REFERENCES merchant_orders(order_id)
    );

    CREATE TABLE bank_settlements (
        settlement_id TEXT PRIMARY KEY,
        trans_id TEXT NOT NULL,
        order_id TEXT NOT NULL,
        settled_amount INTEGER NOT NULL,
        mdr_fee INTEGER NOT NULL,
        settlement_date TEXT NOT NULL
    );
    """)

    start_date = datetime(2026, 10, 14, 0, 0, 0)
    orders = []
    transactions = []
    settlements = []

    for i in range(1, NUM_ORDERS + 1):
        order_id = f"ORD_{i:06d}"
        user_id = f"USR_{random.randint(1, 3800):05d}"
        wallet = random.choices(["MOMO", "ZALOPAY"], weights=[0.58, 0.42])[0]
        amount = random.choice([150000, 250000, 320000, 450000, 680000, 990000, 1250000])

        day_offset = random.randint(0, 29)
        # Giả lập giờ cao điểm 19h-22h có nhiều traffic hơn
        hour = random.choices(
            list(range(24)),
            weights=[1,1,1,1,1,2,3,4,5,6,6,7,7,6,6,6,7,8,10,14,15,12,6,3]
        )[0]
        minute = random.randint(0, 59)
        second = random.randint(0, 59)
        created_dt = start_date + timedelta(days=day_offset, hours=hour, minutes=minute, seconds=second)

        # Tỷ lệ trạng thái: ~72% Paid, ~15% Expired, ~8% Failed, ~5% Created (bỏ dở ngay)
        is_peak = 19 <= hour <= 21
        if is_peak:
            status = random.choices(["Paid", "Expired", "Failed", "Created"], weights=[0.66, 0.18, 0.11, 0.05])[0]
        else:
            status = random.choices(["Paid", "Expired", "Failed", "Created"], weights=[0.75, 0.14, 0.06, 0.05])[0]

        updated_dt = created_dt + timedelta(minutes=random.randint(1, 15))
        orders.append((order_id, user_id, wallet, amount, status, created_dt.isoformat(), updated_dt.isoformat()))

        if status != "Created":
            trans_id = f"{wallet[:2]}_{i:07d}"
            # IPN latency cao hơn vào giờ cao điểm
            base_latency = random.randint(800, 4200) if is_peak else random.randint(180, 1400)

            if status == "Paid":
                # 1.2% cố tình thiếu IPN hoặc timeout giả lập sự cố đối soát
                if random.random() < 0.012:
                    ipn_status = "MISSING"
                    latency = None
                else:
                    ipn_status = "SUCCESS"
                    latency = base_latency
                transactions.append((trans_id, order_id, wallet, amount, ipn_status, latency, updated_dt.isoformat()))

                # Bank settlement: 1.5% bị lệch tiền hoặc thiếu
                if random.random() < 0.015:
                    settled_amount = amount - random.choice([10000, 50000, 1000])
                else:
                    settled_amount = amount
                mdr_fee = int(settled_amount * (0.015 if wallet == "MOMO" else 0.013))
                settle_date = (updated_dt + timedelta(days=1)).strftime("%Y-%m-%d")
                settlements.append((f"STL_{i:06d}", trans_id, order_id, settled_amount, mdr_fee, settle_date))
            else:
                ipn_status = "TIMEOUT" if (status == "Expired" and random.random() < 0.25) else "FAILED"
                transactions.append((trans_id, order_id, wallet, amount, ipn_status, base_latency, updated_dt.isoformat()))

    cur.executemany("INSERT INTO merchant_orders VALUES (?,?,?,?,?,?,?)", orders)
    cur.executemany("INSERT INTO gateway_transactions VALUES (?,?,?,?,?,?,?)", transactions)
    cur.executemany("INSERT INTO bank_settlements VALUES (?,?,?,?,?,?)", settlements)

    conn.commit()
    conn.close()
    print(f"Generated {len(orders)} orders, {len(transactions)} gateway_transactions, {len(settlements)} bank_settlements in {DB_PATH}")

if __name__ == "__main__":
    generate()

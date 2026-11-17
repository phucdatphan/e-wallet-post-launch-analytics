-- ============================================================================
-- E-WALLET POST-LAUNCH FUNNEL & 3-WAY RECONCILIATION ANALYTICS
-- Database: SQLite (ewallet_analytics.db)
-- ============================================================================

-- 1. CHECKOUT FUNNEL & DROP-OFF RATE (Sử dụng CTE & Window Function)
-- Mục đích: Đo lường tỷ lệ chuyển đổi từ lúc Tạo đơn -> Sang Gateway -> Thanh toán thành công.
WITH funnel_counts AS (
    SELECT '1_Order_Created' AS step_name, 1 AS step_order, COUNT(*) AS total_orders
    FROM merchant_orders
    UNION ALL
    SELECT '2_Gateway_Initiated' AS step_name, 2 AS step_order, COUNT(*) AS total_orders
    FROM merchant_orders
    WHERE status != 'Created'
    UNION ALL
    SELECT '3_Payment_Success_Paid' AS step_name, 3 AS step_order, COUNT(*) AS total_orders
    FROM merchant_orders
    WHERE status = 'Paid'
)
SELECT
    step_name,
    total_orders,
    LAG(total_orders) OVER (ORDER BY step_order) AS prev_step_orders,
    ROUND(100.0 * total_orders / FIRST_VALUE(total_orders) OVER (ORDER BY step_order), 2) AS pct_of_total,
    ROUND(
        100.0 * (LAG(total_orders) OVER (ORDER BY step_order) - total_orders)
        / LAG(total_orders) OVER (ORDER BY step_order),
        2
    ) AS step_dropoff_pct
FROM funnel_counts
ORDER BY step_order;


-- 2. SYSTEM HEALTH: TỶ LỆ TIMEOUT & LỖI IPN THEO KHUNG GIỜ (Peak Hours Analysis)
-- Mục đích: Phát hiện khung giờ cao điểm gây nghẽn IPN / tăng tỷ lệ hết hạn.
SELECT
    CAST(strftime('%H', trans_time) AS INTEGER) AS hour_of_day,
    COUNT(*) AS total_tx,
    SUM(CASE WHEN ipn_status = 'TIMEOUT' THEN 1 ELSE 0 END) AS timeout_count,
    SUM(CASE WHEN ipn_status = 'MISSING' THEN 1 ELSE 0 END) AS missing_ipn_count,
    ROUND(100.0 * SUM(CASE WHEN ipn_status IN ('TIMEOUT', 'MISSING') THEN 1 ELSE 0 END) / COUNT(*), 2) AS issue_rate_pct,
    ROUND(AVG(ipn_latency_ms), 0) AS avg_latency_ms
FROM gateway_transactions
GROUP BY hour_of_day
ORDER BY issue_rate_pct DESC, total_tx DESC
LIMIT 10;


-- 3. WALLET PERFORMANCE: SO SÁNH HIỆU NĂNG MOMO VS ZALOPAY
-- Mục đích: Đánh giá tỷ lệ thành công, độ trễ IPN và tổng phí MDR theo từng ví.
SELECT
    o.wallet_type,
    COUNT(*) AS total_orders,
    SUM(CASE WHEN o.status = 'Paid' THEN 1 ELSE 0 END) AS paid_orders,
    ROUND(100.0 * SUM(CASE WHEN o.status = 'Paid' THEN 1 ELSE 0 END) / COUNT(*), 2) AS success_rate_pct,
    ROUND(AVG(g.ipn_latency_ms), 0) AS avg_ipn_latency_ms,
    COALESCE(SUM(b.mdr_fee), 0) AS total_mdr_fee_vnd
FROM merchant_orders o
LEFT JOIN gateway_transactions g ON o.order_id = g.order_id
LEFT JOIN bank_settlements b ON o.order_id = b.order_id
GROUP BY o.wallet_type;


-- 4. 3-WAY RECONCILIATION: ĐỐI SOÁT 3 BÊN (Merchant vs Gateway vs Bank)
-- Mục đích: Tìm chính xác các đơn hàng bị lệch tiền hoặc thiếu IPN để Kế toán xử lý.
SELECT
    o.order_id,
    o.wallet_type,
    o.amount AS merchant_amount,
    g.gateway_amount,
    b.settled_amount AS bank_settled_amount,
    g.ipn_status,
    CASE
        WHEN g.ipn_status = 'MISSING' THEN 'MISSING_IPN'
        WHEN o.amount != b.settled_amount THEN 'AMOUNT_MISMATCH'
        WHEN b.settlement_id IS NULL THEN 'MISSING_BANK_SETTLEMENT'
        ELSE 'MATCHED'
    END AS reconciliation_flag,
    (o.amount - COALESCE(b.settled_amount, 0)) AS discrepancy_vnd
FROM merchant_orders o
JOIN gateway_transactions g ON o.order_id = g.order_id
LEFT JOIN bank_settlements b ON o.order_id = b.order_id
WHERE o.status = 'Paid'
  AND (g.ipn_status = 'MISSING' OR o.amount != b.settled_amount OR b.settlement_id IS NULL)
ORDER BY ABS(o.amount - COALESCE(b.settled_amount, 0)) DESC
LIMIT 50;


-- 5. TỔNG HỢP THIỆT HẠI & SỐ LƯỢNG ĐƠN LỆCH ĐỐI SOÁT THEO LOẠI SỰ CỐ
-- Mục đích: Báo cáo nhanh cho Finance/Acc về tổng số tiền cần truy thu/đối soát lại.
WITH recon_issues AS (
    SELECT
        o.order_id,
        o.amount AS merchant_amount,
        COALESCE(b.settled_amount, 0) AS bank_settled_amount,
        CASE
            WHEN g.ipn_status = 'MISSING' THEN 'MISSING_IPN'
            WHEN o.amount != b.settled_amount THEN 'AMOUNT_MISMATCH'
            ELSE 'OTHER'
        END AS issue_type
    FROM merchant_orders o
    JOIN gateway_transactions g ON o.order_id = g.order_id
    LEFT JOIN bank_settlements b ON o.order_id = b.order_id
    WHERE o.status = 'Paid'
      AND (g.ipn_status = 'MISSING' OR o.amount != b.settled_amount)
)
SELECT
    issue_type,
    COUNT(*) AS affected_orders,
    SUM(merchant_amount - bank_settled_amount) AS total_discrepancy_vnd
FROM recon_issues
GROUP BY issue_type;


-- 6. DOANH THU HÀNG NGÀY & MOVING AVERAGE 7 NGÀY (Window Function)
-- Mục đích: Theo dõi xu hướng tăng trưởng GMV sau 30 ngày go-live.
WITH daily_gmv AS (
    SELECT
        DATE(created_at) AS order_date,
        COUNT(*) AS paid_orders,
        SUM(amount) AS gmv_vnd
    FROM merchant_orders
    WHERE status = 'Paid'
    GROUP BY DATE(created_at)
)
SELECT
    order_date,
    paid_orders,
    gmv_vnd,
    ROUND(AVG(gmv_vnd) OVER (ORDER BY order_date ROWS BETWEEN 6 PRECEDING AND CURRENT ROW), 0) AS ma7_gmv_vnd
FROM daily_gmv
ORDER BY order_date
LIMIT 15;


-- 7. USER RETENTION / REPEAT BUYERS BY WALLET
-- Mục đích: Đánh giá tỷ lệ khách hàng quay lại thanh toán từ 2 đơn trở lên.
WITH user_orders AS (
    SELECT
        user_id,
        wallet_type,
        COUNT(*) AS paid_count
    FROM merchant_orders
    WHERE status = 'Paid'
    GROUP BY user_id, wallet_type
)
SELECT
    wallet_type,
    COUNT(*) AS unique_paying_users,
    SUM(CASE WHEN paid_count >= 2 THEN 1 ELSE 0 END) AS repeat_users,
    ROUND(100.0 * SUM(CASE WHEN paid_count >= 2 THEN 1 ELSE 0 END) / COUNT(*), 2) AS repeat_rate_pct
FROM user_orders
GROUP BY wallet_type;


-- 8. CUT-OFF TIME & T+1 SETTLEMENT DATE MISMATCH (Nâng cao)
-- Mục đích: Phát hiện giao dịch sát nửa đêm (23:45 - 23:59) bị lệch ngày chốt sổ T+1 so với kỳ vọng.
SELECT
    o.order_id,
    o.wallet_type,
    o.created_at,
    b.settlement_date,
    JULIANDAY(b.settlement_date) - JULIANDAY(DATE(o.created_at)) AS settlement_lag_days
FROM merchant_orders o
JOIN bank_settlements b ON o.order_id = b.order_id
WHERE o.status = 'Paid'
  AND TIME(o.created_at) >= '23:45:00'
ORDER BY o.created_at DESC
LIMIT 15;

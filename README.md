<p align="center">
  <img src="https://img.shields.io/badge/Stage%203-Post--Launch%20Analytics-blueviolet?style=for-the-badge&logo=sqlite" alt="Stage 3" />
  <img src="https://img.shields.io/badge/SQL-CTE%20%26%20Window%20Functions-success?style=for-the-badge&logo=postgresql" alt="SQL" />
  <img src="https://img.shields.io/badge/Data-10%2C500%2B%20Orders%20%7C%203--Way%20Recon-informational?style=for-the-badge&logo=python" alt="Data" />
  <img src="https://img.shields.io/badge/License-MIT-orange?style=for-the-badge" alt="License" />
</p>

<h1 align="center">📊 E-Wallet Post-Launch Funnel & 3-Way Reconciliation Analytics</h1>

<h3 align="center">
  Stage 3: Phân tích Dữ liệu Sau Ra Mắt (30 Ngày Go-live), Đo lường Phễu Chuyển đổi & Đối soát Tài chính 3 Bên
</h3>

<p align="center">
  Dự án nối tiếp từ <strong>Stage 1</strong> và <strong>Stage 2</strong>, đóng vai trò IT Business Analyst sử dụng Python & SQL (CTE, Window Functions) để phân tích 10,500+ đơn hàng giả lập sau 1 tháng vận hành, phát hiện điểm nghẽn Drop-off, độ trễ giờ cao điểm và tìm chính xác các đơn lệch đối soát tài chính.
</p>

---

## 🔗 Chuỗi 3 Dự Án Liên Hoàn (E-Wallet Payment System)

| Giai đoạn | Tên Repo | Vai trò & Trọng tâm | Liên kết |
| :--- | :--- | :--- | :--- |
| **Stage 1** | **e-wallet-payment-simulator** | Core Backend Node.js, BRD/SRS, HMAC-SHA256, IPN | [Xem Repo Stage 1](https://github.com/phucdatphan/e-wallet-payment-simulator) |
| **Stage 2** | **e-wallet-checkout-ux-uat** | Wireframes Figma, 10 User Stories, 26 UAT Cases, Postman | [Xem Repo Stage 2](https://github.com/phucdatphan/e-wallet-checkout-ux-uat) |
| **Stage 3** *(Hiện tại)* | **e-wallet-post-launch-analytics** | 10,500+ Orders SQL Analytics, Funnel & Đối soát 3 bên | [Xem Repo Stage 3](https://github.com/phucdatphan/e-wallet-post-launch-analytics) |

---

## 📌 Mục Lục
- [1. Tổng quan Dữ liệu Giả lập (30 Ngày Go-live)](#-1-tổng-quan-dữ-liệu-giả-lập-30-ngày-go-live)
- [2. Executive Dashboard Summary (Kết quả Thực tế)](#-2-executive-dashboard-summary-kết-quả-thực-tế)
- [3. Key Insights & Đề xuất Cải tiến Sản phẩm](#-3-key-insights--đề-xuất-cải-tiến-sản-phẩm)
- [4. Cấu trúc Thư mục Dự án](#-4-cấu-trúc-thư-mục-dự-án)
- [5. Hướng dẫn Chạy lại Phân tích](#-5-hướng-dẫn-chạy-lại-phân-tích)

---

## 🗄️ 1. Tổng quan Dữ liệu Giả lập (30 Ngày Go-live)

Script `generate_data.py` sinh dữ liệu vào SQLite (`ewallet_analytics.db`) với 3 bảng khớp hoàn toàn với kiến trúc của **Stage 1**:
1. `merchant_orders` (**10,500** đơn hàng): Trạng thái `Created`, `Paid`, `Expired`, `Failed`.
2. `gateway_transactions` (**9,944** giao dịch): Log từ ví MoMo/ZaloPay kèm `ipn_status` và `ipn_latency_ms`.
3. `bank_settlements` (**7,550** bản ghi): Sao kê ngân hàng T+1, cố tình chèn ~1–2% giao dịch bị lệch tiền (`AMOUNT_MISMATCH`) hoặc thiếu IPN (`MISSING_IPN`).

---

## 📈 2. Executive Dashboard Summary (Kết quả Thực tế)

- **Figma Dashboard (Interactive)**: 👉 [Mở Dashboard trên Figma](https://www.figma.com/design/3KZYUyxTCNIUQi0isXUejF?node-id=3-3&autoplay-code-preview=3-3)

### 2.1 Checkout Funnel (Phễu chuyển đổi)
| Bước (Step) | Số đơn hàng | Tỷ lệ trên tổng | Tỷ lệ rớt bước (Drop-off) |
| :--- | :---: | :---: | :---: |
| **1. Order Created** | 10,500 | 100.00% | — |
| **2. Gateway Initiated (Mở QR)** | 9,944 | 94.70% | 5.30% |
| **3. Payment Success (Paid)** | 7,550 | 71.90% | **24.07%** |

```text
Order Created (10,500) ──[ -5.30% ]──> Gateway QR (9,944) ──[ -24.07% ]──> Paid (7,550)
```

### 2.2 Hiệu năng theo Ví điện tử (Wallet Performance)
| Ví điện tử | Tổng đơn | Đơn thành công | Success Rate | Avg IPN Latency | Tổng phí MDR (VNĐ) |
| :--- | :---: | :---: | :---: | :---: | :---: |
| **MoMo** | 6,010 | 4,307 | 71.66% | 1,309 ms | 38,103,495 đ |
| **ZaloPay** | 4,490 | 3,243 | 72.23% | 1,283 ms | 24,813,308 đ |

---

## 💡 3. Key Insights & Đề xuất Cải tiến Sản phẩm

1. **Điểm nghẽn lớn nhất ở bước Quét QR → Thanh toán (Drop-off 24.07%)**:
   - *Đề xuất*: Bổ sung nút **One-Tap Deep-link** mở thẳng app MoMo/ZaloPay trên Mobile Web và gửi thông báo nhắc ở phút thứ 10 trước khi hết hạn 15 phút.
2. **Độ trễ IPN tăng vọt 2.5x vào giờ cao điểm (19h–21h)**:
   - *Thực trạng*: `avg_ipn_latency_ms` tăng lên **2,313 – 2,502 ms**, tỷ lệ timeout/lỗi IPN ~5.6–5.9%.
   - *Đề xuất*: Triển khai **Message Queue (RabbitMQ/Kafka)** nhận IPN bất đồng bộ (trả `HTTP 200` trong `< 100ms`) và tăng tần suất **Active Polling** ở frontend.
3. **Phát hiện ~1–2% đơn lệch đối soát 3 bên (3-Way Reconciliation)**:
   - *Đề xuất*: Tự động hóa job đối soát lúc **01:30 AM hàng ngày**, xuất danh sách `AMOUNT_MISMATCH` và `MISSING_IPN` cho Kế toán xử lý T+1.
4. **Tối ưu chi phí MDR**:
   - *Đề xuất*: A/B Testing đặt **ZaloPay** (phí MDR 1.3% vs 1.5% của MoMo, tỷ lệ thành công 72.23%) làm lựa chọn gợi ý mặc định.

---

## 📂 4. Cấu trúc Thư mục Dự án

```text
e-wallet-post-launch-analytics/
├── dashboard/
│   └── index.html
├── generate_data.py
├── analytics_queries.sql
├── ewallet_analytics.db
└── README.md
```

---

## 🚀 5. Hướng dẫn Chạy lại Phân tích

```bash
# 1. Sinh 10,500+ dòng dữ liệu giả lập vào SQLite
python3 generate_data.py

# 2. Chạy toàn bộ 7 câu SQL Analytics (CTE & Window Functions)
sqlite3 -header -column ewallet_analytics.db < analytics_queries.sql
```

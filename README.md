# E-Wallet Post-Launch Funnel & 3-Way Reconciliation Analytics

> **Chuỗi 3 Dự án (E-Wallet Payment System)**:
> - **Stage 1 (Core Backend & BRD)**: [e-wallet-payment-simulator](https://github.com/phucdatphan/e-wallet-payment-simulator)
> - **Stage 2 (UX, Agile Spec & UAT)**: [e-wallet-checkout-ux-uat](https://github.com/phucdatphan/e-wallet-checkout-ux-uat)
> - **Stage 3 (Post-Launch Analytics & Reconciliation)** *(Repo hiện tại)*: [e-wallet-post-launch-analytics](https://github.com/phucdatphan/e-wallet-post-launch-analytics)
> - **Figma Dashboard**: https://www.figma.com/design/3KZYUyxTCNIUQi0isXUejF?node-id=3-3&autoplay-code-preview=3-3

> **Vai trò**: IT Business Analyst (Post-Launch Product & Financial Analytics)  
> **Dữ liệu giả lập**: 30 ngày vận hành thực tế (`10,500` đơn hàng, `9,944` giao dịch Gateway, `7,550` bản ghi đối soát ngân hàng).

---

## 1. Executive Dashboard Summary (Từ `ewallet_analytics.db`)

### 1.1 Checkout Funnel (Phễu chuyển đổi)
| Bước (Step) | Số đơn hàng | Tỷ lệ trên tổng | Tỷ lệ rớt bước (Drop-off) |
| :--- | :---: | :---: | :---: |
| **1. Order Created** | 10,500 | 100.00% | — |
| **2. Gateway Initiated (Mở QR)** | 9,944 | 94.70% | 5.30% |
| **3. Payment Success (Paid)** | 7,550 | 71.90% | **24.07%** |

```
Order Created (10,500) ──[ -5.30% ]──> Gateway QR (9,944) ──[ -24.07% ]──> Paid (7,550)
```

### 1.2 Hiệu năng theo Ví điện tử (Wallet Performance)
| Ví điện tử | Tổng đơn | Đơn thành công | Success Rate | Avg IPN Latency | Tổng phí MDR (VNĐ) |
| :--- | :---: | :---: | :---: | :---: | :---: |
| **MoMo** | 6,010 | 4,307 | 71.66% | 1,309 ms | 38,103,495 đ |
| **ZaloPay** | 4,490 | 3,243 | 72.23% | 1,283 ms | 24,813,308 đ |

---

## 2. Key Insights & Đề xuất Cải tiến Sản phẩm (Product Recommendations)

### Insight 1: Điểm nghẽn lớn nhất nằm ở bước Quét QR → Thanh toán (Drop-off 24.07%)
- **Thực trạng**: Có tới **24.07%** người dùng đã mở màn hình QR nhưng không hoàn tất thanh toán (hết hạn 15 phút hoặc hủy giữa chừng).
- **Đề xuất**:
  1. Bổ sung nút **One-Tap Deep-link** nổi bật hơn trên Mobile Web để tự động mở app MoMo/ZaloPay thay vì bắt user tự chụp màn hình QR.
  2. Gửi thông báo nhắc nhở (Push/In-app) ở phút thứ 10 trước khi hết hạn 15 phút.

### Insight 2: Độ trễ IPN tăng vọt gấp 2.5x vào khung giờ cao điểm (19h–21h)
- **Thực trạng**: Khung giờ `19:00 - 21:59` có lượng giao dịch cao nhất (~1,000 giao dịch/giờ), kéo theo `avg_ipn_latency_ms` tăng lên **2,313 - 2,502 ms** (so với ~800 ms giờ bình thường) và tỷ lệ timeout/lỗi IPN ~5.6–5.9%.
- **Đề xuất**:
  1. Triển khai **Message Queue (RabbitMQ/Kafka)** để nhận IPN bất đồng bộ, trả `HTTP 200` ngay cho Gateway trong `< 100ms` rồi mới xử lý trừ kho.
  2. Tăng tần suất **Active Polling (`POST /v2/gateway/pay/query`)** ở frontend vào khung giờ cao điểm nếu IPN chưa về sau 3 giây.

### Insight 3: Phát hiện ~1–2% đơn hàng lệch đối soát 3 bên (3-Way Reconciliation)
- **Thực trạng**: Câu query đối soát 3 bên phát hiện chính xác các đơn `AMOUNT_MISMATCH` (lệch 1,000đ - 50,000đ giữa `merchant_orders` và `bank_settlements`) và `MISSING_IPN` (tiền đã về ngân hàng nhưng log IPN bị mất).
- **Đề xuất**:
  1. Tự động chạy job đối soát 3 bên lúc **01:30 AM hàng ngày** và xuất danh sách `DISCREPANCY_FLAG` sang Slack/Email cho bộ phận Kế toán.
  2. Bắt buộc kiểm tra `order.amount === ipn.amount` ở tầng Backend trước khi chốt `Paid`.

### Insight 4: Tối ưu chi phí MDR bằng điều hướng ví mặc định
- **Thực trạng**: ZaloPay có tỷ lệ thành công nhỉnh hơn (72.23% vs 71.66%) và mức phí MDR thấp hơn (1.3% vs 1.5%).
- **Đề xuất**: Thử nghiệm A/B Testing đặt ZaloPay làm lựa chọn gợi ý mặc định hoặc kết hợp voucher đồng tài trợ để tối ưu chi phí MDR trên tổng GMV.

---

## 3. Hướng dẫn chạy lại phân tích
```bash
# 1. Sinh 10,500+ dòng dữ liệu giả lập
python3 generate_data.py

# 2. Chạy toàn bộ 7 câu SQL Analytics
sqlite3 -header -column ewallet_analytics.db < analytics_queries.sql
```

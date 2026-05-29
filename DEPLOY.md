# 🚀 HƯỚNG DẪN DEPLOY LÊN RENDER.COM

## Bước 1: Đẩy code lên GitHub

1. Vào github.com → New repository
2. Đặt tên: `shopee-fanpage-bot`
3. Tạo repo (để Private nếu muốn bảo mật)
4. Chạy các lệnh sau trong CMD:

```bash
cd shopee_bot_web
git init
git add .
git commit -m "first commit"
git branch -M main
git remote add origin https://github.com/TÊN_BẠN/shopee-fanpage-bot.git
git push -u origin main
```

---

## Bước 2: Deploy lên Render.com

1. Vào **render.com** → Đăng ký miễn phí bằng GitHub
2. Nhấn **New +** → **Web Service**
3. Chọn repo `shopee-fanpage-bot`
4. Cấu hình:
   - **Name**: shopee-bot
   - **Runtime**: Python 3
   - **Build Command**: `pip install -r requirements.txt`
   - **Start Command**: `gunicorn app:app --workers 1 --threads 2 --timeout 120`
   - **Plan**: **Free**

---

## Bước 3: Thêm API Keys (QUAN TRỌNG)

Trong Render → Service → **Environment** → Add variables:

| Key | Value |
|-----|-------|
| `GEMINI_API_KEY` | key Gemini của bạn |
| `COMPOSIO_API_KEY` | key Composio của bạn |
| `COMPOSIO_ENTITY_ID` | default |
| `POST_HOUR_1` | 11 |
| `POST_MIN_1` | 30 |
| `POST_HOUR_2` | 20 |
| `POST_MIN_2` | 0 |

---

## Bước 4: Deploy!

Nhấn **Create Web Service** → Đợi ~3 phút deploy xong.

Render sẽ cho bạn URL dạng: `https://shopee-bot-xxxx.onrender.com`

Mở URL đó là thấy dashboard!

---

## ⚠️ LƯU Ý RENDER FREE

- Free tier sẽ **ngủ sau 15 phút không có request**
- Để bot chạy 24/7, dùng **UptimeRobot** (miễn phí) ping URL mỗi 10 phút:
  1. Vào uptimerobot.com → New Monitor
  2. Type: HTTP(s)
  3. URL: `https://shopee-bot-xxxx.onrender.com`
  4. Interval: 10 phút
  → Bot sẽ không bao giờ ngủ!

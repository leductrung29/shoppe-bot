"""
===========================================
  SHOPEE AFFILIATE AUTO POST BOT - WEB
  Flask + APScheduler + Groq + Composio
===========================================
"""

import os, json, random, logging, requests, time
from datetime import datetime
from flask import Flask, render_template, jsonify, request
from apscheduler.schedulers.background import BackgroundScheduler
from apscheduler.triggers.cron import CronTrigger
from groq import Groq
from composio import Composio, Action
from dotenv import load_dotenv

load_dotenv()

app = Flask(__name__)
logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
log = logging.getLogger(__name__)

# ── Config ───────────────────────────────────────────────────
GROQ_API_KEY     = os.getenv("GROQ_API_KEY", "")
COMPOSIO_API_KEY = os.getenv("COMPOSIO_API_KEY", "")
ENTITY_ID        = os.getenv("COMPOSIO_ENTITY_ID", "default")
POST_HOUR_1      = int(os.getenv("POST_HOUR_1", "11"))
POST_MIN_1       = int(os.getenv("POST_MIN_1", "30"))
POST_HOUR_2      = int(os.getenv("POST_HOUR_2", "20"))
POST_MIN_2       = int(os.getenv("POST_MIN_2", "0"))

# ── State in memory ──────────────────────────────────────────
bot_status = {
    "running": False,
    "total_posts": 0,
    "success_posts": 0,
    "last_post_time": None,
    "last_post_preview": None,
    "last_image_url": None,
    "logs": [],
    "next_post_time": None,
}

HISTORY_FILE = "posts_history.json"

SHOPEE_CATEGORIES = [
    "điện thoại, phụ kiện điện thoại",
    "tai nghe bluetooth, loa mini",
    "đồng hồ thông minh, smartwatch",
    "đồ gia dụng thông minh, robot hút bụi",
    "mỹ phẩm skincare, kem chống nắng",
    "son môi, phấn má hồng GenZ",
    "quần áo thời trang GenZ streetwear",
    "giày sneaker, dép trendy",
    "túi xách nữ, balo nam aesthetic",
    "đèn LED trang trí phòng",
    "thiết bị gaming, bàn phím cơ",
    "đồ ăn vặt, snack Hàn Quốc",
    "vitamin, thực phẩm chức năng",
    "đồ tập gym, yoga mat",
    "nước hoa mini set",
    "kính mắt thời trang, lens màu",
    "phụ kiện tóc, kẹp tóc viral TikTok",
    "đồ decor bàn học aesthetic",
    "máy ảnh mini, máy in ảnh Polaroid",
    "ốp lưng điện thoại trendy",
]

def add_log(msg, level="info"):
    entry = {"time": datetime.now().strftime("%H:%M:%S"), "msg": msg, "level": level}
    bot_status["logs"].insert(0, entry)
    bot_status["logs"] = bot_status["logs"][:100]
    getattr(log, level)(msg)

def load_history():
    if os.path.exists(HISTORY_FILE):
        with open(HISTORY_FILE, "r", encoding="utf-8") as f:
            return json.load(f)
    return []

def save_history(entry):
    history = load_history()
    history.insert(0, entry)
    with open(HISTORY_FILE, "w", encoding="utf-8") as f:
        json.dump(history[:200], f, ensure_ascii=False, indent=2)

# ── Generate content via Groq ─────────────────────────────────
def generate_post_content():
    client = Groq(api_key=GROQ_API_KEY)
    category = random.choice(SHOPEE_CATEGORIES)
    month = datetime.now().strftime("%m/%Y")

    prompt = f"""Bạn là chuyên gia affiliate Shopee, viết content GenZ cực viral cho Facebook Fanpage.

Nhiệm vụ:
1. Nghĩ ra 1 sản phẩm đang HOT trên Shopee tháng {month} thuộc danh mục: {category}
2. Viết 1 bài đăng Facebook theo phong cách GenZ Việt Nam

YÊU CẦU:
- Dài 150-250 từ
- Tone: vui vẻ, thân thiện, dùng tiếng lóng GenZ (iu, ib, btw, fr, gg, xịn xò, v.v.)
- Mở đầu có hook gây tò mò hoặc đặt câu hỏi
- Nêu rõ: tên sản phẩm, giá tầm bao nhiêu, lý do nên mua
- Nhiều emoji phù hợp
- Kết thúc CTA: kêu gọi comment, tag bạn bè
- Chỉ 3-5 hashtag cuối bài
- Câu kết PHẢI có: "Link Shopee 🛒 [trong bio / comment bên dưới nha!]"

CHỈ trả về nội dung bài viết, không giải thích."""

    add_log(f"🤖 Groq đang tạo content cho: {category}")
    response = client.chat.completions.create(
        model="llama-3.3-70b-versatile",
        messages=[{"role": "user", "content": prompt}],
        max_tokens=1000,
    )
    content = response.choices[0].message.content.strip()
    add_log(f"✅ Tạo content xong ({len(content)} ký tự)")
    return content, category

# ── Generate image via Pollinations ──────────────────────────
def generate_image_url(category):
    prompts = {
        "điện thoại": "modern smartphone product photography white background professional",
        "tai nghe": "wireless earbuds aesthetic background trendy product shot",
        "đồng hồ": "smartwatch elegant lifestyle photography",
        "mỹ phẩm": "skincare products flat lay pastel Korean aesthetic",
        "son môi": "lipstick collection pink aesthetic beauty photography",
        "quần áo": "trendy outfit flatlay aesthetic GenZ fashion streetwear",
        "giày": "sneakers product photography clean streetwear aesthetic",
        "túi": "handbag product photography elegant fashion",
        "đèn LED": "LED room decoration aesthetic bedroom colorful lights",
        "gaming": "gaming setup RGB lights aesthetic desk",
        "snack": "Korean snacks colorful flat lay food photography",
        "máy ảnh": "polaroid mini camera aesthetic pastel background",
        "ốp lưng": "phone case collection aesthetic trendy colorful",
    }
    base_prompt = "trendy Shopee product photography colorful aesthetic GenZ Vietnam"
    for key, val in prompts.items():
        if key in category:
            base_prompt = val
            break

    encoded = requests.utils.quote(base_prompt)
    seed = random.randint(1, 99999)
    url = f"https://image.pollinations.ai/prompt/{encoded}?width=1200&height=630&seed={seed}&nologo=true"
    add_log(f"🎨 Tạo ảnh AI: seed={seed}")
    return url

# ── Post to Facebook via Composio ────────────────────────────
def post_to_facebook(content, image_url):
    try:
        client = Composio(api_key=COMPOSIO_API_KEY)
        entity = client.get_entity(id=ENTITY_ID)
        add_log("📤 Đang gửi lên Facebook Fanpage...")

        result = entity.execute(
            action=Action.FACEBOOK_CREATE_PHOTO_POST,
            params={"message": content, "url": image_url}
        )
        if result and result.get("successfull", False):
            add_log("🎉 Đăng bài thành công!")
            return True

        result2 = entity.execute(
            action=Action.FACEBOOK_CREATE_POST,
            params={"message": f"{content}\n\n📸 {image_url}"}
        )
        add_log(f"📝 Fallback post hoàn tất")
        return True
    except Exception as e:
        add_log(f"❌ Lỗi Composio: {e}", "error")
        return False

# ── Main job ──────────────────────────────────────────────────
def run_post_job():
    add_log("=" * 40)
    add_log(f"🚀 Bắt đầu đăng bài lúc {datetime.now().strftime('%H:%M %d/%m/%Y')}")
    bot_status["total_posts"] += 1

    try:
        content, category = generate_post_content()
        image_url = generate_image_url(category)
        time.sleep(4)
        success = post_to_facebook(content, image_url)

        bot_status["last_post_time"] = datetime.now().strftime("%H:%M %d/%m/%Y")
        bot_status["last_post_preview"] = content[:120] + "..."
        bot_status["last_image_url"] = image_url

        if success:
            bot_status["success_posts"] += 1

        save_history({
            "time": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            "category": category,
            "preview": content[:120] + "...",
            "image_url": image_url,
            "success": success
        })
        add_log("✅ Job hoàn thành!" if success else "⚠️ Job kết thúc nhưng có lỗi")
    except Exception as e:
        add_log(f"💥 Lỗi: {e}", "error")

# ── Scheduler ─────────────────────────────────────────────────
scheduler = BackgroundScheduler(timezone="Asia/Ho_Chi_Minh")

def start_scheduler():
    if scheduler.running:
        scheduler.remove_all_jobs()
    else:
        scheduler.start()

    scheduler.add_job(run_post_job, CronTrigger(hour=POST_HOUR_1, minute=POST_MIN_1), id="post1", replace_existing=True)
    scheduler.add_job(run_post_job, CronTrigger(hour=POST_HOUR_2, minute=POST_MIN_2), id="post2", replace_existing=True)
    bot_status["running"] = True
    add_log(f"⏰ Bot chạy! Lịch: {POST_HOUR_1:02d}:{POST_MIN_1:02d} và {POST_HOUR_2:02d}:{POST_MIN_2:02d}")

# ── Flask routes ──────────────────────────────────────────────
@app.route("/")
def index():
    return render_template("index.html")

@app.route("/api/status")
def api_status():
    jobs = scheduler.get_jobs() if scheduler.running else []
    next_times = [str(j.next_run_time) for j in jobs if j.next_run_time]
    return jsonify({**bot_status, "next_runs": next_times, "scheduler_running": scheduler.running})

@app.route("/api/start", methods=["POST"])
def api_start():
    if not GROQ_API_KEY or not COMPOSIO_API_KEY:
        return jsonify({"ok": False, "msg": "Thiếu API key! Kiểm tra biến môi trường."})
    start_scheduler()
    return jsonify({"ok": True, "msg": "Bot đã khởi động!"})

@app.route("/api/stop", methods=["POST"])
def api_stop():
    if scheduler.running:
        scheduler.pause()
    bot_status["running"] = False
    add_log("⏸️ Bot đã tạm dừng")
    return jsonify({"ok": True, "msg": "Bot đã dừng"})

@app.route("/api/post-now", methods=["POST"])
def api_post_now():
    if not GROQ_API_KEY or not COMPOSIO_API_KEY:
        return jsonify({"ok": False, "msg": "Thiếu API key!"})
    import threading
    threading.Thread(target=run_post_job).start()
    return jsonify({"ok": True, "msg": "Đang tạo và đăng bài..."})

@app.route("/api/history")
def api_history():
    return jsonify(load_history())

@app.route("/api/logs")
def api_logs():
    return jsonify(bot_status["logs"])

# ── Start ─────────────────────────────────────────────────────
if __name__ == "__main__":
    if GROQ_API_KEY and COMPOSIO_API_KEY:
        start_scheduler()
    app.run(host="0.0.0.0", port=int(os.getenv("PORT", 5000)))

import os

TOKEN = os.environ.get("TOKEN", "")
ADMIN_ID = int(os.environ.get("ADMIN_ID", 0))
DANA_ADMIN = os.environ.get("DANA_ADMIN", "085864539634")
MONGO_URL = os.environ.get("MONGO_URL", "")

MIN_WD = 10000
KOMISI_REFERRAL = 1500
KOMISI_PERAPPROVE = 1000
CHANNEL_ID = "@Freelanceapkbot_Info"
BOT_REKOMENDASI = [
    {"nama": "Bot Top Up Game", "link": "https://t.me/XyroStoreBot"}
]

from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup, ReplyKeyboardMarkup
from telegram.ext import ApplicationBuilder, CommandHandler, CallbackQueryHandler, MessageHandler, ContextTypes, filters
from datetime import datetime

from config import TOKEN, CHANNEL_USERNAME
from db import *

# =========================
# CEK MEMBER CHANNEL
# =========================
async def is_member(bot, user_id):
    try:
        member = await bot.get_chat_member(CHANNEL_USERNAME, user_id)
        return member.status in ["member", "administrator", "creator"]
    except:
        return False

# =========================
# START
# =========================
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    user_id = user.id

    create_user(user_id, user.full_name)

    if not await is_member(context.bot, user_id):
        keyboard = [
            [InlineKeyboardButton("📢 JOIN CHANNEL", url=f"https://t.me/{CHANNEL_USERNAME.replace('@','')}")],
            [InlineKeyboardButton("🔄 SUDAH JOIN", callback_data="check_join")]
        ]

        await update.message.reply_text(
            "⚠️ Kamu harus join channel dulu!",
            reply_markup=InlineKeyboardMarkup(keyboard)
        )
        return

    await dashboard(update, context)

# =========================
# CHECK JOIN
# =========================
async def check_join(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    user_id = query.from_user.id

    if await is_member(context.bot, user_id):
        await query.message.delete()
        await dashboard(update, context)
    else:
        await query.answer("Belum join!", show_alert=True)

# =========================
# DASHBOARD
# =========================
async def dashboard(update, context):
    user = update.effective_user
    user_id = user.id
    now = datetime.now()

    saldo = get_saldo(user_id)

    text = (
        f"🌙 Halo {user.first_name}\n\n"
        f"📅 {now.strftime('%d-%m-%Y')}\n"
        f"🕐 {now.strftime('%H:%M:%S')}\n\n"
        f"💰 Saldo: Rp {saldo:,}\n"
    )

    keyboard = [
        ["📌 TUGAS", "💰 SALDO"],
        ["🏧 TARIK SALDO", "👥 REFERRAL"],
        ["📜 RIWAYAT", "ℹ️ INFO"]
    ]

    await update.message.reply_text(
        text,
        reply_markup=ReplyKeyboardMarkup(keyboard, resize_keyboard=True)
    )

# =========================
# SALDO
# =========================
async def saldo(update, context):
    user_id = update.effective_user.id
    saldo = get_saldo(user_id)

    await update.message.reply_text(f"💰 SALDO: Rp {saldo:,}")

# =========================
# TUGAS
# =========================
async def tugas(update, context):
    await update.message.reply_text("📌 Tugas tersedia:\n- Install App\n- Register\n- Screenshot")

# =========================
# TARIK SALDO
# =========================
async def tarik(update, context):
    await update.message.reply_text("🏧 Minimal WD 10.000\nPilih nominal lalu kirim nomor DANA kamu")

# =========================
# REFERRAL
# =========================
async def referral(update, context):
    user_id = update.effective_user.id
    bot_username = context.bot.username

    link = f"https://t.me/{bot_username}?start={user_id}"

    await update.message.reply_text(
        f"👥 Referral link:\n{link}\n\n💰 Bonus: 2000 per user"
    )

# =========================
# HANDLE TEXT
# =========================
async def handle(update, context):
    text = update.message.text

    if text == "📌 TUGAS":
        await tugas(update, context)

    elif text == "💰 SALDO":
        await saldo(update, context)

    elif text == "🏧 TARIK SALDO":
        await tarik(update, context)

    elif text == "👥 REFERRAL":
        await referral(update, context)

    elif text == "📜 RIWAYAT":
        await update.message.reply_text("📜 Belum ada riwayat")

    elif text == "ℹ️ INFO":
        await update.message.reply_text("ℹ️ Bot freelance system v1")

# =========================
# BOT RUN
# =========================
app = ApplicationBuilder().token(TOKEN).build()

app.add_handler(CommandHandler("start", start))
app.add_handler(CallbackQueryHandler(check_join, pattern="check_join"))
app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle))

print("Bot jalan...")
app.run_polling()

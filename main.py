from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup, ReplyKeyboardMarkup, KeyboardButton
from telegram.ext import Application, CommandHandler, MessageHandler, CallbackQueryHandler, filters, ContextTypes
from config import TOKEN, ADMIN_ID, DANA_ADMIN, MIN_WD, KOMISI_REFERRAL, KOMISI_PERAPPROVE, BOT_REKOMENDASI, CHANNEL_ID
from database import *
import logging

logging.basicConfig(level=logging.INFO)

# ===== KEYBOARD MENU BAWAH =====
def main_keyboard():
    keyboard = [
        [KeyboardButton("📋 Tugas"), KeyboardButton("💰 Saldo")],
        [KeyboardButton("💸 Tarik Saldo"), KeyboardButton("👥 Referral")],
        [KeyboardButton("📜 Riwayat"), KeyboardButton("ℹ️ Info")]
    ]
    return ReplyKeyboardMarkup(keyboard, resize_keyboard=True)

# ===== CEK MEMBER CHANNEL =====
async def is_member(bot, user_id):
    try:
        member = await bot.get_chat_member(chat_id=CHANNEL_ID, user_id=user_id)
        return member.status in ["member", "administrator", "creator"]
    except:
        return False

async def send_join_prompt(message):
    keyboard = [[
        InlineKeyboardButton("📢 Gabung Channel", url=f"https://t.me/{CHANNEL_ID.lstrip('@')}"),
        InlineKeyboardButton("✅ Sudah Gabung", callback_data="cek_member")
    ]]
    await message.reply_text(
        f"⚠️ *Kamu belum join channel kami!*\n\n"
        f"Wajib join channel dulu sebelum menggunakan bot:\n"
        f"👉 {CHANNEL_ID}\n\n"
        f"Setelah join, klik tombol *Sudah Gabung* di bawah.",
        parse_mode="Markdown",
        reply_markup=InlineKeyboardMarkup(keyboard)
    )

# ===== START =====
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    user_id = user.id

    if not await is_member(context.bot, user_id):
        await send_join_prompt(update.message)
        return

    is_new_user = get_user(user_id) is None

    referred_by = None
    if is_new_user and context.args:
        ref_code = context.args[0]
        referrer = get_referral_by_code(ref_code)
        if referrer and referrer[0] != user_id:
            referred_by = referrer[0]
            # Kasih komisi ke referrer hanya untuk user baru
            update_saldo(referrer[0], KOMISI_REFERRAL)
            try:
                await context.bot.send_message(
                    chat_id=referrer[0],
                    text=f"🎉 *Teman baru bergabung!*\nKamu dapat komisi Rp {KOMISI_REFERRAL:,}!",
                    parse_mode="Markdown"
                )
            except:
                pass

    ref_code = f"REF{user_id}"
    create_user(user_id, user.username or "", user.full_name or "", ref_code, referred_by)
    db_user = get_user(user_id)
    saldo = db_user[3] if db_user else 0
    total_users = get_total_users()

    text = (
        f"👋 Halo, *{user.full_name}*!\n\n"
        f"🤖 *FREELANCE APK BOT*\n"
        f"━━━━━━━━━━━━━━━━━━\n"
        f"👤 ID: `{user_id}`\n"
        f"💰 Saldo: *Rp {saldo:,}*\n"
        f"👥 Total Member: {total_users}\n"
        f"━━━━━━━━━━━━━━━━━━\n"
        f"Pilih menu di bawah 👇"
    )
    await update.message.reply_text(text, parse_mode="Markdown", reply_markup=main_keyboard())

# ===== HANDLER TEKS =====
async def text_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    text = update.message.text
    user_id = update.effective_user.id

    if not await is_member(context.bot, user_id):
        await send_join_prompt(update.message)
        return

    # Reset semua state jika user pencet tombol menu
    menu_buttons = ["📋 Tugas", "💰 Saldo", "💳 Deposit", "💸 Tarik Saldo", "👥 Referral", "📜 Riwayat", "🤖 Bot Lainnya", "ℹ️ Info"]
    if text in menu_buttons:
        context.user_data["input_wd"] = False
        context.user_data["input_wd_nomor"] = False
        context.user_data["wd_jumlah"] = None
        context.user_data["input_deposit_jumlah"] = False
        context.user_data["input_deposit_bukti"] = False
        context.user_data["broadcast_mode"] = False
        context.user_data["addtask_mode"] = False
        context.user_data["ambil_tugas"] = None

    # Cek mode input (hanya jika bukan tombol menu)
    else:
        if context.user_data.get("input_wd_nomor"):
            await proses_wd_nomor(update, context)
            return
        if context.user_data.get("input_wd"):
            await proses_wd(update, context)
            return
        if context.user_data.get("input_deposit_jumlah"):
            try:
                jumlah = int(text.replace(".", "").replace(",", ""))
                context.user_data["deposit_jumlah"] = jumlah
                context.user_data["input_deposit_jumlah"] = False
                context.user_data["input_deposit_bukti"] = True
                await update.message.reply_text(
                    f"💳 Transfer Rp {jumlah:,} ke DANA:\n`{DANA_ADMIN}`\n\nLalu kirim *screenshot bukti transfer*!",
                    parse_mode="Markdown"
                )
            except:
                await update.message.reply_text("❌ Format salah! Ketik angka saja.\nContoh: `50000`", parse_mode="Markdown")
            return
        if context.user_data.get("broadcast_mode"):
            await do_broadcast(update, context)
            return
        if context.user_data.get("addtask_mode"):
            await do_addtask(update, context)
            return

    # Menu utama
    if text == "📋 Tugas":
        await show_tugas(update, context)
    elif text == "💰 Saldo":
        await show_saldo(update, context)
    elif text == "💳 Deposit":
        await show_deposit(update, context)
    elif text == "💸 Tarik Saldo":
        await show_wd(update, context)
    elif text == "👥 Referral":
        await show_referral(update, context)
    elif text == "📜 Riwayat":
        await show_riwayat_menu(update, context)
    elif text == "🤖 Bot Lainnya":
        await show_bot_lainnya(update, context)
    elif text == "ℹ️ Info":
        await show_info(update, context)

# ===== TUGAS =====
async def show_tugas(update: Update, context: ContextTypes.DEFAULT_TYPE):
    tasks = get_active_tasks()
    if not tasks:
        await update.message.reply_text("🖕tugas belum tersedia anjing sabar lah🖕.\nCoba lagi nanti!")
        return

    text = "📋 *DAFTAR TUGAS*\n━━━━━━━━━━━━━━━━━━\n\n"
    keyboard = []
    for task in tasks:
        task_id, nama, link, bayaran, stok, aktif, _ = task
        stok_text = "♾️" if stok == -1 else str(stok)
        text += f"📱 *{nama}*\n💰 Bayaran: Rp {bayaran:,} | Stok: {stok_text}\n\n"
        keyboard.append([InlineKeyboardButton(f"✅ Ambil: {nama}", callback_data=f"ambil_{task_id}")])

    await update.message.reply_text(text, parse_mode="Markdown", reply_markup=InlineKeyboardMarkup(keyboard))

# ===== SALDO =====
async def show_saldo(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    db_user = get_user(user_id)
    saldo = db_user[3] if db_user else 0
    total_tugas = get_user_task_count(user_id)

    await update.message.reply_text(
        f"💰 *SALDO KAMU*\n━━━━━━━━━━━━━━━━━━\n"
        f"💵 Saldo: *Rp {saldo:,}*\n"
        f"📋 Total Tugas: {total_tugas}\n"
        f"📌 Min WD: Rp {MIN_WD:,}",
        parse_mode="Markdown"
    )

# ===== WD =====
async def show_wd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    db_user = get_user(user_id)
    saldo = db_user[3] if db_user else 0

    if saldo < MIN_WD:
        await update.message.reply_text(
            f"❌ Saldo tidak cukup!\n💰 Saldo: Rp {saldo:,}\n📌 Min WD: Rp {MIN_WD:,}"
        )
        return

    keyboard = [
        [
            InlineKeyboardButton("Rp 2.000", callback_data="wd_nominal_2000"),
            InlineKeyboardButton("Rp 5.000", callback_data="wd_nominal_5000"),
            InlineKeyboardButton("Rp 10.000", callback_data="wd_nominal_10000"),
        ],
        [
            InlineKeyboardButton("Rp 50.000", callback_data="wd_nominal_50000"),
            InlineKeyboardButton("Rp 100.000", callback_data="wd_nominal_100000"),
        ],
        [InlineKeyboardButton("✏️ Ketik Manual", callback_data="wd_manual")]
    ]
    await update.message.reply_text(
        f"💸 *TARIK SALDO*\n━━━━━━━━━━━━━━━━━━\n"
        f"💰 Saldo: *Rp {saldo:,}*\n"
        f"📌 Min WD: Rp {MIN_WD:,}\n"
        f"📊 Fee: 1.5%\n\n"
        f"Pilih nominal atau ketik manual:",
        parse_mode="Markdown",
        reply_markup=InlineKeyboardMarkup(keyboard)
    )

async def proses_wd_nomor(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    nomor = update.message.text.strip()
    jumlah = context.user_data.get("wd_jumlah", 0)

    db_user = get_user(user_id)
    saldo = db_user[3] if db_user else 0

    if jumlah < MIN_WD:
        await update.message.reply_text(f"❌ Minimal WD Rp {MIN_WD:,}")
        context.user_data["input_wd_nomor"] = False
        return
    if jumlah > saldo:
        await update.message.reply_text(f"❌ Saldo tidak cukup! Saldo kamu: Rp {saldo:,}")
        context.user_data["input_wd_nomor"] = False
        return

    fee = round(jumlah * 0.015)
    diterima = jumlah - fee

    wd_id = create_withdrawal(user_id, jumlah, nomor)
    update_saldo(user_id, -jumlah)
    context.user_data["input_wd_nomor"] = False
    context.user_data["wd_jumlah"] = None

    keyboard = [[
        InlineKeyboardButton("✅ APPROVE", callback_data=f"awd_{wd_id}_{user_id}_{jumlah}"),
        InlineKeyboardButton("❌ REJECT", callback_data=f"rwd_{wd_id}_{user_id}_{jumlah}")
    ]]
    await context.bot.send_message(
        chat_id=ADMIN_ID,
        text=f"💸 *WD BARU*\n👤 ID: `{user_id}`\n💰 Rp {jumlah:,}\n💳 Fee: Rp {fee:,}\n📤 Dikirim: Rp {diterima:,}\n📱 DANA: `{nomor}`\n🆔 WD#{wd_id}",
        parse_mode="Markdown",
        reply_markup=InlineKeyboardMarkup(keyboard)
    )
    await update.message.reply_text(
        f"✅ *Permintaan WD dikirim!*\n━━━━━━━━━━━━━━━━━━\n"
        f"💰 Jumlah WD: Rp {jumlah:,}\n"
        f"📊 Fee (1.5%): Rp {fee:,}\n"
        f"📤 Kamu terima: *Rp {diterima:,}*\n"
        f"📱 DANA: `{nomor}`\n"
        f"⏳ Diproses dalam 1x24 jam",
        parse_mode="Markdown"
    )

async def proses_wd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    try:
        parts = update.message.text.split("|")
        jumlah = int(parts[0].strip())
        nomor = parts[1].strip()
    except:
        await update.message.reply_text("❌ Format salah!\nContoh: `50000|081234567890`", parse_mode="Markdown")
        return

    db_user = get_user(user_id)
    saldo = db_user[3] if db_user else 0

    if jumlah < MIN_WD:
        await update.message.reply_text(f"❌ Minimal WD Rp {MIN_WD:,}")
        return
    if jumlah > saldo:
        await update.message.reply_text(f"❌ Saldo tidak cukup!")
        return

    fee = round(jumlah * 0.015)
    diterima = jumlah - fee

    wd_id = create_withdrawal(user_id, jumlah, nomor)
    update_saldo(user_id, -jumlah)
    context.user_data["input_wd"] = False

    keyboard = [[
        InlineKeyboardButton("✅ APPROVE", callback_data=f"awd_{wd_id}_{user_id}_{jumlah}"),
        InlineKeyboardButton("❌ REJECT", callback_data=f"rwd_{wd_id}_{user_id}_{jumlah}")
    ]]
    await context.bot.send_message(
        chat_id=ADMIN_ID,
        text=f"💸 *WD BARU*\n👤 ID: `{user_id}`\n💰 Rp {jumlah:,}\n💳 Fee: Rp {fee:,}\n📤 Dikirim: Rp {diterima:,}\n📱 DANA: `{nomor}`\n🆔 WD#{wd_id}",
        parse_mode="Markdown",
        reply_markup=InlineKeyboardMarkup(keyboard)
    )
    await update.message.reply_text(
        f"✅ *Permintaan WD dikirim!*\n━━━━━━━━━━━━━━━━━━\n"
        f"💰 Jumlah WD: Rp {jumlah:,}\n"
        f"📊 Fee (1.5%): Rp {fee:,}\n"
        f"📤 Kamu terima: *Rp {diterima:,}*\n"
        f"📱 DANA: `{nomor}`\n"
        f"⏳ Diproses dalam 1x24 jam",
        parse_mode="Markdown"
    )

# ===== REFERRAL =====
async def show_referral(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    bot_info = await context.bot.get_me()
    ref_link = f"https://t.me/{bot_info.username}?start=REF{user_id}"

    await update.message.reply_text(
        f"👥 *REFERRAL*\n━━━━━━━━━━━━━━━━━━\n"
        f"🔗 Link kamu:\n`{ref_link}`\n\n"
        f"💰 Komisi per referral: *Rp {KOMISI_REFERRAL:,}*\n\n"
        f"✅ Komisi per approved: *Rp {KOMISI_PERAPPROVE:,}*\n\n"
        f"Bagikan ke teman dan dapat komisi otomatis!",
        parse_mode="Markdown"
    )

# ===== RIWAYAT =====
async def show_riwayat_menu(update: Update, context: ContextTypes.DEFAULT_TYPE):
    keyboard = [
        [InlineKeyboardButton("📋 Riwayat Tugas", callback_data="riwayat_tugas"),
         InlineKeyboardButton("💸 Riwayat WD", callback_data="riwayat_wd")]
    ]
    await update.message.reply_text("📜 Pilih riwayat:", reply_markup=InlineKeyboardMarkup(keyboard))
    

# ===== INFO =====
async def show_info(update: Update, context: ContextTypes.DEFAULT_TYPE):
    total = get_total_users()
    total_tugas = get_total_tasks_done()
    await update.message.reply_text(
        f"ℹ️ *INFO BOT*\n━━━━━━━━━━━━━━━━━━\n"
        f"👥 Total Member: {total}\n"
        f"✅ Total Tugas Selesai: {total_tugas}\n"
        f"💰 Min WD: Rp {MIN_WD:,}\n"
        f"🎁 Komisi Referral: Rp {KOMISI_REFERRAL:,}",
        parse_mode="Markdown"
    )

# ===== DEPOSIT =====
async def show_deposit(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data["input_deposit_jumlah"] = True
    await update.message.reply_text(
        f"💳 *DEPOSIT SALDO*\n━━━━━━━━━━━━━━━━━━\n"
        f"Transfer ke DANA:\n📱 `{DANA_ADMIN}`\n\n"
        f"Ketik jumlah deposit kamu:\nContoh: `50000`",
        parse_mode="Markdown"
    )

# ===== BOT LAINNYA =====
async def show_bot_lainnya(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not BOT_REKOMENDASI:
        await update.message.reply_text("🤖 Belum ada rekomendasi bot saat ini.")
        return
    text = "🤖 *BOT LAINNYA*\n━━━━━━━━━━━━━━━━━━\n\n"
    keyboard = []
    for bot in BOT_REKOMENDASI:
        text += f"📌 *{bot['nama']}*\n"
        keyboard.append([InlineKeyboardButton(f"🔗 {bot['nama']}", url=bot["link"])])
    await update.message.reply_text(text, parse_mode="Markdown", reply_markup=InlineKeyboardMarkup(keyboard))

# ===== FOTO HANDLER =====
async def photo_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id

    if not await is_member(context.bot, user_id):
        await send_join_prompt(update.message)
        return

    if context.user_data.get("ambil_tugas"):
        task_id = context.user_data["ambil_tugas"]
        task = get_task(task_id)
        if not task:
            await update.message.reply_text("❌ Tugas tidak valid!")
            return
        if user_already_did_task(user_id, task_id):
            await update.message.reply_text("⚠️ Sudah pernah mengerjakan tugas ini!")
            return

        bukti = update.message.photo[-1].file_id
        submit_id = submit_task(user_id, task_id, bukti)
        context.user_data["ambil_tugas"] = None

        keyboard = [[
            InlineKeyboardButton("✅ APPROVE", callback_data=f"at_{submit_id}_{user_id}_{task[3]}"),
            InlineKeyboardButton("❌ REJECT", callback_data=f"rt_{submit_id}_{user_id}")
        ]]
        await context.bot.send_photo(
            chat_id=ADMIN_ID,
            photo=bukti,
            caption=f"📋 *TUGAS BARU*\n👤 ID: `{user_id}`\n📱 APK: {task[1]}\n💰 Rp {task[3]:,}\n🆔 #{submit_id}",
            parse_mode="Markdown",
            reply_markup=InlineKeyboardMarkup(keyboard)
        )
        await update.message.reply_text(
            f"✅ *Bukti dikirim!*\n⏳ Status: *PENDING*\nDiproses dalam 1x24 jam",
            parse_mode="Markdown"
        )

    elif context.user_data.get("input_deposit_bukti"):
        jumlah = context.user_data.get("deposit_jumlah", 0)
        bukti = update.message.photo[-1].file_id
        dep_id = create_deposit(user_id, jumlah, bukti)
        context.user_data["input_deposit_bukti"] = False

        keyboard = [[InlineKeyboardButton("✅ APPROVE DEPOSIT", callback_data=f"adep_{dep_id}_{user_id}_{jumlah}")]]
        await context.bot.send_photo(
            chat_id=ADMIN_ID,
            photo=bukti,
            caption=f"💳 *DEPOSIT BARU*\n👤 ID: `{user_id}`\n💰 Rp {jumlah:,}\n🆔 #{dep_id}",
            parse_mode="Markdown",
            reply_markup=InlineKeyboardMarkup(keyboard)
        )
        await update.message.reply_text(
            f"✅ Bukti deposit dikirim!\n💰 Rp {jumlah:,}\n⏳ Menunggu konfirmasi admin",
            parse_mode="Markdown"
        )

# ===== CALLBACK =====
async def callback_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    data = query.data
    parts = data.split("_")

    if data.startswith("ambil_"):
        task_id = parts[1]
        user_id = query.from_user.id
        task = get_task(task_id)
        if not task:
            await query.edit_message_text("❌ Tugas tidak ditemukan!")
            return
        if user_already_did_task(user_id, task_id):
            await query.edit_message_text("⚠️ Kamu sudah mengerjakan tugas ini!")
            return
        context.user_data["ambil_tugas"] = task_id
        await query.edit_message_text(
            f"📱 *{task[1]}*\n━━━━━━━━━━━━━━━━━━\n"
            f"💰 Bayaran: Rp {task[3]:,}\n\n"
            f"📌 *Cara kerja:*\n"
            f"1️⃣ Klik link referral\n"
            f"2️⃣ Daftar di APK\n"
            f"3️⃣ Screenshot bukti\n"
            f"4️⃣ Kirim screenshot ke bot\n\n"
            f"🔗 Link: {task[2]}\n\n"
            f"📸 *Kirim screenshot sekarang!*",
            parse_mode="Markdown"
        )

    elif data.startswith("at_"):
        # Approve tugas
        submit_id, user_id, bayaran = int(parts[1]), int(parts[2]), int(parts[3])
        approve_user_task(submit_id)
        update_saldo(user_id, bayaran)
        try:
            await context.bot.send_message(user_id, f"✅ *Tugas DISETUJUI!*\n💰 Rp {bayaran:,} masuk ke saldo!", parse_mode="Markdown")
        except: pass
        await query.edit_message_caption(caption=query.message.caption + "\n\n✅ APPROVED", parse_mode="Markdown")
        try:
            await context.bot.send_message(
                chat_id=CHANNEL_ID,
                text=(
                    f"✅ *TUGAS BERHASIL DISELESAIKAN!*\n"
                    f"━━━━━━━━━━━━━━━━━━\n"
                    f"👤 User ID: `{user_id}`\n"
                    f"💰 Bayaran: Rp {bayaran:,}\n\n"
                    f"Kamu juga bisa dapat penghasilan! Gabung sekarang 👇"
                ),
                parse_mode="Markdown"
            )
        except Exception as ce:
            logging.warning(f"Gagal posting ke channel: {ce}")

    elif data.startswith("rt_"):
        # Reject tugas
        submit_id, user_id = int(parts[1]), int(parts[2])
        reject_user_task(submit_id)
        try:
            await context.bot.send_message(user_id, "❌ *Tugas DITOLAK!*\nBukti tidak valid.", parse_mode="Markdown")
        except: pass
        await query.edit_message_caption(caption=query.message.caption + "\n\n❌ REJECTED", parse_mode="Markdown")

    elif data.startswith("awd_"):
        # Approve WD
        wd_id, user_id, jumlah = int(parts[1]), int(parts[2]), int(parts[3])
        approve_withdrawal(wd_id)
        try:
            await context.bot.send_message(user_id, f"✅ *WD DISETUJUI!*\nRp {jumlah:,} sudah dikirim!", parse_mode="Markdown")
        except: pass
        await query.edit_message_text(query.message.text + "\n\n✅ SUDAH DITRANSFER", parse_mode="Markdown")
        try:
            await context.bot.send_message(
                chat_id=CHANNEL_ID,
                text=(
                    f"💸 *WITHDRAW BERHASIL DIPROSES!*\n"
                    f"━━━━━━━━━━━━━━━━━━\n"
                    f"👤 User ID: `{user_id}`\n"
                    f"💰 Jumlah: Rp {jumlah:,}\n\n"
                    f"Mau dapat penghasilan juga? Gabung sekarang 👇"
                ),
                parse_mode="Markdown"
            )
        except Exception as ce:
            logging.warning(f"Gagal posting ke channel: {ce}")

    elif data.startswith("rwd_"):
        # Reject WD
        wd_id, user_id, jumlah = int(parts[1]), int(parts[2]), int(parts[3])
        reject_withdrawal(wd_id)
        update_saldo(user_id, jumlah)
        try:
            await context.bot.send_message(user_id, f"❌ *WD DITOLAK!*\nRp {jumlah:,} dikembalikan.", parse_mode="Markdown")
        except: pass
        await query.edit_message_text(query.message.text + "\n\n❌ DITOLAK", parse_mode="Markdown")

    elif data.startswith("adep_"):
        # Approve deposit
        dep_id, user_id, jumlah = int(parts[1]), int(parts[2]), int(parts[3])
        approve_deposit_db(dep_id)
        update_saldo(user_id, jumlah)
        try:
            await context.bot.send_message(user_id, f"✅ *DEPOSIT DISETUJUI!*\nRp {jumlah:,} masuk!", parse_mode="Markdown")
        except: pass
        await query.edit_message_caption(caption=query.message.caption + "\n\n✅ APPROVED", parse_mode="Markdown")

    elif data == "riwayat_tugas":
        user_id = query.from_user.id
        tasks = get_user_tasks(user_id)
        if not tasks:
            await query.edit_message_text("📜 Belum ada riwayat tugas!")
            return
        text = "📋 *RIWAYAT TUGAS*\n━━━━━━━━━━━━━━━━━━\n\n"
        for t in tasks:
            emoji = {"pending":"⏳","approved":"✅","rejected":"❌"}.get(t[4],"❓")
            text += f"{emoji} {t[9]} - Rp {t[10]:,}\n"
        await query.edit_message_text(text, parse_mode="Markdown")

    elif data == "riwayat_wd":
        user_id = query.from_user.id
        wds = get_user_withdrawals(user_id)
        if not wds:
            await query.edit_message_text("📜 Belum ada riwayat WD!")
            return
        text = "💸 *RIWAYAT WD*\n━━━━━━━━━━━━━━━━━━\n\n"
        for w in wds:
            emoji = {"pending":"⏳","approved":"✅","rejected":"❌"}.get(w[4],"❓")
            text += f"{emoji} Rp {w[2]:,} → {w[3]}\n"
        await query.edit_message_text(text, parse_mode="Markdown")

    elif data.startswith("wd_nominal_"):
        user_id = query.from_user.id
        jumlah = int(parts[2])
        db_user = get_user(user_id)
        saldo = db_user[3] if db_user else 0
        if jumlah > saldo:
            await query.answer(f"❌ Saldo tidak cukup! Saldo kamu: Rp {saldo:,}", show_alert=True)
            return
        fee = round(jumlah * 0.015)
        diterima = jumlah - fee
        context.user_data["wd_jumlah"] = jumlah
        context.user_data["input_wd_nomor"] = True
        await query.edit_message_text(
            f"💸 *TARIK SALDO*\n━━━━━━━━━━━━━━━━━━\n"
            f"💰 Jumlah WD: *Rp {jumlah:,}*\n"
            f"📊 Fee (1.5%): Rp {fee:,}\n"
            f"📤 Kamu terima: *Rp {diterima:,}*\n\n"
            f"Ketik *nomor DANA* kamu:",
            parse_mode="Markdown"
        )

    elif data == "wd_manual":
        user_id = query.from_user.id
        db_user = get_user(user_id)
        saldo = db_user[3] if db_user else 0
        context.user_data["input_wd"] = True
        await query.edit_message_text(
            f"💸 *TARIK SALDO — MANUAL*\n━━━━━━━━━━━━━━━━━━\n"
            f"💰 Saldo: *Rp {saldo:,}*\n"
            f"📊 Fee: 1.5% dari jumlah WD\n\n"
            f"Ketik dengan format:\n`jumlah|nomorDANA`\n"
            f"Contoh: `50000|081234567890`",
            parse_mode="Markdown"
        )

    elif data == "cek_member":
        user_id = query.from_user.id
        if await is_member(context.bot, user_id):
            await query.edit_message_text(
                "✅ *Verifikasi berhasil!*\n\nSekarang kamu bisa menggunakan bot.\nKetik /start untuk memulai!",
                parse_mode="Markdown"
            )
        else:
            await query.answer("❌ Kamu belum join channel! Silakan join dulu.", show_alert=True)

# ===== ADMIN COMMANDS =====
async def admin_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_user.id != ADMIN_ID:
        return
    await update.message.reply_text(
        "🔧 *ADMIN PANEL*\n━━━━━━━━━━━━━━━━━━\n\n"
        "/addtask - Tambah tugas\n"
        "Format: `/addtask Nama|Link|Bayaran|Stok`\n\n"
        "/deltask ID - Hapus tugas\n"
        "/cekuser ID - Cek user\n"
        "/addsaldo ID Jumlah - Tambah saldo\n"
        "/broadcast - Kirim pesan ke semua",
        parse_mode="Markdown"
    )

async def addtask_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_user.id != ADMIN_ID:
        return
    if not context.args:
        await update.message.reply_text("Format: `/addtask Nama|Link|Bayaran|Stok`", parse_mode="Markdown")
        return
    try:
        text = " ".join(context.args)
        p = text.split("|")
        nama = p[0].strip()
        link = p[1].strip()
        bayaran = int(p[2].strip())
        stok = int(p[3].strip()) if len(p) > 3 else -1
        add_task(nama, link, bayaran, stok)
        await update.message.reply_text(f"✅ Tugas *{nama}* ditambahkan!", parse_mode="Markdown")
        stok_text = "♾️" if stok == -1 else str(stok)
        try:
            await context.bot.send_message(
                chat_id=CHANNEL_ID,
                text=(
                    f"📢 *TUGAS BARU TERSEDIA!*\n"
                    f"━━━━━━━━━━━━━━━━━━\n"
                    f"📱 *{nama}*\n"
                    f"💰 Bayaran: Rp {bayaran:,}\n"
                    f"📦 Stok: {stok_text}\n"
                    f"🔗 Link: {link}\n\n"
                    f"Segera ambil tugas di bot!"
                ),
                parse_mode="Markdown"
            )
        except Exception as ce:
            logging.warning(f"Gagal posting ke channel: {ce}")
    except Exception as e:
        await update.message.reply_text(f"❌ Error: {e}")

async def deltask_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_user.id != ADMIN_ID:
        return
    if not context.args:
        await update.message.reply_text("Format: `/deltask ID`", parse_mode="Markdown")
        return
    deactivate_task(context.args[0])
    await update.message.reply_text(f"✅ Tugas dihapus!")

async def cekuser_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_user.id != ADMIN_ID:
        return
    if not context.args:
        return
    u = get_user(int(context.args[0]))
    if not u:
        await update.message.reply_text("❌ User tidak ditemukan!")
        return
    await update.message.reply_text(
        f"👤 *INFO USER*\nID: `{u[0]}`\nNama: {u[2]}\nSaldo: Rp {u[3]:,}",
        parse_mode="Markdown"
    )

async def addsaldo_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_user.id != ADMIN_ID:
        return
    if len(context.args) < 2:
        await update.message.reply_text("Format: `/addsaldo UserID Jumlah`", parse_mode="Markdown")
        return
    user_id = int(context.args[0])
    jumlah = int(context.args[1])
    update_saldo(user_id, jumlah)
    await update.message.reply_text(f"✅ Saldo Rp {jumlah:,} ditambahkan ke user {user_id}!")

async def broadcast_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_user.id != ADMIN_ID:
        return
    context.user_data["broadcast_mode"] = True
    await update.message.reply_text("📢 Ketik pesan broadcast:")

async def do_broadcast(update: Update, context: ContextTypes.DEFAULT_TYPE):
    msg = update.message.text
    users = get_all_users()
    ok = 0
    for u in users:
        try:
            await context.bot.send_message(u[0], f"📢 {msg}")
            ok += 1
        except: pass
    context.user_data["broadcast_mode"] = False
    await update.message.reply_text(f"✅ Terkirim ke {ok}/{len(users)} user!")

async def do_addtask(update: Update, context: ContextTypes.DEFAULT_TYPE):
    pass

def main():
    init_db()
    app = Application.builder().token(TOKEN).build()
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("admin", admin_cmd))
    app.add_handler(CommandHandler("addtask", addtask_cmd))
    app.add_handler(CommandHandler("deltask", deltask_cmd))
    app.add_handler(CommandHandler("cekuser", cekuser_cmd))
    app.add_handler(CommandHandler("addsaldo", addsaldo_cmd))
    app.add_handler(CommandHandler("broadcast", broadcast_cmd))
    app.add_handler(CallbackQueryHandler(callback_handler))
    app.add_handler(MessageHandler(filters.PHOTO, photo_handler))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, text_handler))
    print("✅ Bot jalan!")
    app.run_polling(drop_pending_updates=True)

if __name__ == "__main__":
    main()

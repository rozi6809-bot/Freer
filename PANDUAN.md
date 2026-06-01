# 🤖 FREELANCE APK BOT - PANDUAN SETUP

## STEP 1 - EDIT CONFIG
Buka file `config.py` dan isi:
- TOKEN = "token dari BotFather"
- ADMIN_ID = ID Telegram kamu (cek di @userinfobot)
- DANA_ADMIN = nomor DANA kamu

## STEP 2 - UPLOAD KE GITHUB
1. Buka github.com
2. Klik "New Repository"
3. Nama: freelance-apk-bot
4. Upload semua file ini

## STEP 3 - DEPLOY KE RAILWAY
1. Buka railway.app
2. Klik "New Project"
3. Pilih "Deploy from GitHub repo"
4. Pilih repo yang tadi dibuat
5. Railway otomatis detect Python
6. Tambah Environment Variable:
   - Klik "Variables"
   - Tambah: TOKEN = token bot kamu

## STEP 4 - BOT ONLINE!
Railway akan otomatis jalankan bot 24/7!

---

## CARA PAKAI (ADMIN)

### Tambah Tugas:
/addtask NamaAPK|LinkReferral|Bayaran|Stok
Contoh: /addtask Shopee|https://s.shopee.co.id/xxx|5000|100

### Approve Tugas User:
Klik tombol ✅ APPROVE di notif yang masuk

### Approve WD:
Klik tombol ✅ APPROVE WD di notif yang masuk

### Broadcast Pesan:
/broadcast

### Cek User:
/cekuser 123456789

---

## FITUR BOT
✅ Menu tugas APK referral
✅ Submit bukti screenshot
✅ Status Pending → Approved/Rejected
✅ Sistem saldo
✅ Tarik saldo (WD) via DANA
✅ Deposit saldo
✅ Sistem referral + komisi
✅ Riwayat tugas & WD
✅ Admin panel lengkap
✅ Broadcast ke semua user
✅ Online 24/7 di Railway

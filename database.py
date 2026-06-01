from pymongo import MongoClient
import certifi
from config import MONGO_URL

# =========================
# CONNECT MONGODB
# =========================
client = MongoClient(
    MONGO_URL,
    tlsCAFile=certifi.where()
)

db = client["bot_db"]

users = db["users"]
tasks = db["tasks"]
user_tasks = db["user_tasks"]
withdrawals = db["withdrawals"]
deposits = db["deposits"]

# =========================
# USERS
# =========================
def get_user(user_id):
    return users.find_one({"user_id": user_id})

def create_user(user_id, username, full_name, ref_code, referred_by=None):
    if not get_user(user_id):
        users.insert_one({
            "user_id": user_id,
            "username": username,
            "full_name": full_name,
            "saldo": 0,
            "referral_code": ref_code,
            "referred_by": referred_by
        })

def update_saldo(user_id, jumlah):
    users.update_one(
        {"user_id": user_id},
        {"$inc": {"saldo": jumlah}}
    )

def get_total_users():
    return users.count_documents({})

# =========================
# TASKS
# =========================
def add_task(nama, link, bayaran, stok=-1):
    tasks.insert_one({
        "nama_apk": nama,
        "link_referral": link,
        "bayaran": bayaran,
        "stok": stok,
        "aktif": 1
    })

def get_active_tasks():
    return list(tasks.find({"aktif": 1}))

def get_task(task_id):
    return tasks.find_one({"_id": task_id})

def deactivate_task(task_id):
    tasks.update_one(
        {"_id": task_id},
        {"$set": {"aktif": 0}}
    )

# =========================
# USER TASKS
# =========================
def submit_task(user_id, task_id, bukti):
    user_tasks.insert_one({
        "user_id": user_id,
        "task_id": task_id,
        "bukti_file_id": bukti,
        "status": "pending"
    })

def user_already_did_task(user_id, task_id):
    return user_tasks.find_one({
        "user_id": user_id,
        "task_id": task_id,
        "status": {"$ne": "rejected"}
    }) is not None

# =========================
# WITHDRAW
# =========================
def create_withdrawal(user_id, jumlah, nomor):
    withdrawals.insert_one({
        "user_id": user_id,
        "jumlah": jumlah,
        "nomor_dana": nomor,
        "status": "pending"
    })

def get_total_withdrawals():
    return withdrawals.count_documents({})

# =========================
# DEPOSIT
# =========================
def create_deposit(user_id, jumlah, bukti):
    deposits.insert_one({
        "user_id": user_id,
        "jumlah": jumlah,
        "bukti_file_id": bukti,
        "status": "pending"
    })

def get_total_deposits():
    return deposits.count_documents({})

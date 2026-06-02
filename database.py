
# db.py

from pymongo import MongoClient
from config import MONGO_URI

client = MongoClient(MONGO_URI)
db = client["freelance_bot"]

users = db["users"]


# =========================
# USER FUNCTIONS
# =========================

def get_user(user_id):
    return users.find_one({"user_id": user_id})


def create_user(user_id, name):
    if not get_user(user_id):
        users.insert_one({
            "user_id": user_id,
            "name": name,
            "saldo": 0,
            "tasks_done": 0,
            "wd_total": 0,
            "referral": 0
        })


def add_saldo(user_id, amount):
    users.update_one(
        {"user_id": user_id},
        {"$inc": {"saldo": amount}}
    )


def get_saldo(user_id):
    user = get_user(user_id)
    return user["saldo"] if user else 0


def add_task(user_id):
    users.update_one(
        {"user_id": user_id},
        {"$inc": {"tasks_done": 1}}
    )


def add_wd(user_id, amount):
    users.update_one(
        {"user_id": user_id},
        {"$inc": {"wd_total": amount, "saldo": -amount}}
    )


def add_referral(user_id):
    users.update_one(
        {"user_id": user_id},
        {"$inc": {"referral": 1, "saldo": 2000}}
    )

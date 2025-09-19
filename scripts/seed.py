import os
from config import Config
from pymongo import MongoClient
from auth import hash_password
import datetime

def run():
    client = MongoClient(Config.MONGO_URI)
    db = client["civic_reporter"]

    users = db.users
    users.delete_many({})

    users.insert_one({
        "email": "admin@local",
        "password": hash_password("admin123"),
        "name": "Admin",
        "role": "admin",
        "pincode": "000000",
        "created_at": datetime.datetime.utcnow()
    })

    users.insert_one({
        "email": "staff@local",
        "password": hash_password("staff123"),
        "name": "Staff",
        "role": "staff",
        "pincode": "560001",
        "created_at": datetime.datetime.utcnow()
    })

    users.insert_one({
        "email": "citizen@local",
        "password": hash_password("citizen123"),
        "fname": "Citizen",
        "lname": "User",
        "phone_no": "9999999999",
        "pincode": "560001",
        "role": "citizen",
        "created_at": datetime.datetime.utcnow()
    })

    print("Seeded users: admin@local/admin123, staff@local/staff123, citizen@local/citizen123")
    client.close()

if __name__ == "__main__":
    run()

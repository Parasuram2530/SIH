# test_registration.py
from pymongo import MongoClient
from config import Config
from auth import hash_password
import datetime

def test_registration():
    print("Testing registration process...")
    
    # Simulate registration data
    test_user = {
        "email": "test@example.com",
        "password": hash_password("test123"),
        "fname": "Test",
        "lname": "User",
        "phone_no": "1234567890",
        "pincode": "560001",
        "role": "citizen",
        "created_at": datetime.datetime.utcnow()
    }
    
    try:
        # Connect to database
        client = MongoClient(Config.MONGO_URI)
        db = client["civic_reporter"]
        
        print("✅ Connected to database")
        
        # Insert test user
        result = db.users.insert_one(test_user)
        print(f"✅ Inserted test user with ID: {result.inserted_id}")
        
        # Verify insertion
        inserted = db.users.find_one({"_id": result.inserted_id})
        if inserted:
            print("✅ Verification successful - user found in database")
            print(f"   Email: {inserted['email']}")
        else:
            print("❌ Verification failed - user not found")
        
        # Clean up
        db.users.delete_one({"_id": result.inserted_id})
        print("✅ Cleaned up test user")
        
        client.close()
        
    except Exception as e:
        print(f"❌ Error: {e}")

if __name__ == "__main__":
    test_registration()
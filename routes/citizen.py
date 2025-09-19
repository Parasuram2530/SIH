from flask import Blueprint, request, current_app, render_template, redirect, url_for, send_from_directory, session, jsonify
from extensions import mongo
from auth import hash_password, verify_password
import uuid, os, datetime, requests
from utils import auto_assign_department

citizen_bp = Blueprint("citizen", __name__)

def get_location_from_ip(ip):
    try:
        response = requests.get(f"http://ipinfo.io/{ip}/json")
        data = response.json()
        if "loc" in data:
            lat, lon = data["loc"].split(",")
            return {"lat": float(lat), "lon": float(lon)}
    except:
        pass
    return {"lat": None, "lon": None}

@citizen_bp.route("/register", methods=["GET", "POST"])
def register_page():
    print(f"🔹 mongo.db available: {hasattr(mongo, 'db')}")
    if hasattr(mongo, 'db'):
        print(f"🔹 Database name: {mongo.db.name}")
        print(f"🔹 Collections: {mongo.db.list_collection_names()}")
    else:
        print("❌ mongo.db is not accessible!")
    if request.method == "POST":
        print("=" * 50)
        print("🔹 CITIZEN REGISTRATION STARTED")
        print("=" * 50)
        
        # Get form data
        email = request.form.get("email")
        password = request.form.get("password")
        fname = request.form.get("fname")
        lname = request.form.get("lname")
        phone_no = request.form.get("phone_no")
        pincode = request.form.get("pincode")
        
        print(f"📋 Form data:")
        print(f"   Email: {email}")
        print(f"   Password: {password}")
        print(f"   First Name: {fname}")
        print(f"   Last Name: {lname}")
        print(f"   Phone: {phone_no}")
        print(f"   Pincode: {pincode}")
        
        # Validation
        if not all([email, password, phone_no, fname, lname]):
            print("❌ Missing required fields")
            return "Every field is required", 400
        
        # Check if user exists
        try:
            existing_user = mongo.db.users.find_one({"email": email})
            if existing_user:
                print(f"❌ User already exists: {email}")
                return "User already exists", 400
            print("✅ Email is available")
        except Exception as e:
            print(f"❌ Database error checking existing user: {e}")
            return "Database error", 500
        
        # Hash password
        try:
            pwd_hash = hash_password(password)
            print(f"🔐 Password hash: {pwd_hash}")
        except Exception as e:
            print(f"❌ Password hashing error: {e}")
            return "Server error", 500
        
        # Prepare user data
        user_data = {
            "email": email,
            "password": pwd_hash,
            "fname": fname,
            "lname": lname,
            "phone_no": phone_no,
            "pincode": pincode,
            "role": "citizen",
            "created_at": datetime.datetime.utcnow()
        }
        
        print(f"💾 User data to insert: {user_data}")
        
        # Insert user
        try:
            result = mongo.db.users.insert_one(user_data)
            print(f"✅ User inserted with ID: {result.inserted_id}")
            
            # Verify insertion immediately
            inserted_user = mongo.db.users.find_one({"_id": result.inserted_id})
            if inserted_user:
                print("✅ User successfully saved to database!")
                print(f"✅ Stored email: {inserted_user['email']}")
                print(f"✅ Stored hash: {inserted_user['password']}")
            else:
                print("❌ FAILED: User not found after insertion!")
                return "Registration failed", 500
                
        except Exception as e:
            print(f"❌ Database insertion error: {e}")
            return "Registration failed", 500
        
        print("✅ Registration completed successfully")
        return redirect(url_for("citizen.login_page"))
    
    return render_template("register.html")

@citizen_bp.route("/login", methods=["GET", "POST"])
def login_page():
    if request.method == "POST":
        email = request.form.get("email")
        password = request.form.get("password")
        user = mongo.db.users.find_one({"email": email})
        
        print(f"🔹 Login attempt for: {email}")  # Debug
        print(f"🔹 User found: {user is not None}")  # Debug
        
        if not user:
            print("❌ User not found")  # Debug
            return "Invalid credentials", 401
            
        if not verify_password(password, user["password"]):
            print("❌ Password verification failed")  # Debug
            return "Invalid credentials", 401
            
        print("✅ Login successful")  # Debug
        
        from flask import session
        session["user_id"] = str(user["_id"])
        session["user_email"] = user["email"]
        # Combine fname and lname for session
        session["user_name"] = f"{user.get('fname', '')} {user.get('lname', '')}".strip()
        session["pincode"] = user.get("pincode")
        session["role"] = user.get("role", "citizen")
        
        return redirect(url_for("citizen.submit_page"))
    
    return render_template("login.html")

@citizen_bp.route("/submit", methods=["GET", "POST"])
def submit_page():
    if session.get("role") != "citizen":
        return redirect(url_for("citizen.login_page"))

    if request.method == "POST":
        title = request.form.get("title")
        description = request.form.get("description")
        category = request.form.get("category")
        severity = request.form.get("severity") or "Not urgent"

        user_ip = request.remote_addr
        location = get_location_from_ip(user_ip)

        saved_files = []
        UPLOAD_FOLDER = current_app.config.get('UPLOAD_FOLDER', 'uploads')
        os.makedirs(UPLOAD_FOLDER, exist_ok=True)
        files = request.files.getlist("file")
        for f in files:
            ext = os.path.splitext(f.filename)[1]
            fname = f"{uuid.uuid4().hex}{ext}"
            path = os.path.join(UPLOAD_FOLDER, fname)
            f.save(path)
            saved_files.append({"filename": fname, "url": f"/citizen/uploads/{fname}", "mimetype": f.mimetype})

        report = {
            "title": title,
            "description": description,
            "category": category,
            "severity": severity,
            "location": location,
            "media": saved_files,
            "reporter_email": session.get("user_email"),
            "reported_id": session.get("user_id"),
            "pincode": session.get("pincode"),
            "status": "submitted",
            "assigned_department": auto_assign_department(category),
            "notifications": [{"ts": datetime.datetime.utcnow(), "msg": "Report Submitted"}],
            "created_at": datetime.datetime.utcnow(),
            "updated_at": None,
            "resolved_at": None,
            "user_confirmed": False
        }

        mongo.db.reports.insert_one(report)
        return "Report Submitted!"
    return render_template("submit.html")

@citizen_bp.route("/my_reports")
def my_reports_page():
    if session.get("role") != "citizen":
        return redirect(url_for("citizen.login_page"))

    user_id = session.get("user_id")
    cursor = mongo.db.reports.find({"reported_id": user_id}).sort("created_at", -1)
    reports = []
    for r in cursor:
        r["_id"] = str(r["_id"])
        reports.append(r)
    return render_template("my_reports.html", reports=reports)

@citizen_bp.route("/notifications")
def notifications_page():
    if session.get("role") != "citizen":
        return redirect(url_for("citizen.login_page"))

    user_id = session.get("user_id")
    docs = mongo.db.reports.find({"reported_id": user_id}, {"notifications": 1, "_id": 0})
    notifications = []
    for d in docs:
        notifications.extend(d.get("notifications", []))
    return render_template("notifications.html", notifications=notifications)

@citizen_bp.route("/uploads/<path:filename>")
def uploaded_file(filename):
    UPLOAD_FOLDER = current_app.config.get('UPLOAD_FOLDER', 'uploads')
    return send_from_directory(UPLOAD_FOLDER, filename)

@citizen_bp.route("/test-db")
def test_db():
    try:
        collections = mongo.db.list_collection_names()
        users_count = mongo.db.users.count_documents({})
        return jsonify({
            "status": "success",
            "collections": collections,
            "users_count": users_count
        })
    except Exception as e:
        return jsonify({"status": "error", "message": str(e)}), 500
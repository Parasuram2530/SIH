from flask import Blueprint, request, current_app, render_template, redirect, url_for, send_from_directory
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
    if request.method == "POST":
        email = request.form.get("email")
        password = request.form.get("password")
        fname = request.form.get("name")
        lname = request.form.get("lname")
        phone_no = request.form.get("phone_no")
        pincode = request.form.get("pincode")
        if not email or not password or not phone_no or not fname or not lname:
            return "Every field is required", 400
        if mongo.db.users.find_one({"email": email}):
            return "User already exists", 400
        pwd_hash = hash_password(password)
        mongo.db.users.insert_one({
            "email": email,
            "password": pwd_hash,
            "fname": fname,
            "lname": lname,
            "phone_no":phone_no,
            "pincode":pincode,
            "role": "citizen",
            "created_at": datetime.datetime.utcnow()
        })
        return redirect(url_for("citizen.login_page"))
    return render_template("register.html")


@citizen_bp.route("/login", methods=["GET", "POST"])
def login_page():
    if request.method == "POST":
        email = request.form.get("email")
        password = request.form.get("password")
        user = mongo.db.users.find_one({"email": email})
        if not user or not verify_password(password, user["password"]):
            return "Invalid credentials", 401
        from flask import session
        session["user_id"] = str(user["_id"])
        session["user_email"] = user["email"]
        session["user_name"] = user.get("name", "")
        return redirect(url_for("citizen.submit_page"))
    return render_template("login.html")


@citizen_bp.route("/submit", methods=["GET", "POST"])
def submit_page():
    from flask import session
    if "user_id" not in session:
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
    from flask import session
    if "user_id" not in session:
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
    from flask import session
    if "user_id" not in session:
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

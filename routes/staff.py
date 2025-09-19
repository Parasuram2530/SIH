from flask import Blueprint, request, render_template, redirect, url_for, session, current_app, send_from_directory
from extensions import mongo
import datetime, os, uuid
from bson import ObjectId
from auth import verify_password

staff_bp = Blueprint("staff", __name__)

def require_staff_role():
    return session.get("role") in ("staff", "admin")

@staff_bp.route("/login", methods=["GET", "POST"])
def login_page():
    if request.method == "POST":
        email = request.form.get("email")
        password = request.form.get("password")
        user = mongo.db.users.find_one({"email": email, "role": {"$in": ["staff","admin"]}})
        if not user or not verify_password(password, user["password"]):
            return "Invalid credentials", 401

        session["user_id"] = str(user["_id"])
        session["user_email"] = user["email"]
        session["role"] = user["role"]
        session["name"] = user.get("name", "")
        session["staff_pincode"] = user.get("pincode")
        return redirect(url_for("staff.view_reports"))
    return render_template("staff_login.html")



@staff_bp.route("/reports/view")
def view_reports():
    staff_pincode = session.get("staff_pincode")  
    if not staff_pincode:
        return "Staff pincode not found. Please log in.", 403

    reports = list(mongo.db.reports.find({
        "status": {"$ne": "closed"}
        # "pincode": staff_pincode
    }))
    return render_template("staff_reports.html", reports=reports)

@staff_bp.route("/reports/closed")
def closed_reports():
    staff_pincode = session.get("staff_pincode")
    if not staff_pincode:
        return "Staff pincode not found. Please log in.", 403

    reports = list(mongo.db.reports.find({
        "status": "closed",
        # "pincode": staff_pincode
    }))
    return render_template("staff_reports_closed.html", reports=reports)

@staff_bp.route("/report/assign/<report_id>", methods=["GET", "POST"])
def assign_report(report_id):
    if not require_staff_role():
        return redirect(url_for("staff.login_page"))

    if request.method == "POST":
        department = request.form.get("department")
        assigned_to = request.form.get("assigned_to")
        if not department:
            return "Department required", 400

        mongo.db.reports.update_one(
            {"_id": ObjectId(report_id)},
            {"$set": {"assigned_department": department, "status": "acknowledged", "updated_at": datetime.datetime.utcnow()},
             "$push": {"notifications": {"ts": datetime.datetime.utcnow(), "msg": f"Assigned to {department}"}}}
        )
        return redirect(url_for("staff.view_reports"))

    report = mongo.db.reports.find_one({"_id": ObjectId(report_id)})
    if report:
        report["_id"] = str(report["_id"])
    return render_template("assign_report.html", report=report)


@staff_bp.route("/report/update/<report_id>", methods=["GET", "POST"])
def update_report(report_id):
    if not require_staff_role():
        return redirect(url_for("staff.login_page"))

    report = mongo.db.reports.find_one({"_id": ObjectId(report_id)})
    if not report:
        return "Report not found", 404
    report["_id"] = str(report["_id"])

    if request.method == "POST":
        status = request.form.get("status")
        if status not in ("submitted", "acknowledged", "in_progress", "resolved", "rejected"):
            return "Invalid status", 400

        update_fields = {"status": status, "updated_at": datetime.datetime.utcnow()}

        if status == "resolved":
            files = request.files.getlist("resolution_images")
            saved = []
            UPLOAD_FOLDER = current_app.config.get('UPLOAD_FOLDER', 'uploads')
            os.makedirs(UPLOAD_FOLDER, exist_ok=True)
            for f in files:
                ext = os.path.splitext(f.filename)[1]
                fname = f"{uuid.uuid4().hex}{ext}"
                path = os.path.join(UPLOAD_FOLDER, fname)
                f.save(path)
                saved.append({"filename": fname, "url": f"/staff/uploads/{fname}"})
            if saved:
                update_fields['resolution_media'] = saved
            update_fields['status'] = "awaiting_user_confirm"

        mongo.db.reports.update_one({"_id": ObjectId(report_id)}, {"$set": update_fields})
        mongo.db.reports.update_one(
            {"_id": ObjectId(report_id)},
            {"$push": {"notifications": {"ts": datetime.datetime.utcnow(), "msg": f"Status Updated to {update_fields['status']}"}}}
        )
        return redirect(url_for("staff.view_reports"))

    return render_template("update_report.html", report=report)


@staff_bp.route("/report/confirm_close/<report_id>", methods=["GET","POST"])
def confirm_close(report_id):
    if not require_staff_role():
        return redirect(url_for("staff.login_page"))

    mongo.db.reports.update_one(
        {"_id": ObjectId(report_id)},
        {"$set": {"status": "closed", "updated_at": datetime.datetime.utcnow(), "user_confirmed": True}}
    )
    return redirect(url_for("staff.view_reports"))


@staff_bp.route("/uploads/<path:filename>")
def uploaded_file(filename):
    UPLOAD_FOLDER = current_app.config.get('UPLOAD_FOLDER', 'uploads')
    from flask import send_from_directory
    return send_from_directory(UPLOAD_FOLDER, filename)


@staff_bp.route("/report/details/<report_id>")
def report_details(report_id):
    if not require_staff_role():
        return redirect(url_for("staff.login_page"))

    report = mongo.db.reports.find_one({"_id": ObjectId(report_id)})
    if not report:
        return "Report not found", 404

    report["_id"] = str(report["_id"])
    return render_template("report_details.html", report=report)

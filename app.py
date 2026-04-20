import os
import re
import sqlite3
import sys
import uuid
from datetime import datetime
from functools import wraps


BASE_DIR = os.path.abspath(os.path.dirname(__file__))
VENDOR_DIR = os.path.join(BASE_DIR, "vendor")
if os.path.isdir(VENDOR_DIR) and VENDOR_DIR not in sys.path:
    sys.path.insert(0, VENDOR_DIR)

from flask import (
    Flask,
    flash,
    g,
    jsonify,
    redirect,
    render_template,
    request,
    session,
    url_for,
)
from PIL import Image
from werkzeug.security import check_password_hash, generate_password_hash
from werkzeug.utils import secure_filename

try:
    import pytesseract
except ImportError:  # pragma: no cover - handled at runtime
    pytesseract = None


DATABASE = os.path.join(BASE_DIR, "agrismart.db")
UPLOAD_FOLDER = os.path.join(BASE_DIR, "static", "uploads")
ALLOWED_EXTENSIONS = {"png", "jpg", "jpeg", "webp"}

app = Flask(__name__)
app.config["SECRET_KEY"] = "agrismart-ai-secret-key"
app.config["UPLOAD_FOLDER"] = UPLOAD_FOLDER
app.config["MAX_CONTENT_LENGTH"] = 8 * 1024 * 1024

os.makedirs(UPLOAD_FOLDER, exist_ok=True)


TRANSLATIONS = {
    "en": {
        "portal_name": "AgriSmart AI - Farmer Welfare Portal",
        "home": "Home",
        "register": "Farmer Registration",
        "track_status": "Track Status",
        "admin_login": "Admin Login",
        "dashboard": "Dashboard",
        "logout": "Logout",
        "hero_title": "Smart Agriculture Digital Portal",
        "hero_text": "A unified digital welfare platform for farmers to register, apply for schemes, track benefits, and connect with the agriculture department.",
        "hero_button": "Register as Farmer",
        "track_button": "Track Application",
        "why_title": "Services for Farmers",
        "register_card": "Easy farmer onboarding with ID generation and document checks.",
        "subsidy_card": "Apply for welfare schemes, subsidy support, and crop assistance.",
        "status_card": "Track approvals, complaints, and application history in one place.",
        "reg_title": "Farmer Registration Form",
        "name": "Name",
        "age": "Age",
        "address": "Address",
        "phone": "Phone Number",
        "aadhaar": "Aadhaar Number",
        "land_area": "Land Area (acres)",
        "patta_number": "Patta Number",
        "aadhaar_photo": "Upload Aadhaar Photo",
        "land_photo": "Upload Land Photo",
        "patta_photo": "Upload Patta Photo",
        "submit": "Submit",
        "status_title": "Track Farmer Application Status",
        "search_label": "Enter Phone Number or Aadhaar Number",
        "search": "Check Status",
        "admin_title": "Department Admin Login",
        "username": "Username",
        "password": "Password",
        "complaints": "Complaints",
        "subsidy": "Subsidy",
        "insurance": "Insurance",
        "welcome_farmer": "Welcome Farmer",
        "history": "Application History",
        "chatbot_title": "Farmer Help Bot",
        "chatbot_hint": "Ask about subsidy, insurance, complaints, or status tracking.",
        "lang_toggle": "Tamil",
        "response": "Response",
        "ai_intro_title": "AI-Powered Smart Agriculture Administration",
        "ai_intro_text": "There is a need to develop an AI-powered smart agriculture administration system that can automate document processing, streamline application verification, enable intelligent grievance handling, and provide real-time insights. The system should improve decision-making, enhance transparency, and ensure faster and more efficient service delivery to farmers.",
    },
    "ta": {
        "portal_name": "அக்ரி ஸ்மார்ட் AI - விவசாயிகள் நலன் தளம்",
        "home": "முகப்பு",
        "register": "விவசாயி பதிவு",
        "track_status": "நிலை கண்காணிப்பு",
        "admin_login": "நிர்வாக உள்நுழைவு",
        "dashboard": "டாஷ்போர்டு",
        "logout": "வெளியேறு",
        "hero_title": "செயற்கை நுண்ணறிவு வேளாண்மை டிஜிட்டல் தளம்",
        "hero_text": "விவசாயிகள் பதிவு செய்ய, திட்டங்களுக்கு விண்ணப்பிக்க, நிலையை கண்காணிக்க, மற்றும் வேளாண்மை துறையுடன் இணைவதற்கான ஒருங்கிணைந்த தளம்.",
        "hero_button": "விவசாயியாக பதிவு செய்க",
        "track_button": "விண்ணப்ப நிலை பார்க்க",
        "why_title": "விவசாயிகளுக்கான சேவைகள்",
        "register_card": "விவசாயி ஐடி உருவாக்கம் மற்றும் ஆவண சரிபார்ப்புடன் எளிய பதிவு.",
        "subsidy_card": "அரசுத் திட்டங்கள், மானியம் மற்றும் பயிர் ஆதரவுக்கு விண்ணப்பிக்கவும்.",
        "status_card": "அனுமதி, புகார் மற்றும் விண்ணப்ப வரலாற்றை ஒரே இடத்தில் காணவும்.",
        "reg_title": "விவசாயி பதிவு படிவம்",
        "name": "பெயர்",
        "age": "வயது",
        "address": "முகவரி",
        "phone": "தொலைபேசி எண்",
        "aadhaar": "ஆதார் எண்",
        "land_area": "நில அளவு (ஏக்கர்)",
        "patta_number": "பட்டா எண்",
        "aadhaar_photo": "ஆதார் புகைப்படம் பதிவேற்றம்",
        "land_photo": "நில புகைப்படம் பதிவேற்றம்",
        "patta_photo": "பட்டா புகைப்படம் பதிவேற்றம்",
        "submit": "சமர்ப்பிக்கவும்",
        "status_title": "விவசாயி விண்ணப்ப நிலை கண்காணிப்பு",
        "search_label": "தொலைபேசி எண் அல்லது ஆதார் எண்ணை உள்ளிடவும்",
        "search": "நிலை பார்க்க",
        "admin_title": "துறை நிர்வாகி உள்நுழைவு",
        "username": "பயனர் பெயர்",
        "password": "கடவுச்சொல்",
        "complaints": "புகார்கள்",
        "subsidy": "மானியம்",
        "insurance": "காப்பீடு",
        "welcome_farmer": "வரவேற்கிறோம்",
        "history": "விண்ணப்ப வரலாறு",
        "chatbot_title": "விவசாயி உதவி பாட்டு",
        "chatbot_hint": "மானியம், காப்பீடு, புகார், அல்லது நிலை பற்றி கேளுங்கள்.",
        "lang_toggle": "English",
        "response": "பதில்",
        "ai_intro_title": "ஏஐ ஆதரவு கொண்ட ஸ்மார்ட் வேளாண்மை நிர்வாகம்",
        "ai_intro_text": "ஆவண செயலாக்கத்தை தானியக்கப்படுத்தி, விண்ணப்ப சரிபார்ப்பை எளிதாக்கி, புத்திசாலித்தனமான குறைதீர் மேலாண்மையை வழங்கி, நேரடி தகவல்களை காண்பிக்கும் ஏஐ ஆதரவு கொண்ட ஸ்மார்ட் வேளாண்மை நிர்வாக அமைப்பு தேவைப்படுகிறது. இது தீர்மான எடுப்பை மேம்படுத்தி, வெளிப்படைத்தன்மையை உயர்த்தி, விவசாயிகளுக்கான சேவை வழங்கலை வேகமாகவும் திறம்படவும் மாற்றும்.",
    },
}


def get_db():
    if "db" not in g:
        g.db = sqlite3.connect(DATABASE)
        g.db.row_factory = sqlite3.Row
    return g.db


@app.teardown_appcontext
def close_db(_error):
    db = g.pop("db", None)
    if db is not None:
        db.close()


def init_db():
    os.makedirs(UPLOAD_FOLDER, exist_ok=True)
    db = sqlite3.connect(DATABASE)
    with open(os.path.join(BASE_DIR, "schema.sql"), "r", encoding="utf-8") as schema_file:
        db.executescript(schema_file.read())
    admin_exists = db.execute("SELECT id FROM admin WHERE username = ?", ("admin",)).fetchone()
    if not admin_exists:
        db.execute(
            "INSERT INTO admin (username, password_hash) VALUES (?, ?)",
            ("admin", generate_password_hash("admin123")),
        )

    existing_columns = {
        row[1] for row in db.execute("PRAGMA table_info(farmers)").fetchall()
    }
    if "patta_number" not in existing_columns:
        db.execute("ALTER TABLE farmers ADD COLUMN patta_number TEXT DEFAULT ''")
    if "patta_photo" not in existing_columns:
        db.execute("ALTER TABLE farmers ADD COLUMN patta_photo TEXT DEFAULT ''")
    db.commit()
    db.close()


def allowed_file(filename):
    return "." in filename and filename.rsplit(".", 1)[1].lower() in ALLOWED_EXTENSIONS


def save_file(file_storage, prefix):
    if not file_storage or file_storage.filename == "":
        return ""
    if not allowed_file(file_storage.filename):
        raise ValueError("Only PNG, JPG, JPEG, and WEBP files are allowed.")
    filename = secure_filename(file_storage.filename)
    unique_name = f"{prefix}_{uuid.uuid4().hex}_{filename}"
    file_path = os.path.join(app.config["UPLOAD_FOLDER"], unique_name)
    file_storage.save(file_path)
    return f"uploads/{unique_name}"


def normalize_text(value):
    return re.sub(r"[^a-z0-9]", "", value.lower()) if value else ""


def run_ocr_check(image_relative_path, entered_name, entered_aadhaar):
    if not image_relative_path:
        return "Mismatch", "No Aadhaar image uploaded."

    image_path = os.path.join(BASE_DIR, "static", image_relative_path)
    if pytesseract is None:
        return "Mismatch", "pytesseract is not installed."

    try:
        text = pytesseract.image_to_string(Image.open(image_path))
    except Exception as exc:  # pragma: no cover - depends on environment setup
        return "Mismatch", f"OCR error: {exc}"

    name_ok = normalize_text(entered_name) in normalize_text(text)
    aadhaar_digits = re.sub(r"\D", "", text)
    aadhaar_ok = entered_aadhaar in aadhaar_digits
    status = "Verified" if name_ok and aadhaar_ok else "Mismatch"
    return status, text.strip()[:1500]


def generate_farmer_id():
    stamp = datetime.now().strftime("%Y%m%d")
    suffix = uuid.uuid4().hex[:5].upper()
    return f"AGRI-{stamp}-{suffix}"


def admin_required(view_func):
    @wraps(view_func)
    def wrapper(*args, **kwargs):
        if not session.get("admin_logged_in"):
            flash("Please log in as admin to continue.", "error")
            return redirect(url_for("admin_login"))
        return view_func(*args, **kwargs)

    return wrapper


def approved_farmer_required(view_func):
    @wraps(view_func)
    def wrapper(*args, **kwargs):
        farmer_id = session.get("farmer_db_id")
        if not farmer_id:
            flash("Please access your approved dashboard from the status page.", "error")
            return redirect(url_for("track_status"))
        farmer = get_db().execute("SELECT * FROM farmers WHERE id = ?", (farmer_id,)).fetchone()
        if not farmer or farmer["status"] != "Approved":
            session.pop("farmer_db_id", None)
            flash("Your dashboard is available only for approved farmers.", "error")
            return redirect(url_for("track_status"))
        return view_func(*args, **kwargs)

    return wrapper


def current_lang():
    lang = session.get("lang", "en")
    return lang if lang in TRANSLATIONS else "en"


def t(key):
    return TRANSLATIONS[current_lang()].get(key, key)


@app.context_processor
def inject_globals():
    return {"t": t, "lang": current_lang(), "portal_name": t("portal_name")}


@app.route("/set-language/<lang_code>")
def set_language(lang_code):
    session["lang"] = "ta" if lang_code == "ta" else "en"
    return redirect(request.referrer or url_for("home"))


@app.route("/")
def home():
    return render_template("home.html")


@app.route("/register", methods=["GET", "POST"])
def register_farmer():
    if request.method == "POST":
        name = request.form.get("name", "").strip()
        age = request.form.get("age", "").strip()
        address = request.form.get("address", "").strip()
        phone = request.form.get("phone", "").strip()
        aadhaar = request.form.get("aadhaar", "").strip()
        land_area = request.form.get("land_area", "").strip()
        patta_number = request.form.get("patta_number", "").strip()
        aadhaar_photo = request.files.get("aadhaar_photo")
        land_photo = request.files.get("land_photo")
        patta_photo = request.files.get("patta_photo")

        if not re.fullmatch(r"\d{10}", phone):
            flash("Phone number must contain exactly 10 digits.", "error")
            return redirect(url_for("register_farmer"))
        if not re.fullmatch(r"\d{12}", aadhaar):
            flash("Aadhaar number must contain exactly 12 digits.", "error")
            return redirect(url_for("register_farmer"))

        db = get_db()
        existing_farmer = db.execute(
            "SELECT id FROM farmers WHERE phone = ? OR aadhaar = ?",
            (phone, aadhaar),
        ).fetchone()
        if existing_farmer:
            flash("A farmer with this phone number or Aadhaar already exists.", "error")
            return redirect(url_for("register_farmer"))

        try:
            aadhaar_path = save_file(aadhaar_photo, "aadhaar")
            land_path = save_file(land_photo, "land")
            patta_path = save_file(patta_photo, "patta")
        except ValueError as exc:
            flash(str(exc), "error")
            return redirect(url_for("register_farmer"))

        farmer_unique_id = generate_farmer_id()
        ocr_status, ocr_text = run_ocr_check(aadhaar_path, name, aadhaar)
        db.execute(
            """
            INSERT INTO farmers (
                farmer_id, name, age, address, phone, aadhaar, land_area,
                patta_number, aadhaar_photo, land_photo, patta_photo, status, ocr_status, ocr_text
            )
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, 'Pending', ?, ?)
            """,
            (
                farmer_unique_id,
                name,
                age,
                address,
                phone,
                aadhaar,
                land_area,
                patta_number,
                aadhaar_path,
                land_path,
                patta_path,
                ocr_status,
                ocr_text,
            ),
        )
        db.commit()
        flash(f"Registration successful. Your Farmer ID is {farmer_unique_id}.", "success")
        return redirect(url_for("track_status"))

    return render_template("register.html")


@app.route("/track-status", methods=["GET", "POST"])
def track_status():
    farmer = None
    if request.method == "POST":
        lookup = request.form.get("lookup", "").strip()
        farmer = get_db().execute(
            "SELECT * FROM farmers WHERE phone = ? OR aadhaar = ?",
            (lookup, lookup),
        ).fetchone()
        if not farmer:
            flash("No farmer application found for the entered details.", "error")
    return render_template("track_status.html", farmer=farmer)


@app.post("/farmer/access")
def farmer_access():
    farmer_id = request.form.get("farmer_id")
    farmer = get_db().execute("SELECT * FROM farmers WHERE id = ?", (farmer_id,)).fetchone()
    if farmer and farmer["status"] == "Approved":
        session["farmer_db_id"] = farmer["id"]
        flash("Approved farmer dashboard unlocked.", "success")
        return redirect(url_for("farmer_dashboard"))
    flash("Dashboard access is available only after approval.", "error")
    return redirect(url_for("track_status"))


@app.route("/farmer/dashboard")
@approved_farmer_required
def farmer_dashboard():
    db = get_db()
    farmer = db.execute("SELECT * FROM farmers WHERE id = ?", (session["farmer_db_id"],)).fetchone()
    subsidies = db.execute(
        "SELECT * FROM subsidies WHERE farmer_id = ? ORDER BY created_at DESC",
        (farmer["id"],),
    ).fetchall()
    insurance_items = db.execute(
        "SELECT * FROM insurance WHERE farmer_id = ? ORDER BY created_at DESC",
        (farmer["id"],),
    ).fetchall()
    complaints = db.execute(
        "SELECT * FROM complaints WHERE farmer_id = ? ORDER BY created_at DESC",
        (farmer["id"],),
    ).fetchall()
    return render_template(
        "farmer_dashboard.html",
        farmer=farmer,
        subsidies=subsidies,
        insurance_items=insurance_items,
        complaints=complaints,
    )


@app.post("/farmer/subsidy")
@approved_farmer_required
def apply_subsidy():
    db = get_db()
    db.execute(
        """
        INSERT INTO subsidies (farmer_id, scheme_name, amount, details, status)
        VALUES (?, ?, ?, ?, 'Pending')
        """,
        (
            session["farmer_db_id"],
            request.form.get("scheme_name", "").strip(),
            request.form.get("amount", "").strip(),
            request.form.get("details", "").strip(),
        ),
    )
    db.commit()
    flash("Subsidy application submitted successfully.", "success")
    return redirect(url_for("farmer_dashboard"))


@app.post("/farmer/insurance")
@approved_farmer_required
def apply_insurance():
    db = get_db()
    db.execute(
        """
        INSERT INTO insurance (farmer_id, crop_type, season, land_details, status)
        VALUES (?, ?, ?, ?, 'Pending')
        """,
        (
            session["farmer_db_id"],
            request.form.get("crop_type", "").strip(),
            request.form.get("season", "").strip(),
            request.form.get("land_details", "").strip(),
        ),
    )
    db.commit()
    flash("Insurance request submitted successfully.", "success")
    return redirect(url_for("farmer_dashboard"))


@app.post("/farmer/complaint")
@approved_farmer_required
def submit_complaint():
    db = get_db()
    db.execute(
        """
        INSERT INTO complaints (farmer_id, subject, message, status)
        VALUES (?, ?, ?, 'Open')
        """,
        (
            session["farmer_db_id"],
            request.form.get("subject", "").strip(),
            request.form.get("message", "").strip(),
        ),
    )
    db.commit()
    flash("Complaint submitted to the agriculture department.", "success")
    return redirect(url_for("farmer_dashboard"))


@app.route("/admin/login", methods=["GET", "POST"])
def admin_login():
    if request.method == "POST":
        username = request.form.get("username", "").strip()
        password = request.form.get("password", "").strip()
        admin = get_db().execute("SELECT * FROM admin WHERE username = ?", (username,)).fetchone()
        if admin and check_password_hash(admin["password_hash"], password):
            session["admin_logged_in"] = True
            flash("Admin login successful.", "success")
            return redirect(url_for("admin_dashboard"))
        flash("Invalid admin credentials.", "error")
    return render_template("admin_login.html")


@app.route("/admin/dashboard")
@admin_required
def admin_dashboard():
    db = get_db()
    farmers = db.execute("SELECT * FROM farmers ORDER BY created_at DESC").fetchall()
    subsidies = db.execute(
        """
        SELECT subsidies.*, farmers.name AS farmer_name, farmers.farmer_id AS farmer_code
        FROM subsidies
        JOIN farmers ON farmers.id = subsidies.farmer_id
        ORDER BY subsidies.created_at DESC
        """
    ).fetchall()
    insurance_items = db.execute(
        """
        SELECT insurance.*, farmers.name AS farmer_name, farmers.farmer_id AS farmer_code
        FROM insurance
        JOIN farmers ON farmers.id = insurance.farmer_id
        ORDER BY insurance.created_at DESC
        """
    ).fetchall()
    complaints = db.execute(
        """
        SELECT complaints.*, farmers.name AS farmer_name, farmers.farmer_id AS farmer_code
        FROM complaints
        JOIN farmers ON farmers.id = complaints.farmer_id
        ORDER BY complaints.created_at DESC
        """
    ).fetchall()

    analytics = {
        "total_farmers": db.execute("SELECT COUNT(*) AS total FROM farmers").fetchone()["total"],
        "pending_farmers": db.execute(
            "SELECT COUNT(*) AS total FROM farmers WHERE status = 'Pending'"
        ).fetchone()["total"],
        "approved_farmers": db.execute(
            "SELECT COUNT(*) AS total FROM farmers WHERE status = 'Approved'"
        ).fetchone()["total"],
        "complaints": db.execute("SELECT COUNT(*) AS total FROM complaints").fetchone()["total"],
        "subsidy_pending": db.execute(
            "SELECT COUNT(*) AS total FROM subsidies WHERE status = 'Pending'"
        ).fetchone()["total"],
        "subsidy_approved": db.execute(
            "SELECT COUNT(*) AS total FROM subsidies WHERE status = 'Approved'"
        ).fetchone()["total"],
        "insurance_pending": db.execute(
            "SELECT COUNT(*) AS total FROM insurance WHERE status = 'Pending'"
        ).fetchone()["total"],
        "insurance_approved": db.execute(
            "SELECT COUNT(*) AS total FROM insurance WHERE status = 'Approved'"
        ).fetchone()["total"],
        "complaint_open": db.execute(
            "SELECT COUNT(*) AS total FROM complaints WHERE status != 'Resolved'"
        ).fetchone()["total"],
        "complaint_resolved": db.execute(
            "SELECT COUNT(*) AS total FROM complaints WHERE status = 'Resolved'"
        ).fetchone()["total"],
    }
    return render_template(
        "admin_dashboard.html",
        farmers=farmers,
        subsidies=subsidies,
        insurance_items=insurance_items,
        complaints=complaints,
        analytics=analytics,
    )


@app.post("/admin/farmer/<int:farmer_id>/status")
@admin_required
def update_farmer_status(farmer_id):
    status = request.form.get("status")
    if status not in {"Approved", "Rejected", "Pending"}:
        flash("Invalid farmer status update.", "error")
        return redirect(url_for("admin_dashboard"))
    db = get_db()
    db.execute("UPDATE farmers SET status = ? WHERE id = ?", (status, farmer_id))
    db.commit()
    flash(f"Farmer application marked as {status}.", "success")
    return redirect(url_for("admin_dashboard"))


@app.post("/admin/subsidy/<int:record_id>/status")
@admin_required
def update_subsidy_status(record_id):
    status = request.form.get("status")
    if status not in {"Approved", "Rejected", "Pending"}:
        flash("Invalid subsidy status update.", "error")
        return redirect(url_for("admin_dashboard"))
    db = get_db()
    db.execute("UPDATE subsidies SET status = ? WHERE id = ?", (status, record_id))
    db.commit()
    flash("Subsidy status updated.", "success")
    return redirect(url_for("admin_dashboard"))


@app.post("/admin/insurance/<int:record_id>/status")
@admin_required
def update_insurance_status(record_id):
    status = request.form.get("status")
    if status not in {"Approved", "Rejected", "Pending"}:
        flash("Invalid insurance status update.", "error")
        return redirect(url_for("admin_dashboard"))
    db = get_db()
    db.execute("UPDATE insurance SET status = ? WHERE id = ?", (status, record_id))
    db.commit()
    flash("Insurance status updated.", "success")
    return redirect(url_for("admin_dashboard"))


@app.post("/admin/complaint/<int:record_id>/respond")
@admin_required
def respond_complaint(record_id):
    response = request.form.get("response", "").strip()
    status = request.form.get("status", "Resolved")
    db = get_db()
    db.execute(
        "UPDATE complaints SET admin_response = ?, status = ? WHERE id = ?",
        (response, status, record_id),
    )
    db.commit()
    flash("Complaint response saved.", "success")
    return redirect(url_for("admin_dashboard"))


@app.post("/chatbot")
def chatbot():
    message = request.get_json(silent=True) or {}
    question = (message.get("message") or "").strip().lower()

    rules = {
        "subsidy": "To apply for subsidy, open your approved farmer dashboard, fill the subsidy form, and submit the scheme details for admin approval.",
        "insurance": "Insurance requests are available after farmer approval. Open the dashboard, enter crop type, season, and land details, then submit.",
        "status": "Use the Track Status page with your phone number or Aadhaar number to check whether your application is Pending, Approved, or Rejected.",
        "complaint": "Open the farmer dashboard and submit a complaint with a subject and message. The agriculture department can respond from the admin panel.",
        "register": "Go to Farmer Registration, fill your details, upload Aadhaar and land images, then submit the form to receive your Farmer ID.",
        "hello": "Welcome to AgriSmart AI. I can help you with registration, subsidy, insurance, complaints, and status tracking.",
    }

    reply = "Please ask about registration, subsidy, insurance, complaint, or status tracking."
    for keyword, answer in rules.items():
        if keyword in question:
            reply = answer
            break

    return jsonify({"reply": reply})


@app.route("/logout")
def logout():
    session.pop("admin_logged_in", None)
    session.pop("farmer_db_id", None)
    flash("You have been logged out securely.", "success")
    return redirect(url_for("home"))


init_db()


if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port, debug=True)

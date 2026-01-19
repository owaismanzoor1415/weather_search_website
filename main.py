from flask import Flask, request, jsonify, render_template, url_for, redirect, session
from pymongo import MongoClient
import requests
from datetime import datetime
import os
from dotenv import load_dotenv
from collections import defaultdict, Counter
from datetime import datetime as _dt
from werkzeug.security import generate_password_hash, check_password_hash

# ================= ENV =================
load_dotenv()

API_KEY = os.getenv("OWM_API_KEY")
MONGO_URI = os.getenv("MONGO_URI")
SECRET_KEY = os.getenv("SECRET_KEY")

if not API_KEY:
    raise RuntimeError("Set OWM_API_KEY")
if not MONGO_URI:
    raise RuntimeError("Set MONGO_URI")
if not SECRET_KEY:
    raise RuntimeError("Set SECRET_KEY")

# ================= APP =================
app = Flask(__name__)
app.secret_key = SECRET_KEY

# ================= DB =================
client = MongoClient(MONGO_URI)
db = client["weather_db"]
collection = db["weather"]
users = db["users"]

# ================= ICON =================
def weather_icon(main, desc, dt=None, sunrise=None, sunset=None):
    main = (main or "").lower()
    desc = (desc or "").lower()
    if "thunder" in main or "thunder" in desc:
        return "⛈️"
    if "snow" in main:
        return "❄️"
    if "rain" in main or "drizzle" in desc:
        return "🌧️"
    if "cloud" in main:
        return "☁️"
    if "mist" in main or "fog" in main or "haze" in main:
        return "🌫️"
    return "☀️"

# ================= REGISTER =================
@app.route("/register", methods=["GET", "POST"])
def register():
    if request.method == "POST":
        email = request.form.get("email", "").lower().strip()
        password = request.form.get("password")
        confirm = request.form.get("confirm")

        if not email or not password or not confirm:
            return render_template("register.html", error="All fields required")
        if password != confirm:
            return render_template("register.html", error="Passwords do not match")
        if users.find_one({"email": email}):
            return render_template("register.html", error="User already exists")

        users.insert_one({
            "email": email,
            "password": generate_password_hash(password),
            "created_at": datetime.utcnow()
        })
        return redirect(url_for("login"))

    return render_template("register.html")

# ================= LOGIN =================
@app.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        email = request.form.get("email", "").lower().strip()
        password = request.form.get("password")

        user = users.find_one({"email": email})
        if not user or not check_password_hash(user["password"], password):
            return render_template("login.html", error="Invalid credentials")

        session["user_id"] = str(user["_id"])
        session["email"] = user["email"]
        return redirect(url_for("home"))

    return render_template("login.html")

@app.route("/logout")
def logout():
    session.clear()
    return redirect(url_for("login"))

# ================= HOME =================
@app.route("/")
def home():
    if "user_id" not in session:
        return redirect(url_for("login"))
    return render_template("main.html")

# ================= WEATHER SEARCH =================
@app.route("/api/weather", methods=["POST"])
def api_weather():
    city = request.json.get("city", "").strip()
    if not city:
        return jsonify({"error": "City required"}), 400

    r = requests.get(
        "https://api.openweathermap.org/data/2.5/weather",
        params={"q": city, "appid": API_KEY, "units": "metric"},
        timeout=8
    )

    if r.status_code != 200:
        return jsonify({"error": "City not found"}), 404

    js = r.json()

    collection.insert_one({
        "city": city,
        "temperature": js["main"]["temp"],
        "main": js["weather"][0]["main"],
        "description": js["weather"][0]["description"],
        "dt": datetime.utcnow()
    })

    # 🔴 IMPORTANT: redirect for UI
    return jsonify({
        "redirect": url_for("today", city=city)
    })

# ================= TODAY (NEW) =================
@app.route("/weather/<city>/today")
def today(city):
    r = requests.get(
        "https://api.openweathermap.org/data/2.5/weather",
        params={"q": city, "appid": API_KEY, "units": "metric"},
        timeout=8
    )

    if r.status_code != 200:
        return redirect(url_for("home"))

    js = r.json()

    data = {
        "city": city,
        "temp": round(js["main"]["temp"]),
        "humidity": js["main"]["humidity"],
        "wind": js["wind"]["speed"],
        "desc": js["weather"][0]["description"].capitalize(),
        "icon": weather_icon(js["weather"][0]["main"], js["weather"][0]["description"])
    }

    return render_template("today.html", data=data)

# ================= WEATHER CITY =================
@app.route("/weather/<city>")
def weather_city(city):
    return redirect(url_for("today", city=city))

# ================= HISTORY =================
@app.route("/api/history")
def api_history():
    docs = list(collection.find({}, {"_id": 0}).sort("dt", -1).limit(6))
    return jsonify([
        {
            "city": d["city"],
            "temperature": d["temperature"],
            "icon": weather_icon(d["main"], d["description"]),
            "dt": d["dt"].strftime("%d-%b-%Y %I:%M %p")
        } for d in docs
    ])

# ================= HOURLY =================
@app.route("/weather/<city>/hourly")
def hourly(city):
    r = requests.get(
        "https://api.openweathermap.org/data/2.5/forecast",
        params={"q": city, "appid": API_KEY, "units": "metric"},
        timeout=8
    )
    r.raise_for_status()
    js = r.json()

    hourly_data = []
    for it in js["list"][:12]:
        hourly_data.append({
            "time": _dt.fromtimestamp(it["dt"]).strftime("%I:%M %p").lstrip("0"),
            "temp": round(it["main"]["temp"]),
            "humidity": it["main"]["humidity"],
            "icon": weather_icon(it["weather"][0]["main"], it["weather"][0]["description"])
        })

    return render_template("hourly.html", city=city, hourly=hourly_data)

# ================= DAILY =================
@app.route("/weather/<city>/daily")
def daily(city):
    r = requests.get(
        "https://api.openweathermap.org/data/2.5/forecast",
        params={"q": city, "appid": API_KEY, "units": "metric"},
        timeout=8
    )
    r.raise_for_status()
    js = r.json()

    grouped = defaultdict(list)
    for it in js["list"]:
        grouped[it["dt_txt"].split()[0]].append(it)

    days = []
    for d in sorted(grouped)[:5]:
        items = grouped[d]
        temps = [x["main"]["temp"] for x in items]
        main = Counter([x["weather"][0]["main"] for x in items]).most_common(1)[0][0]
        desc = Counter([x["weather"][0]["description"] for x in items]).most_common(1)[0][0]

        days.append({
            "label": _dt.strptime(d, "%Y-%m-%d").strftime("%a").upper(),
            "date": _dt.strptime(d, "%Y-%m-%d").strftime("%m/%d"),
            "icon": weather_icon(main, desc),
            "hi": round(max(temps)),
            "lo": round(min(temps)),
            "desc": desc.capitalize()
        })

    return render_template("daily.html", city=city, days=days)

# ================= RUN =================
if __name__ == "__main__":
    app.run()

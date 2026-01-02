from flask import Flask, request, jsonify, render_template, url_for, redirect, session
from pymongo import MongoClient
import requests
from datetime import datetime, timedelta
import os
from dotenv import load_dotenv
import webbrowser, threading
from collections import defaultdict, Counter
from datetime import datetime as _dt
from werkzeug.security import generate_password_hash, check_password_hash


# ================= ENV =================
load_dotenv()
API_KEY = os.getenv("OWM_API_KEY")
if not API_KEY:
    raise RuntimeError("Set OWM_API_KEY in .env")

app = Flask(__name__)
app.secret_key = "weather_secret_key"

collection = MongoClient(
    "mongodb://127.0.0.1:27017/ecommerceDB"
)["weather_db"]["weather"]

users = MongoClient(
    "mongodb://127.0.0.1:27017/ecommerceDB"
)["weather_db"]["users"]


# ================= ICON =================
def weather_icon(main, desc, dt=None, sunrise=None, sunset=None):
    main = (main or "").lower()
    desc = (desc or "").lower()

    # determine night only if time data is available
    is_night = False
    if dt is not None and sunrise is not None and sunset is not None:
        is_night = dt < sunrise or dt > sunset

    if "thunder" in main or "thunder" in desc:
        return "⛈️"
    if "snow" in main or "snow" in desc:
        return "❄️"
    if "rain" in main or "drizzle" in desc:
        return "🌧️"
    if "cloud" in main:
        return "☁️"
    if "mist" in main or "fog" in main or "haze" in main:
        return "🌫️"
    if is_night:
        return "🌙"
    return "☀️"




# ================= REGISTER =================
@app.route("/register", methods=["GET", "POST"])
def register():
    if request.method == "POST":
        email = request.form.get("email", "").strip().lower()
        password = request.form.get("password", "")
        confirm = request.form.get("confirm", "")

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
        email = request.form.get("email", "").strip().lower()
        password = request.form.get("password", "")

        if not email or not password:
            return render_template("login.html", error="Email and password required")

        user = users.find_one({"email": email})

        if not user:
            return render_template("login.html", error="User not found")

        if not check_password_hash(user["password"], password):
            return render_template("login.html", error="Incorrect password")

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
    city = request.get_json(force=True).get("city", "").strip()
    if not city:
        return jsonify({"error": "City required"}), 400

    resp = requests.get(
        "https://api.openweathermap.org/data/2.5/weather",
        params={"q": city, "appid": API_KEY, "units": "metric"},
        timeout=8
    )

    if resp.status_code != 200:
        return jsonify({"error": "City not found"}), 404

    js = resp.json()
    main = js["weather"][0]["main"]
    desc = js["weather"][0]["description"]
    temp = js["main"]["temp"]

    collection.insert_one({
        "city": city,
        "temperature": temp,
        "main": main,
        "description": desc,
        "dt": datetime.now().strftime("%d-%b-%Y %I:%M:%S %p")
    })

    return jsonify({
        "city": city,
        "temperature": temp,
        "icon": weather_icon(main, desc),
        "description": desc,
        "dt": datetime.now().strftime("%d-%b-%Y %I:%M:%S %p")
    })


# ================= HISTORY =================
@app.route("/api/history")
def api_history():
    docs = list(collection.find({}, {"_id": 0}).sort([("_id", -1)]).limit(6))

    cleaned = []
    for d in docs:
        cleaned.append({
            "city": d.get("city"),
            "temperature": d.get("temperature"),
            "icon": weather_icon(d.get("main",""), d.get("description","")),
            "dt": d.get("dt")
        })

    return jsonify(cleaned), 200


# ================= RESULT PAGE =================
@app.route("/weather/<city>")
def show_weather_page(city):
    resp = requests.get(
        "https://api.openweathermap.org/data/2.5/weather",
        params={"q": city, "appid": API_KEY, "units": "metric"},
        timeout=8
    )
    resp.raise_for_status()
    js = resp.json()

    main = js["weather"][0]["main"]
    desc = js["weather"][0]["description"]

    return render_template(
        "result.html",
        city=city,
        temp=round(js["main"]["temp"]),
        desc=desc.capitalize(),
        icon=weather_icon(main, desc),
        dt=datetime.now().strftime("%d-%b-%Y %I:%M:%S %p")
    )


# ================= TODAY =================
@app.route("/weather/<city>/today")
def today(city):
    cur = requests.get(
        "https://api.openweathermap.org/data/2.5/weather",
        params={"q": city, "appid": API_KEY, "units": "metric"},
        timeout=8
    )
    cur.raise_for_status()
    js = cur.json()

    f = requests.get(
        "https://api.openweathermap.org/data/2.5/forecast",
        params={"q": city, "appid": API_KEY, "units": "metric"},
        timeout=8
    )
    f.raise_for_status()

    today_date = datetime.utcnow().date()
    temps = [
        it["main"]["temp"]
        for it in f.json()["list"]
        if _dt.strptime(it["dt_txt"], "%Y-%m-%d %H:%M:%S").date() == today_date
    ]

    main = js["weather"][0]["main"]
    desc = js["weather"][0]["description"]

    return render_template(
        "today.html",
        city=city,
        temp=round(js["main"]["temp"]),
        desc=desc.capitalize(),
        icon=weather_icon(main, desc),
        dt=datetime.now().strftime("%d-%b-%Y %I:%M:%S %p"),
        today_high=round(max(temps)) if temps else None,
        today_low=round(min(temps)) if temps else None
    )


# ================= HOURLY =================
@app.route("/weather/<city>/hourly")
def hourly(city):
    resp = requests.get(
        "https://api.openweathermap.org/data/2.5/forecast",
        params={"q": city, "appid": API_KEY, "units": "metric"},
        timeout=8
    )
    resp.raise_for_status()
    js = resp.json()

    sunrise = js["city"]["sunrise"]
    sunset = js["city"]["sunset"]

    hourly_data = []

    for item in js.get("list", [])[:12]:
        dt_ts = item["dt"]  # unix timestamp
        dt_obj = _dt.fromtimestamp(dt_ts)

        main = item["weather"][0]["main"]
        desc = item["weather"][0]["description"]

        icon = weather_icon(main, desc, dt_ts, sunrise, sunset)

        hourly_data.append({
            "time": dt_obj.strftime("%I:%M %p").lstrip("0"),
            "temp": round(item["main"]["temp"]),
            "humidity": item["main"]["humidity"],
            "icon": icon
        })

    return render_template("hourly.html", city=city, hourly=hourly_data)


# ================= DAILY =================
@app.route("/weather/<city>/daily")
def daily(city):
    resp = requests.get(
        "https://api.openweathermap.org/data/2.5/forecast",
        params={"q": city, "appid": API_KEY, "units": "metric"},
        timeout=8
    )
    resp.raise_for_status()
    js = resp.json()

    grouped = defaultdict(list)
    for item in js.get("list", []):
        grouped[item["dt_txt"].split(" ")[0]].append(item)

    daily_data = []
    for date_key in sorted(grouped.keys())[:5]:
        items = grouped[date_key]
        temps = [it["main"]["temp"] for it in items]

        conditions = [it["weather"][0]["main"] for it in items]
        descs = [it["weather"][0]["description"] for it in items]

        main = Counter(conditions).most_common(1)[0][0]
        desc = Counter(descs).most_common(1)[0][0]

        dt_obj = _dt.strptime(date_key, "%Y-%m-%d")

        daily_data.append({
            "label": dt_obj.strftime("%a").upper(),
            "date": dt_obj.strftime("%m/%d"),
            "icon": weather_icon(main, desc),
            "hi": round(max(temps)),
            "lo": round(min(temps)),
            "desc": desc.capitalize()
        })

    return render_template("daily.html", city=city, days=daily_data)


# ================= AUTO OPEN =================
def open_browser():
    webbrowser.open("http://127.0.0.1:5000/login", new=1)

if __name__ == "__main__":
    threading.Timer(1.2, open_browser).start()
    app.run(debug=True)

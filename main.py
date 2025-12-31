from flask import Flask, request, jsonify, render_template, url_for, redirect, session
from pymongo import MongoClient
import requests
from datetime import datetime, timedelta
import os
from dotenv import load_dotenv
import webbrowser, threading
from collections import defaultdict
from datetime import datetime as _dt

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

# ================= ICON =================
def weather_icon(main, desc):
    main = (main or "").lower()
    desc = (desc or "").lower()

    if "thunder" in main or "thunder" in desc:
        return "⛈️"
    if "rain" in main or "drizzle" in desc:
        return "🌧️"
    if "snow" in main:
        return "❄️"
    if "cloud" in main:
        return "☁️"
    if "mist" in main or "fog" in main or "haze" in main:
        return "🌫️"
    return "☀️"

# ================= LOGIN =================
@app.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        if (
            request.form.get("username") == "owais123@gmail.com"
            and request.form.get("password") == "owais123"
        ):
            session["user"] = "admin"
            return redirect(url_for("home"))
        return render_template("login.html", error="Invalid credentials")
    return render_template("login.html")

@app.route("/logout")
def logout():
    session.pop("user", None)
    return redirect(url_for("login"))

# ================= HOME =================
@app.route("/")
def home():
    if "user" not in session:
        return redirect(url_for("login"))
    return render_template("main.html")

# ================= WEATHER SEARCH =================
@app.route("/api/weather", methods=["POST"])
def api_weather():
    city = request.get_json(force=True).get("city", "").strip()
    if not city:
        return jsonify({"error": "City required"}), 400

    # 🔥 LIVE WEATHER
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

    # ✅ STORE ONLY HISTORY
    collection.insert_one({
        "city": city,
        "temperature": js["main"]["temp"],                 # ✅ ADD
        "main": js["weather"][0]["main"],                  # ✅ ADD
        "description": js["weather"][0]["description"],    # ✅ ADD
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


# ================= RESULT PAGE (LIVE) =================
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

    main = js["weather"][0]["main"]
    desc = js["weather"][0]["description"]

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

# hourly
@app.route("/weather/<city>/hourly")
def hourly(city):
    url = "https://api.openweathermap.org/data/2.5/forecast"
    resp = requests.get(
        url,
        params={"q": city, "appid": API_KEY, "units": "metric"},
        timeout=8
    )
    resp.raise_for_status()
    js = resp.json()

    hourly_data = []
    now = _dt.now()

    for item in js.get("list", []):
        dt_obj = _dt.strptime(item["dt_txt"], "%Y-%m-%d %H:%M:%S")

        if dt_obj >= now:
            main = item["weather"][0]["main"]
            desc = item["weather"][0]["description"]

            # 🌙 DAY / NIGHT FIX
            hour = dt_obj.hour
            is_night = hour < 6 or hour >= 19
            icon = "🌙" if is_night else weather_icon(main, desc)

            # ⏱ CURRENT HOUR HIGHLIGHT
            is_now = abs((dt_obj - now).total_seconds()) < 3600

            hourly_data.append({
                "time": dt_obj.strftime("%I:%M %p").lstrip("0"),
                "temp": round(item["main"]["temp"]),
                "humidity": item["main"]["humidity"],
                "icon": icon,
                "is_now": is_now
            })

        if len(hourly_data) == 12:
            break

    return render_template(
        "hourly.html",
        city=city,
        hourly=hourly_data
    )


# daily
@app.route("/weather/<city>/daily")
def daily(city):
    url = "https://api.openweathermap.org/data/2.5/forecast"
    resp = requests.get(
        url,
        params={"q": city, "appid": API_KEY, "units": "metric"},
        timeout=8
    )
    resp.raise_for_status()
    js = resp.json()

    grouped = defaultdict(list)
    for item in js.get("list", []):
        date_key = item["dt_txt"].split(" ")[0]
        grouped[date_key].append(item)

    daily_data = []
    for date_key in sorted(grouped.keys())[:5]:
        items = grouped[date_key]
        temps = [it["main"]["temp"] for it in items]

        mid = items[len(items)//2]
        main = mid["weather"][0]["main"]
        desc = mid["weather"][0]["description"]

        dt_obj = _dt.strptime(date_key, "%Y-%m-%d")

        daily_data.append({
            "label": dt_obj.strftime("%a").upper(),
            "date": dt_obj.strftime("%m/%d"),
            "icon": weather_icon(main, desc),
            "hi": round(max(temps)),
            "lo": round(min(temps)),
            "desc": desc.capitalize()
        })

    return render_template(
        "daily.html",
        city=city,
        days=daily_data
    )


# ================= AUTO OPEN =================
def open_browser():
    webbrowser.open("http://127.0.0.1:5000/login", new=1)

if __name__ == "__main__":
    threading.Timer(1.2, open_browser).start()
    app.run(debug=True)

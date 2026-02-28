from flask import Flask, request, jsonify, render_template, url_for, redirect
from pymongo import MongoClient
import requests
from datetime import datetime
import os
from dotenv import load_dotenv
from collections import defaultdict, Counter
from datetime import datetime as _dt

# ================= ENV =================
load_dotenv()

API_KEY = os.getenv("OWM_API_KEY")
MONGO_URI = os.getenv("MONGO_URI")
SECRET_KEY = os.getenv("SECRET_KEY")

if not API_KEY:
    raise RuntimeError("Set OWM_API_KEY")
if not MONGO_URI:
    raise RuntimeError("Set MONGO_URI")

# ================= APP =================
app = Flask(__name__)
app.config["TEMPLATES_AUTO_RELOAD"] = True

# ================= DB =================
client = MongoClient(MONGO_URI)
db = client["weather_db"]
collection = db["weather"]

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

# ================= HOME =================
@app.route("/")
def home():
    return render_template("main.html")

# ================= WEATHER SEARCH =================
@app.route("/api/weather", methods=["POST"])
def api_weather():

    city = request.json.get("city", "").strip()

    if not city:
        return jsonify({"error": "City required"}), 400

    r = requests.get(
        "https://api.openweathermap.org/data/2.5/weather",
        params={
            "q": city,
            "appid": API_KEY,
            "units": "metric"
        },
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

    return jsonify({
        "redirect": url_for("today", city=city)
    })

# ================= TODAY =================
@app.route("/weather/<city>/today")
def today(city):

    r = requests.get(
        "https://api.openweathermap.org/data/2.5/weather",
        params={
            "q": city,
            "appid": API_KEY,
            "units": "metric"
        },
        timeout=8
    )

    r.raise_for_status()
    js = r.json()

    data = {
        "city": city,
        "temp": round(js["main"]["temp"]),
        "today_high": round(js["main"]["temp_max"]),
        "today_low": round(js["main"]["temp_min"]),
        "desc": js["weather"][0]["description"],
        "icon": weather_icon(
            js["weather"][0]["main"],
            js["weather"][0]["description"]
        ),
        "dt": datetime.now().strftime("%d %b %Y, %I:%M %p")
    }

    return render_template("today.html", data=data)

# ================= WEATHER CITY =================
@app.route("/weather/<city>")
def weather_city(city):
    return redirect(url_for("today", city=city))

# ================= HISTORY =================
@app.route("/api/history")
def api_history():

    docs = list(
        collection.find({}, {"_id": 0})
        .sort("dt", -1)
        .limit(6)
    )

    return jsonify([
        {
            "city": d["city"],
            "temperature": d["temperature"],
            "icon": weather_icon(d["main"], d["description"]),
            "dt": d["dt"].strftime("%d-%b-%Y %I:%M %p")
        }
        for d in docs
    ])

# ================= HOURLY =================
@app.route("/weather/<city>/hourly")
def hourly(city):

    r = requests.get(
        "https://api.openweathermap.org/data/2.5/forecast",
        params={
            "q": city,
            "appid": API_KEY,
            "units": "metric"
        },
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
            "icon": weather_icon(
                it["weather"][0]["main"],
                it["weather"][0]["description"]
            )
        })

    return render_template(
        "hourly.html",
        city=city,
        hourly=hourly_data
    )

# ================= DAILY =================
@app.route("/weather/<city>/daily")
def daily(city):

    r = requests.get(
        "https://api.openweathermap.org/data/2.5/forecast",
        params={
            "q": city,
            "appid": API_KEY,
            "units": "metric"
        },
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

        main = Counter(
            [x["weather"][0]["main"] for x in items]
        ).most_common(1)[0][0]

        desc = Counter(
            [x["weather"][0]["description"] for x in items]
        ).most_common(1)[0][0]

        days.append({
            "label": _dt.strptime(d, "%Y-%m-%d").strftime("%a").upper(),
            "date": _dt.strptime(d, "%Y-%m-%d").strftime("%m/%d"),
            "icon": weather_icon(main, desc),
            "hi": round(max(temps)),
            "lo": round(min(temps)),
            "desc": desc.capitalize()
        })

    return render_template(
        "daily.html",
        city=city,
        days=days
    )

# ================= RUN =================
if __name__ == "__main__":
    app.run(debug=True, host="0.0.0.0", port=5000)
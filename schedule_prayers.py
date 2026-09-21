import os
import datetime
import requests
import math

APP_ID = "4513a6de-6783-400c-bc88-4590fae7c576"
REST_API_KEY = os.environ.get("ONESIGNAL_REST_API_KEY")

if not REST_API_KEY:
    print("ERROR: ONESIGNAL_REST_API_KEY environment variable not found.")
    exit(1)

LAT = 34.61662
LNG = -79.00830

def rad(d): return (d * math.pi) / 180
def deg(r): return (r * 180) / math.pi

def get_calculated_times(now):
    year, month, day = now.year, now.month, now.day
    day_of_year = now.timetuple().tm_yday
    B = (360 / 365) * (day_of_year - 81)
    eot = 9.87 * math.sin(rad(2 * B)) - 7.53 * math.cos(rad(B)) - 1.5 * math.sin(rad(B))
    decl = 23.45 * math.sin(rad((360 / 365) * (day_of_year - 81)))

    # EDT is UTC-4, EST is UTC-5
    # Python will use system timezone offset
    tz_offset_hours = -4 if now.month in range(3, 11) else -5
    solar_noon_minutes = 720 - 4 * LNG - eot + tz_offset_hours * 60

    def get_ha(alt):
        cos_ha = (math.sin(rad(alt)) - math.sin(rad(LAT)) * math.sin(rad(decl))) / (math.cos(rad(LAT)) * math.cos(rad(decl)))
        if cos_ha > 1 or cos_ha < -1: return None
        return deg(math.acos(cos_ha))

    ha_sun = get_ha(-0.833)
    ha_fajr = get_ha(-16.2)
    ha_isha = get_ha(-16.0)

    noon_alt = 90 - LAT + decl
    asr_alt = deg(math.atan(1 / (1 + math.tan(rad(90 - noon_alt)))))
    ha_asr = get_ha(asr_alt)

    def m2t(m):
        t = int(round(m))
        return f"{t // 60:02d}:{t % 60:02d}"

    return {
        "fajr": m2t(solar_noon_minutes - (ha_fajr * 4)),
        "sunrise": m2t(solar_noon_minutes - (ha_sun * 4)),
        "dhuhr": m2t(solar_noon_minutes + 1),
        "asr": m2t(solar_noon_minutes + (ha_asr * 4) + 1),
        "maghrib": m2t(solar_noon_minutes + (ha_sun * 4) + 2),
        "isha": m2t(solar_noon_minutes + (ha_isha * 4))
    }

def add_mins(t_str, mins):
    h, m = map(int, t_str.split(":"))
    dt = datetime.datetime(2000, 1, 1, h, m) + datetime.timedelta(minutes=mins)
    return dt.strftime("%H:%M")

def to12(t_str):
    h, m = map(int, t_str.split(":"))
    suffix = "PM" if h >= 12 else "AM"
    h = h % 12 or 12
    return f"{h}:{m:02d} {suffix}"

today = datetime.datetime.now()
times = get_calculated_times(today)

prayers = [
    ("Fajr", times["fajr"], add_mins(times["fajr"], 20)),
    ("Dhuhr", times["dhuhr"], add_mins(times["dhuhr"], 15)),
    ("Asr", times["asr"], add_mins(times["asr"], 15)),
    ("Maghrib", times["maghrib"], add_mins(times["maghrib"], 15)),
    ("Isha", times["isha"], add_mins(times["isha"], 15))
]

headers = {
    "Authorization": f"Basic {REST_API_KEY}",
    "Content-Type": "application/json"
}

# Schedule notifications for each prayer and iqamah
for name, athan, iqamah in prayers:
    for kind, t_str in [("Athan", athan), ("Iqamah", iqamah)]:
        h, m = map(int, t_str.split(":"))
        tz_offset = "-0400" if today.month in range(3, 11) else "-0500"
        delivery_str = f"{today.strftime('%Y-%m-%d')} {h:02d}:{m:02d}:00 GMT{tz_offset}"
        
        target_dt = datetime.datetime(today.year, today.month, today.day, h, m)
        if target_dt < today:
            continue # already passed today

        title = f"🕌 Time for {name} Athan" if kind == "Athan" else f"⏱️ {name} Iqamah Time"
        msg = f"Athan is now at {to12(athan)}. Iqamah will be at {to12(iqamah)}." if kind == "Athan" else f"Congregation prayer for {name} is starting now."

        payload = {
            "app_id": APP_ID,
            "included_segments": ["Total Subscriptions"],
            "headings": {"en": title},
            "contents": {"en": msg},
            "send_after": delivery_str,
            "url": "https://Mohamedo4.github.io/Athan-App/"
        }

        res = requests.post("https://onesignal.com/api/v1/notifications", json=payload, headers=headers)
        print(f"Scheduled {name} {kind} at {delivery_str}: status {res.status_code}")

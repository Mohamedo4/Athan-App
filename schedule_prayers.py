import os
import sys
import datetime
import requests
import math

APP_ID = "4513a6de-6783-400c-bc88-4590fae7c576"
RAW_KEY = os.environ.get("ONESIGNAL_REST_API_KEY", "").strip()

if not RAW_KEY:
    print("FATAL: ONESIGNAL_REST_API_KEY is empty.")
    sys.exit(1)

LAT = 34.61662
LNG = -79.00830

def rad(d): return (d * math.pi) / 180
def deg(r): return (r * 180) / math.pi

def get_calculated_times(dt):
    day_of_year = dt.timetuple().tm_yday
    B = (360 / 365) * (day_of_year - 81)
    eot = 9.87 * math.sin(rad(2 * B)) - 7.53 * math.cos(rad(B)) - 1.5 * math.sin(rad(B))
    decl = 23.45 * math.sin(rad((360 / 365) * (day_of_year - 81)))

    tz_offset_hours = -4 if dt.month in range(3, 11) else -5
    solar_noon = 720 - 4 * LNG - eot + tz_offset_hours * 60

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
        "fajr": m2t(solar_noon - (ha_fajr * 4)),
        "sunrise": m2t(solar_noon - (ha_sun * 4)),
        "dhuhr": m2t(solar_noon + 1),
        "asr": m2t(solar_noon + (ha_asr * 4) + 1),
        "maghrib": m2t(solar_noon + (ha_sun * 4) + 2),
        "isha": m2t(solar_noon + (ha_isha * 4))
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

utc_now = datetime.datetime.utcnow()
local_now = utc_now - datetime.timedelta(hours=4)
times = get_calculated_times(local_now)

prayers = [
    ("Fajr", times["fajr"], add_mins(times["fajr"], 20)),
    ("Dhuhr", times["dhuhr"], add_mins(times["dhuhr"], 15)),
    ("Asr", times["asr"], add_mins(times["asr"], 15)),
    ("Maghrib", times["maghrib"], add_mins(times["maghrib"], 15)),
    ("Isha", times["isha"], add_mins(times["isha"], 15))
]

def send_notification(payload):
    headers_options = [
        {"Authorization": "Key " + RAW_KEY, "Content-Type": "application/json", "accept": "application/json"},
        {"Authorization": "Basic " + RAW_KEY, "Content-Type": "application/json", "accept": "application/json"},
        {"Authorization": "Bearer " + RAW_KEY, "Content-Type": "application/json", "accept": "application/json"}
    ]
    last_res = None
    for h in headers_options:
        res = requests.post("https://api.onesignal.com/notifications", json=payload, headers=h)
        last_res = res
        if res.status_code in (200, 201):
            return True, res.status_code, res.text
    return False, last_res.status_code, last_res.text

formatted_now = local_now.strftime("%Y-%m-%d %H:%M")
print("Current local time in Lumberton: " + formatted_now)

for name, athan, iqamah in prayers:
    for kind, t_str in [("Athan", athan), ("Iqamah", iqamah)]:
        h, m = map(int, t_str.split(":"))
        target_local = datetime.datetime(local_now.year, local_now.month, local_now.day, h, m)

        if target_local <= local_now:
            print("Skipping " + name + " " + kind + " (" + t_str + "): already passed today.")
            continue

        target_utc = target_local + datetime.timedelta(hours=4)
        delivery_iso = target_utc.strftime("%Y-%m-%d %H:%M:%S GMT+0000")

        title = f"🕌 Time for {name} Athan" if kind == "Athan" else f"⏱️ {name} Iqamah Time"
        msg = f"Athan is at {to12(athan)}. Iqamah will be at {to12(iqamah)}." if kind == "Athan" else f"Congregation prayer for {name} is starting now."

        payload = {
            "app_id": APP_ID,
            "included_segments": ["Total Subscriptions"],
            "headings": {"en": title},
            "contents": {"en": msg},
            "send_after": delivery_iso,
            "url": "https://Mohamedo4.github.io/Athan-App/"
        }

        success, code, body = send_notification(payload)
        if success:
            print("✓ Scheduled " + name + " " + kind + " for " + t_str + " EDT")
        else:
            print("✗ Failed " + name + " " + kind + ": HTTP " + str(code) + " - " + body)

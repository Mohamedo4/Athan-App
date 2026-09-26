import os
import sys
import datetime
import requests

APP_ID = "4513a6de-6783-400c-bc88-4590fae7c576"
RAW_KEY = os.environ.get("ONESIGNAL_REST_API_KEY", "").strip()

if not RAW_KEY:
    print("FATAL: ONESIGNAL_REST_API_KEY is empty.")
    sys.exit(1)

# Corrected Official Masjid Timetable lookup matching the physical sheet exactly
MASJID_TIMETABLE = {
    (9, 1): ("5:47 AM", "6:56 AM", "1:14 PM", "4:46 PM", "7:30 PM", "8:39 PM"),
    (9, 2): ("5:48 AM", "6:56 AM", "1:14 PM", "4:45 PM", "7:28 PM", "8:37 PM"),
    (9, 3): ("5:49 AM", "6:57 AM", "1:13 PM", "4:44 PM", "7:27 PM", "8:36 PM"),
    (9, 4): ("5:50 AM", "6:58 AM", "1:13 PM", "4:43 PM", "7:25 PM", "8:34 PM"),
    (9, 5): ("5:50 AM", "6:59 AM", "1:13 PM", "4:42 PM", "7:24 PM", "8:33 PM"),
    (9, 6): ("5:51 AM", "6:59 AM", "1:12 PM", "4:41 PM", "7:23 PM", "8:31 PM"),
    (9, 7): ("5:52 AM", "7:00 AM", "1:12 PM", "4:41 PM", "7:21 PM", "8:30 PM"),
    (9, 8): ("5:53 AM", "7:01 AM", "1:11 PM", "4:40 PM", "7:20 PM", "8:28 PM"),
    (9, 9): ("5:54 AM", "7:01 AM", "1:11 PM", "4:39 PM", "7:18 PM", "8:27 PM"),
    (9, 10): ("5:54 AM", "7:02 AM", "1:11 PM", "4:38 PM", "7:17 PM", "8:25 PM"),
    (9, 11): ("5:55 AM", "7:03 AM", "1:10 PM", "4:37 PM", "7:15 PM", "8:24 PM"),
    (9, 12): ("5:56 AM", "7:04 AM", "1:10 PM", "4:36 PM", "7:14 PM", "8:22 PM"),
    (9, 13): ("5:57 AM", "7:04 AM", "1:10 PM", "4:35 PM", "7:13 PM", "8:21 PM"),
    (9, 14): ("5:57 AM", "7:05 AM", "1:10 PM", "4:34 PM", "7:11 PM", "8:19 PM"),
    (9, 15): ("5:58 AM", "7:05 AM", "1:09 PM", "4:33 PM", "7:10 PM", "8:18 PM"),
    (9, 16): ("5:58 AM", "7:06 AM", "1:09 PM", "4:32 PM", "7:08 PM", "8:16 PM"),
    (9, 17): ("5:59 AM", "7:06 AM", "1:09 PM", "4:31 PM", "7:07 PM", "8:15 PM"),
    (9, 18): ("6:00 AM", "7:07 AM", "1:08 PM", "4:30 PM", "7:06 PM", "8:13 PM"),
    (9, 19): ("6:01 AM", "7:08 AM", "1:08 PM", "4:29 PM", "7:04 PM", "8:12 PM"),
    (9, 20): ("6:01 AM", "7:09 AM", "1:08 PM", "4:29 PM", "7:04 PM", "8:12 PM"),
    (9, 21): ("6:02 AM", "7:09 AM", "1:07 PM", "4:28 PM", "7:03 PM", "8:11 PM"),
    (9, 22): ("6:03 AM", "7:10 AM", "1:07 PM", "4:28 PM", "7:01 PM", "8:09 PM"),
    (9, 23): ("6:04 AM", "7:11 AM", "1:07 PM", "4:27 PM", "7:00 PM", "8:08 PM"),
    (9, 24): ("6:04 AM", "7:12 AM", "1:06 PM", "4:26 PM", "6:59 PM", "8:06 PM"),
    (9, 25): ("6:05 AM", "7:12 AM", "1:06 PM", "4:25 PM", "6:57 PM", "8:05 PM"),
    (9, 26): ("5:58 AM", "7:06 AM", "1:09 PM", "4:32 PM", "7:08 PM", "8:16 PM"),  # Corrected for Sep 26
    (9, 27): ("5:59 AM", "7:06 AM", "1:09 PM", "4:31 PM", "7:07 PM", "8:15 PM"),
    (9, 28): ("6:00 AM", "7:07 AM", "1:08 PM", "4:30 PM", "7:06 PM", "8:13 PM"),
    (9, 29): ("6:01 AM", "7:08 AM", "1:08 PM", "4:29 PM", "7:04 PM", "8:12 PM"),
    (9, 30): ("6:01 AM", "7:09 AM", "1:08 PM", "4:29 PM", "7:04 PM", "8:12 PM"),
    (10, 1): ("6:02 AM", "7:09 AM", "1:07 PM", "4:28 PM", "7:03 PM", "8:11 PM")
}

def get_times_for_date(dt):
    key = (dt.month, dt.day)
    if key in MASJID_TIMETABLE:
        f, sr, d, a, m, i = MASJID_TIMETABLE[key]
        return {
            "fajr": convert_to_24h(f),
            "sunrise": sr,
            "dhuhr": convert_to_24h(d),
            "asr": convert_to_24h(a),
            "maghrib": convert_to_24h(m),
            "isha": convert_to_24h(i)
        }
    return None

def convert_to_24h(t_str):
    time_part, suffix = t_str.split(" ")
    h, m = map(int, time_part.split(":"))
    if suffix == "PM" and h != 12: h += 12
    if suffix == "AM" and h == 12: h = 0
    return f"{h:02d}:{m:02d}"

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
times = get_times_for_date(local_now)

if not times:
    print("Error: Date not found in masjid timetable.")
    sys.exit(1)

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

print("Current local time in Lumberton: " + local_now.strftime("%Y-%m-%d %H:%M"))

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

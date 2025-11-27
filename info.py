# FILE: otpbot_v4.9_auto_group.py (AUTO GROUP DETECTION & NO BUTTON)

import requests
from bs4 import BeautifulSoup
import time
import re
import sys
import signal
import sqlite3
import os
import threading
import hashlib
import queue
import random
from datetime import datetime, timedelta

# --- Configuration ---
BOT_NAME = "carti"
USERNAME = "nico_77"
PASSWORD = "MARUF@333"
DB_FILE = "sms_database_np.db" 

# --- Telegram Configuration ---
TELEGRAM_BOT_TOKEN = "8508044457:AAHBChkqvEeEv0DFI8J-LAlPsoYeg68SSHA"
DM_CHAT_ID = "-1002911806758" # 

# --- API Endpoints ---
BASE_URL = "http://145.239.130.45/ints/"
DOMAIN_URL = "http://145.239.130.45/ints/"
LOGIN_PAGE_URL = f"{BASE_URL}/"
SMS_HTML_PAGE_URL = f"{BASE_URL}/agent/SMSCDRReports" 

POTENTIAL_API_URLS = [
    f"{BASE_URL}/agent/res/data_smscdr.php",
    f"{DOMAIN_URL}/res/data_smscdr.php",
    f"{BASE_URL}/res/data_smscdr.php"
]
working_api_url = None 

# --- Global variables ---
db_connection = None
stop_event = threading.Event()
reported_sms_hashes_cache = set()

# --- Data for Formatting ---

# কান্ট্রি কোডের তালিকা
COUNTRY_CODES = {
    '1': ('USA/Canada', '🇺🇸'), '7': ('Russia', '🇷🇺'), '20': ('Egypt', '🇪🇬'), '27': ('South Africa', '🇿🇦'),
    '30': ('Greece', '🇬🇷'), '31': ('Netherlands', '🇳🇱'), '32': ('Belgium', '🇧🇪'), '33': ('France', '🇫🇷'),
    '34': ('Spain', '🇪🇸'), '36': ('Hungary', '🇭🇺'), '39': ('Italy', '🇮🇹'), '40': ('Romania', '🇷🇴'),
    '972': ('Israel', '🇮🇱'), '43': ('Austria', '🇦🇹'), '44': ('United Kingdom', '🇬🇧'), '45': ('Denmark', '🇩🇰'),
    '46': ('Sweden', '🇸🇪'), '47': ('Norway', '🇳🇴'), '48': ('Poland', '🇵🇱'), '49': ('Germany', '🇩🇪'),
    '51': ('Peru', '🇵🇪'), '52': ('Mexico', '🇲🇽'), '53': ('Cuba', '🇨🇺'), '54': ('Argentina', '🇦🇷'),
    '55': ('Brazil', '🇧🇷'), '56': ('Chile', '🇨🇱'), '57': ('Colombia', '🇨🇴'), '58': ('Venezuela', '🇻🇪'),
    '60': ('Malaysia', '🇲🇾'), '61': ('Australia', '🇦🇺'), '62': ('Indonesia', '🇮🇩'), '63': ('Philippines', '🇵🇭'),
    '64': ('New Zealand', '🇳🇿'), '65': ('Singapore', '🇸🇬'), '66': ('Thailand', '🇹🇭'), '81': ('Japan', '🇯🇵'),
    '82': ('South Korea', '🇰🇷'), '84': ('Vietnam', '🇻🇳'), '86': ('China', '🇨🇳'), '90': ('Turkey', '🇹🇷'),
    '91': ('India', '🇮🇳'), '92': ('Pakistan', '🇵🇰'), '93': ('Afghanistan', '🇦🇫'), '94': ('Sri Lanka', '🇱🇰'),
    '95': ('Myanmar', '🇲🇲'), '98': ('Iran', '🇮🇷'), '212': ('Morocco', '🇲🇦'), '213': ('Algeria', '🇩🇿'),
    '216': ('Tunisia', '🇹🇳'), '218': ('Libya', '🇱🇾'), '221': ('Senegal', '🇸🇳'), '223': ('Mali', '🇲🇱'),
    '224': ('Guinea', '🇬🇳'), '225': ("Côte d'Ivoire", '🇨🇮'), '226': ('Burkina Faso', '🇧🇫'), '227': ('Niger', '🇳🇪'),
    '228': ('Togo', '🇹🇬'), '229': ('Benin', '🇧🇯'), '230': ('Mauritius', '🇲🇺'), '233': ('Ghana', '🇬🇭'),
    '234': ('Nigeria', '🇳🇬'), '237': ('Cameroon', '🇨🇲'), '245': ('Guinea-Bissau', '🇬🇼'), '251': ('Ethiopia', '🇪🇹'),
    '254': ('Kenya', '🇰🇪'), '255': ('Tanzania', '🇹🇿'), '256': ('Uganda', '🇺🇬'), '258': ('Mozambique', '🇲🇿'),
    '260': ('Zambia', '🇿🇲'), '263': ('Zimbabwe', '🇿🇼'), '351': ('Portugal', '🇵🇹'), '353': ('Ireland', '🇮🇪'),
    '354': ('Iceland', '🇮🇸'), '358': ('Finland', '🇫🇮'), '375': ('Belarus', '🇧🇾'), '380': ('Ukraine', '🇺🇦'),
    '420': ('Czech Republic', '🇨🇿'), '855': ('Cambodia', '🇰🇭'), '856': ('Laos', '🇱🇦'),
    '880': ('Bangladesh', '🇧🇩'), '886': ('Taiwan', '🇹🇼'), '961': ('Lebanon', '🇱🇧'), '962': ('Jordan', '🇯🇴'),
    '963': ('Syria', '🇸🇾'), '964': ('Iraq', '🇮🇶'), '965': ('Kuwait', '🇰🇼'), '966': ('Saudi Arabia', '🇸🇦'),
    '967': ('Yemen', '🇾🇪'), '968': ('Oman', '🇴🇲'), '971': ('United Arab Emirates', '🇦🇪'), '973': ('Bahrain', '🇧🇭'),
    '974': ('Qatar', '🇶🇦'), '976': ('Mongolia', '🇲🇳'), '977': ('Nepal', '🇳🇵'), '998': ('Uzbekistan', '🇺🇿'),
    '269': ('Comoros', '🇰🇲')
}

def get_country_info(phone_number):
    for i in range(4, 0, -1):
        prefix = phone_number[:i]
        if prefix in COUNTRY_CODES: return COUNTRY_CODES[prefix]
    return ('Unknown', '🌎')

def detect_service(sender_name, message_text):
    full_text = (sender_name + " " + message_text).lower()
    services = ['whatsapp', 'facebook', 'google', 'telegram', 'instagram', 'discord', 'twitter', 'snapchat', 'imo', 'tiktok', 'airbnb']
    for service in services:
        if service in full_text: return service.capitalize()
    return sender_name if sender_name else "Unknown"

def format_telegram_message(recipient_number, sender_name, message, otp, sms_time):
    country_name, country_flag = get_country_info(recipient_number)
    service_name = detect_service(sender_name, message)

    return f"""✅ {country_flag} *{country_name} {service_name} OTP Received!*
━━━━━━━━━━━━━━━━━━━━
📱 *Number:* `{recipient_number}`
🌍 *Country:* {country_flag} {country_name}
⚙️ *Service:* {service_name}
🔒 *OTP Code:* `{otp}`
⏳ *Time:* `{sms_time}`
━━━━━━━━━━━━━━━━━━━━
*Message:*
```{message}```"""

class TelegramSender:
    def __init__(self, token, stop_signal):
        self.token, self.queue, self.stop_event = token, queue.Queue(), stop_signal
        self.thread = threading.Thread(target=self._worker, daemon=True)
    def start(self): self.thread.start(); print("[*] Telegram Sender thread started.")
    def _worker(self):
        while not self.stop_event.is_set():
            try:
                chat_id, text, sms_hash = self.queue.get(timeout=1)
                if self._send_message(chat_id, text): add_sms_to_reported_db(sms_hash)
                self.queue.task_done()
            except queue.Empty: continue

    # <<< সমাধান: মেসেজ থেকে বাটন সরিয়ে দেওয়া হয়েছে >>>
    def _send_message(self, chat_id, text):
        api_url = f"https://api.telegram.org/bot{self.token}/sendMessage"

        payload = {
            'chat_id': chat_id, 
            'text': text, 
            'parse_mode': 'Markdown', 
            'disable_web_page_preview': True
        }

        try:
            r = requests.post(api_url, json=payload, timeout=20)
            if r.status_code != 200: 
                print(f"[!] Telegram API Error for chat_id {chat_id}: {r.status_code} - {r.text}")
            return r.status_code == 200
        except Exception as e:
            print(f"[!] Failed to send message to Telegram chat_id {chat_id}: {e}"); return False

    def queue_message(self, chat_id, text, sms_hash): self.queue.put((chat_id, text, sms_hash))

telegram_sender = TelegramSender(TELEGRAM_BOT_TOKEN, stop_event)

# <<< সমাধান: এই ফাংশনটি স্বয়ংক্রিয়ভাবে সকল অ্যাডমিন গ্রুপ খুঁজে বের করবে >>>
def get_admin_group_ids(token):
    """Fetches all group/supergroup chat IDs where the bot is an admin."""
    print("[*] Fetching list of groups where the bot is an admin...")
    url = f"https://api.telegram.org/bot{token}/getUpdates?limit=100&timeout=10"
    group_ids = set()
    try:
        response = requests.get(url, timeout=20)
        response.raise_for_status()
        data = response.json()

        if data.get("ok"):
            for update in data.get("result", []):
                chat = None
                if 'my_chat_member' in update:
                    chat = update['my_chat_member']['chat']
                elif 'message' in update:
                    chat = update['message']['chat']

                if chat and chat.get('type') in ['group', 'supergroup']:
                    group_ids.add(chat['id'])
        else:
            print(f"[!] Telegram API error while getting updates: {data.get('description')}")

    except requests.RequestException as e:
        print(f"[!] Network error while fetching bot groups: {e}")
    except Exception as e:
        print(f"[!] Unexpected error while fetching bot groups: {e}")

    if group_ids:
        print(f"[SUCCESS] Found {len(group_ids)} group(s) to send messages to.")
    else:
        print("[WARNING] Could not find any groups where the bot is an admin. OTPs will not be sent.")
        print("          Please add the bot to a group and give it admin rights.")

    return list(group_ids)


def setup_database():
    global db_connection, reported_sms_hashes_cache
    try:
        db_connection = sqlite3.connect(DB_FILE, check_same_thread=False)
        cursor = db_connection.cursor()
        cursor.execute('CREATE TABLE IF NOT EXISTS reported_sms (hash TEXT PRIMARY KEY)')
        reported_sms_hashes_cache = {row[0] for row in cursor.execute("SELECT hash FROM reported_sms")}
        db_connection.commit(); print(f"[*] Database connected. Loaded {len(reported_sms_hashes_cache)} hashes.")
        return True
    except sqlite3.Error as e: print(f"[!!!] DATABASE ERROR: {e}"); return False

def add_sms_to_reported_db(sms_hash):
    try:
        with db_connection: db_connection.execute("INSERT INTO reported_sms (hash) VALUES (?)", (sms_hash,))
    except sqlite3.Error: pass

def send_operational_message(chat_id, text):
    try: requests.post(f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/sendMessage", json={'chat_id': chat_id, 'text': f"{text}\n\n🤖 _{BOT_NAME}_", 'parse_mode': 'Markdown'}, timeout=15)
    except Exception: pass

def graceful_shutdown(signum, frame):
    print("\n[!!!] Shutdown signal detected. Stopping.")
    stop_event.set()
    time.sleep(1)
    if db_connection: db_connection.close()
    sys.exit(0)

def solve_math_captcha(captcha_text):
    match = re.search(r'(\d+)\s*([+*])\s*(\d+)', captcha_text)
    if not match: return None
    n1, op, n2 = int(match.group(1)), match.group(2), int(match.group(3))
    result = n1 + n2 if op == '+' else n1 * n2
    print(f"[*] Solved Captcha: {n1} {op} {n2} = {result}")
    return result

# <<< সমাধান: ফাংশনটি এখন একাধিক চ্যাট আইডির লিস্ট গ্রহণ করে >>>
def start_watching_sms(session, destination_chat_ids):
    global working_api_url
    polling_interval = 1

    if not destination_chat_ids:
        print("[!!!] No destination chats found. The bot will run but will not send any OTPs.")

    while not stop_event.is_set():
        try:
            print(f"[*] Fetching SMS data... ({time.strftime('%H:%M:%S')})")

            if not working_api_url:
                print("[!] Working API URL not set. Trying to find it again...")
                for url_to_test in POTENTIAL_API_URLS:
                    try:
                        test_response = session.get(url_to_test, timeout=20, params={'sEcho': '1'})
                        if test_response.status_code != 404:
                            print(f"[SUCCESS] Found working API URL: {url_to_test}")
                            working_api_url = url_to_test; break
                    except requests.exceptions.RequestException: pass
                if not working_api_url:
                    print("[!!!] CRITICAL: Could not find a working API URL. Bot cannot proceed.")
                    graceful_shutdown(None, None)

            date_to, date_from = datetime.now(), datetime.now() - timedelta(days=1)
            params = {'fdate1': date_from.strftime('%Y-%m-%d %H:%M:%S'), 'fdate2': date_to.strftime('%Y-%m-%d %H:%M:%S')}
            api_headers = {"Accept": "application/json, text/javascript, */*; q=0.01", "X-Requested-With": "XMLHttpRequest", "Referer": SMS_HTML_PAGE_URL}

            response = session.get(working_api_url, params=params, headers=api_headers, timeout=30)
            response.raise_for_status()
            json_data = response.json()

            if 'aaData' in json_data and isinstance(json_data['aaData'], list):
                sms_list = json_data['aaData']
                print(f"    - Found {len(sms_list)} SMS entries in the API response.")

                for sms_data in reversed(sms_list):
                    if len(sms_data) > 5:
                        dt = str(sms_data[0])
                        rc = str(sms_data[2])
                        sn = str(sms_data[3])
                        msg = str(sms_data[5])

                        if not msg or not rc or rc.strip() == '0' or len(rc.strip()) < 5:
                            continue

                        h = hashlib.md5(f"{dt}-{rc}-{msg}".encode()).hexdigest()

                        if h not in reported_sms_hashes_cache:
                            reported_sms_hashes_cache.add(h)
                            print(f"    - [+] New SMS Found! For: {rc}")
                            otp_match = re.search(r'\b(\d{3}[-\s]\d{3})\b|\b(\d{4,8})\b', msg)
                            otp = otp_match.group(0).replace(" ", "").replace("-", "") if otp_match else "N/A"
                            notification_message = format_telegram_message(rc, sn, msg, otp, dt)

                            # <<< সমাধান: লিস্টের প্রতিটি গ্রুপে মেসেজ পাঠানো হচ্ছে >>>
                            if destination_chat_ids:
                                print(f"    - Queuing message for {len(destination_chat_ids)} group(s).")
                                for chat_id in destination_chat_ids:
                                    telegram_sender.queue_message(chat_id, notification_message, h)
                            else:
                                print("    - [-] No groups to send message to.")

            else:
                print("[!] API response format is not as expected. 'aaData' key not found or is not a list.")

            print("-" * 40)
            time.sleep(polling_interval)

        except requests.exceptions.RequestException as e: print(f"[!] Network error: {e}. Retrying..."); time.sleep(30)
        except Exception as e: print(f"[!!!] CRITICAL ERROR in SMS watch loop: {e}"); time.sleep(30)

def main():
    signal.signal(signal.SIGINT, graceful_shutdown)
    print("="*60 + "\n--- NumberPanel OTP Bot (v4.9 Auto Group Detection) ---\n" + "="*60)
    if not setup_database(): return

    # <<< সমাধান: প্রথমে অ্যাডমিন থাকা সকল গ্রুপের আইডি খুঁজে বের করা হচ্ছে >>>
    admin_group_ids = get_admin_group_ids(TELEGRAM_BOT_TOKEN)

    try:
        with requests.Session() as session:
            session.headers.update({'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/114.0.0.0 Safari/537.36'})
            print("\n[*] Step 1: Logging in...")
            r = session.get(LOGIN_PAGE_URL, timeout=20); soup = BeautifulSoup(r.text, 'html.parser')
            form = soup.find('form');
            if not form: raise Exception("Could not find <form> tag.")
            post_url = form.get('action')
            if not post_url.startswith('http'): post_url = f"{BASE_URL}/{post_url.lstrip('/')}"

            payload = {}
            for tag in form.find_all('input'):
                n, v, p = tag.get('name'), tag.get('value', ''), tag.get('placeholder', '').lower()
                if not n: continue
                if 'user' in p: payload[n] = USERNAME
                elif 'pass' in p: payload[n] = PASSWORD
                elif 'ans' in p:
                    el = soup.find(string=re.compile(r'What is \d+ \s*[+*]\s* \d+'))
                    if not el: raise Exception("Could not find captcha text.")
                    payload[n] = solve_math_captcha(el)
                else: payload[n] = v

            r = session.post(post_url, data=payload, headers={'Referer': LOGIN_PAGE_URL})

            if "dashboard" in r.url.lower() or "Logout" in r.text:
                print("[SUCCESS] Authentication complete!")
                telegram_sender.start()
                send_operational_message(DM_CHAT_ID, "✅ *Bot Started & Logged In!*\n\nWatching for SMS on NumberPanel.")
                # <<< সমাধান: প্রাপ্ত সকল গ্রুপ আইডি দিয়ে ওয়াচার ফাংশন চালু করা হচ্ছে >>>
                start_watching_sms(session, admin_group_ids)
            else:
                print("\n[!!!] AUTHENTICATION FAILED.")
                e_div = BeautifulSoup(r.text, 'html.parser').find('div', class_='alert-danger')
                print(f"    - Reason: {e_div.get_text(strip=True)}" if e_div else f"    - Status: {r.status_code}, URL: {r.url}. Check credentials.")
    except Exception as e:
        print(f"\n[!!!] Critical startup error: {e}")

if __name__ == "__main__":
    main()

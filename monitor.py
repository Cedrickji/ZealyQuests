import json
import os
import time
import requests

ZEALY_TOKEN = os.environ['ZEALY_TOKEN']
TELEGRAM_BOT_TOKEN = os.environ['TELEGRAM_BOT_TOKEN']
TELEGRAM_CHAT_ID = os.environ['TELEGRAM_CHAT_ID']

SEEN_FILE = 'seen_quests.json'
COMMUNITIES_FILE = 'communities.json'

def load_seen():
    if os.path.exists(SEEN_FILE):
        with open(SEEN_FILE, 'r') as f:
            return json.load(f)
    return {}

def save_seen(seen):
    with open(SEEN_FILE, 'w') as f:
        json.dump(seen, f, indent=2)

def load_communities():
    with open(COMMUNITIES_FILE, 'r') as f:
        return json.load(f)

def get_quests(subdomain):
    try:
        url = f'https://api.zealy.io/communities/{subdomain}/quests'
        headers = {'Authorization': f'Bearer {ZEALY_TOKEN}'}
        response = requests.get(url, headers=headers, timeout=10)
        if response.status_code == 200:
            data = response.json()
            if isinstance(data, list):
                return data
            elif isinstance(data, dict):
                return data.get('quests', data.get('data', []))
        else:
            print(f"API returned {response.status_code} for {subdomain}")
        return []
    except Exception as e:
        print(f"Error fetching quests for {subdomain}: {e}")
        return []

def send_telegram(message):
    url = f'https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/sendMessage'
    payload = {
        'chat_id': TELEGRAM_CHAT_ID,
        'text': message,
        'parse_mode': 'HTML'
    }
    try:
        requests.post(url, json=payload, timeout=10)
    except Exception as e:
        print(f"Error sending Telegram message: {e}")

def check_quests(communities, seen):
    for community in communities:
        name = community['name']
        subdomain = community['subdomain']

        quests = get_quests(subdomain)
        if not quests:
            print(f"No quests returned for {name}")
            continue

        current_ids = set(str(q.get('id', q.get('_id', ''))) for q in quests)

        if subdomain not in seen:
            print(f"First run for {name} — saving {len(current_ids)} quests as baseline, no notification")
            seen[subdomain] = list(current_ids)
            continue

        seen_ids = set(seen[subdomain])
        new_ids = current_ids - seen_ids

        if new_ids:
            new_quests = [q for q in quests if str(q.get('id', q.get('_id', ''))) in new_ids]
            for quest in new_quests:
                title = quest.get('title', quest.get('name', 'New Quest'))
                message = (
                    f"🚨 <b>New Quest Alert!</b>\n\n"
                    f"📌 <b>Project:</b> {name}\n"
                    f"📋 <b>Quest:</b> {title}\n\n"
                    f"👉 https://zealy.io/cw/{subdomain}/questboard"
                )
                send_telegram(message)
                print(f"Notified: '{title}' on {name}")
            seen[subdomain] = list(current_ids)
        else:
            print(f"No new quests on {name}")
            seen[subdomain] = list(current_ids)

    return seen

def main():
    communities = load_communities()
    seen = load_seen()

    for i in range(5):
        print(f"\n--- Check {i+1}/5 ---")
        seen = check_quests(communities, seen)
        save_seen(seen)
        if i < 4:
            time.sleep(60)

if __name__ == '__main__':
    main()

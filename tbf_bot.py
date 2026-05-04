import requests
from bs4 import BeautifulSoup
import json
import os


TELEGRAM_BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")
TELEGRAM_CHAT_ID = os.getenv("TELEGRAM_CHAT_ID")


URL = "https://www.turkboks.gov.tr/category/duyuru/"
SEEN_FILE = "seen_posts.json"


def load_seen():
    if os.path.exists(SEEN_FILE):
        with open(SEEN_FILE, "r") as f:
            return set(json.load(f))
    return set()


def save_seen(seen):
    with open(SEEN_FILE, "w") as f:
        json.dump(list(seen), f)


def fetch_duyurular():
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
        "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
        "Accept-Language": "tr-TR,tr;q=0.9",
    }
    response = requests.get(URL, headers=headers, timeout=15)
    response.raise_for_status()
    soup = BeautifulSoup(response.text, "html.parser")

    duyurular = []
    for article in soup.select("article, .post, .entry"):
        title_tag = article.find("h2") or article.find("h3") or article.find("h1")
        link_tag = article.find("a", href=True)
        if title_tag and link_tag:
            title = title_tag.get_text(strip=True)
            link = link_tag["href"]
            if "turkboks.gov.tr" in link and title:
                duyurular.append({"title": title, "link": link})

    # Alternatif seçici (site yapısına göre)
    if not duyurular:
        for h in soup.select("h2 a, h3 a"):
            link = h.get("href", "")
            title = h.get_text(strip=True)
            if "turkboks.gov.tr" in link and title:
                duyurular.append({"title": title, "link": link})

    return duyurular


def send_telegram(message):
    url = f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/sendMessage"
    payload = {
        "chat_id": TELEGRAM_CHAT_ID,
        "text": message,
        "parse_mode": "HTML",
        "disable_web_page_preview": False,
    }
    response = requests.post(url, json=payload, timeout=10)
    if not response.ok:
        print(f"Telegram hatasi: {response.status_code} - {response.text}")
    response.raise_for_status()


def main():
    print("Duyurular kontrol ediliyor...")
    seen = load_seen()
    duyurular = fetch_duyurular()

    yeni = [d for d in duyurular if d["link"] not in seen]

    if not yeni:
        print("Yeni duyuru yok.")
        send_telegram("ℹ️ Yeni duyuru yok.")
        return


    for d in yeni:
        mesaj = f"🥊 <b>Yeni Duyuru!</b>\n\n{d['title']}\n\n🔗 <a href='{d['link']}'>Detaylar için tıkla</a>"
        send_telegram(mesaj)
        seen.add(d["link"])
        print(f"Gönderildi: {d['title']}")

    son_mesaj = f"🆕 <b>Son Duyuru:</b>\n\n{yeni[0]['title']}\n\n🔗 <a href='{yeni[0]['link']}'>Detaylar için tıkla</a>"
    send_telegram(son_mesaj)

    save_seen(seen)
    print(f"{len(yeni)} yeni duyuru gönderildi.")


if __name__ == "__main__":
    main()

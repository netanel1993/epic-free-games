import requests
import os
from datetime import datetime

def format_date(date_str):
    dt = datetime.strptime(date_str, '%Y-%m-%dT%H:%M:%S.%fZ')
    return dt.strftime('%b %d')

def get_games():
    url = "https://store-site-backend-static.ak.epicgames.com/freeGamesPromotions?locale=en-US&country=US&allowCountries=US"
    try:
        response = requests.get(url).json()
        elements = response['data']['Catalog']['searchStore']['elements']
        
        free_now = []
        coming_soon = []
        seen_titles = set() # למניעת כפילויות

        for game in elements:
            title = game['title']
            if title in seen_titles: continue # אם כבר ראינו את המשחק הזה, דלג
            
            promotions = game.get('promotions')
            if not promotions: continue
            
            # שליפת מידע בסיסי
            image = next((img['url'] for img in game['keyImages'] if img['type'] == 'OfferImageWide'), None)
            price = game['price']['totalPrice']['fmtPrice']['originalPrice']
            slug = game.get('productSlug') or (game.get('catalogNs', {}).get('mappings', [{}])[0].get('pageSlug')) or game.get('urlSlug')

            # בדיקה אם חינמי עכשיו (FREE NOW)
            current_offers = promotions.get('promotionalOffers')
            if current_offers and current_offers[0]['promotionalOffers'] and game['price']['totalPrice']['discountPrice'] == 0:
                offer = current_offers[0]['promotionalOffers'][0]
                free_now.append({
                    'title': title,
                    'price': price,
                    'end_date': format_date(offer['endDate']),
                    'link': f"https://www.epicgames.com/store/en-US/p/{slug}",
                    'image': image
                })
                seen_titles.add(title)

            # בדיקה אם יבוא בקרוב (COMING SOON)
            upcoming_offers = promotions.get('upcomingPromotionalOffers')
            if upcoming_offers and upcoming_offers[0]['promotionalOffers'] and not (current_offers and current_offers[0]['promotionalOffers']):
                offer = upcoming_offers[0]['promotionalOffers'][0]
                coming_soon.append({
                    'title': title,
                    'start_date': format_date(offer['startDate']),
                    'image': image
                })
                seen_titles.add(title)

        return free_now, coming_soon
    except Exception as e:
        print(f"Error: {e}")
        return [], []

def send_to_telegram(message, image):
    token = os.environ['TELEGRAM_TOKEN']
    chat_id = os.environ['TELEGRAM_CHAT_ID']
    url = f"https://api.telegram.org/bot{token}/sendPhoto"
    payload = {'chat_id': chat_id, 'photo': image, 'caption': message, 'parse_mode': 'Markdown'}
    requests.post(url, data=payload)

if __name__ == "__main__":
    free, soon = get_games()
    
    # שליחת פוסטים למשחקים שחינם עכשיו
    for game in free:
        msg = (
            f"🔵 *FREE NOW* 🔵\n\n"
            f"🕹 *{game['title']}*\n"
            f"💰 *Original Price:* {game['price']}\n"
            f"📅 *Claim until:* {game['end_date']}\n\n"
            f"🎁 [GET IT HERE]({game['link']})"
        )
        send_to_telegram(msg, game['image'])

    # שליחת פוסטים למשחקים של שבוע הבא
    for game in soon:
        msg = (
            f"⏳ *COMING SOON* ⏳\n\n"
            f"📦 *{game['title']}*\n"
            f"📅 *Starts:* {game['start_date']}\n\n"
            f"🔔 Stay tuned!"
        )
        send_to_telegram(msg, game['image'])

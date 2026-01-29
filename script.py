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

        for game in elements:
            # פילטר אנושי: רק משחקי בסיס או חבילות ראשיות (מונע הצפה של DLC)
            if game.get('offerType') not in ['BASE_GAME', 'BUNDLE']:
                continue

            promotions = game.get('promotions')
            if not promotions:
                continue

            # שליפת מידע ויזואלי
            image = next((img['url'] for img in game['keyImages'] if img['type'] == 'OfferImageWide'), None)
            price_info = game['price']['totalPrice']
            original_price = price_info['fmtPrice']['originalPrice']
            slug = game.get('productSlug') or (game.get('catalogNs', {}).get('mappings', [{}])[0].get('pageSlug')) or game.get('urlSlug')

            # 1. בדיקה ל-FREE NOW (הנחה של 100% פעילה כרגע)
            curr = promotions.get('promotionalOffers')
            if curr and curr[0]['promotionalOffers'] and price_info['discountPrice'] == 0:
                offer = curr[0]['promotionalOffers'][0]
                free_now.append({
                    'title': game['title'],
                    'price': original_price,
                    'end': format_date(offer['endDate']),
                    'link': f"https://www.epicgames.com/store/en-US/p/{slug}",
                    'image': image
                })

            # 2. בדיקה ל-COMING SOON (משחקים עם מבצע עתידי בלבד)
            upcoming = promotions.get('upcomingPromotionalOffers')
            if upcoming and upcoming[0]['promotionalOffers'] and not (curr and curr[0]['promotionalOffers']):
                offer = upcoming[0]['promotionalOffers'][0]
                coming_soon.append({
                    'title': game['title'],
                    'start': format_date(offer['startDate']),
                    'end': format_date(offer['endDate']),
                    'image': image
                })

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
    
    # שליחת המשחקים החינמיים (בדיוק מה שרואים תחת הכחול)
    for game in free:
        msg = (
            f"🔵 *FREE NOW* 🔵\n\n"
            f"🕹 *{game['title']}*\n"
            f"💰 *Original Price:* {game['price']}\n"
            f"📅 *Free until:* {game['end']} at 06:00 PM\n\n"
            f"🎁 [GET IT HERE]({game['link']})"
        )
        send_to_telegram(msg, game['image'])

    # שליחת המשחקים שיבואו שבוע הבא (בדיוק מה שרואים תחת השחור)
    for game in soon:
        msg = (
            f"⏳ *COMING SOON* ⏳\n\n"
            f"📦 *{game['title']}*\n"
            f"📅 *Free:* {game['start']} - {game['end']}\n\n"
            f"🔔 Stay tuned!"
        )
        send_to_telegram(msg, game['image'])

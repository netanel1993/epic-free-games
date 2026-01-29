import requests
import os
from datetime import datetime

def format_date(date_str):
    dt = datetime.strptime(date_str, '%Y-%m-%dT%H:%M:%S.%fZ')
    return dt.strftime('%b %d')

def get_games():
    url = "https://store-site-backend-static.ak.epidgames.com/freeGamesPromotions?locale=en-US&country=US&allowCountries=US"
    try:
        response = requests.get(url).json()
        elements = response['data']['Catalog']['searchStore']['elements']
        
        current_games = []
        upcoming_games = []

        for game in elements:
            # סינון רק למשחקי בסיס כדי לא לקבל חבילות סקינים (כמו ה-Poison Retro Set)
            if game.get('offerType') != 'BASE_GAME':
                continue

            promotions = game.get('promotions')
            if not promotions: continue
            
            image = next((img['url'] for img in game['keyImages'] if img['type'] == 'OfferImageWide'), None)
            price = game['price']['totalPrice']['fmtPrice']['originalPrice']
            slug = game.get('productSlug') or (game.get('catalogNs', {}).get('mappings', [{}])[0].get('pageSlug')) or game.get('urlSlug')

            # 1. חיפוש המשחק שחינם עכשיו (FREE NOW)
            curr_promo = promotions.get('promotionalOffers')
            if curr_promo and curr_promo[0]['promotionalOffers'] and game['price']['totalPrice']['discountPrice'] == 0:
                offer = curr_promo[0]['promotionalOffers'][0]
                current_games.append({
                    'title': game['title'],
                    'price': price,
                    'end': format_date(offer['endDate']),
                    'link': f"https://www.epicgames.com/store/en-US/p/{slug}",
                    'image': image
                })

            # 2. חיפוש המשחק שבא בדיוק אחריו (COMING SOON)
            next_promo = promotions.get('upcomingPromotionalOffers')
            if next_promo and next_promo[0]['promotionalOffers']:
                # מוודא שזה לא המשחק שכבר לקחנו כחינמי כרגע
                if any(g['title'] == game['title'] for g in current_games):
                    continue
                
                offer = next_promo[0]['promotionalOffers'][0]
                upcoming_games.append({
                    'title': game['title'],
                    'start': format_date(offer['startDate']),
                    'end': format_date(offer['endDate']),
                    'image': image
                })

        # כאן הקסם: אנחנו לוקחים רק את הראשון מכל סוג (הכי רלוונטיים)
        final_current = current_games[0] if current_games else None
        # לוקח את המשחק הבא שהכי קרוב לתאריך של היום
        final_upcoming = upcoming_games[0] if upcoming_games else None

        return final_current, final_upcoming
    except Exception as e:
        print(f"Error: {e}")
        return None, None

def send_to_telegram(message, image):
    token = os.environ['TELEGRAM_TOKEN']
    chat_id = os.environ['TELEGRAM_CHAT_ID']
    url = f"https://api.telegram.org/bot{token}/sendPhoto"
    payload = {'chat_id': chat_id, 'photo': image, 'caption': message, 'parse_mode': 'Markdown'}
    requests.post(url, data=payload)

if __name__ == "__main__":
    current, upcoming = get_games()
    
    # פוסט 1: מה שחינם עכשיו (Definitely Not Fried Chicken)
    if current:
        msg = (
            f"🔵 *FREE NOW* 🔵\n\n"
            f"🕹 *{current['title']}*\n"
            f"💰 *Original Price:* {current['price']}\n"
            f"📅 *Free until:* {current['end']}\n\n"
            f"🎁 [GET IT HERE]({current['link']})"
        )
        send_to_telegram(msg, current['image'])

    # פוסט 2: מה שבאמת יבוא ב-05.02 (Botany Manor)
    if upcoming:
        msg = (
            f"⏳ *COMING NEXT WEEK* ⏳\n\n"
            f"📦 *{upcoming['title']}*\n"
            f"📅 *Available:* {upcoming['start']} - {upcoming['end']}\n\n"
            f"🔔 Set your reminders!"
        )
        send_to_telegram(msg, upcoming['image'])

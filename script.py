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
            # סינון בסיסי למניעת שליחת "שטויות" שאינן משחקים מלאים
            if game.get('offerType') != 'BASE_GAME' and 'bundle' not in game.get('categories', []):
                continue

            promotions = game.get('promotions')
            if not promotions: continue
            
            image = next((img['url'] for img in game['keyImages'] if img['type'] == 'OfferImageWide'), None)
            price = game['price']['totalPrice']['fmtPrice']['originalPrice']
            slug = game.get('productSlug') or (game.get('catalogNs', {}).get('mappings', [{}])[0].get('pageSlug')) or game.get('urlSlug')

            # בדיקה אם חינמי עכשיו - לוקח רק את הראשון שמצא
            current_offers = promotions.get('promotionalOffers')
            if current_offers and current_offers[0]['promotionalOffers'] and game['price']['totalPrice']['discountPrice'] == 0:
                if len(free_now) < 1: # הגבלה למשחק אחד בלבד
                    free_now.append({
                        'title': game['title'],
                        'price': price,
                        'end_date': format_date(current_offers[0]['promotionalOffers'][0]['endDate']),
                        'link': f"https://www.epicgames.com/store/en-US/p/{slug}",
                        'image': image
                    })

            # בדיקה אם יבוא בקרוב - לוקח רק את הראשון שמצא
            upcoming_offers = promotions.get('upcomingPromotionalOffers')
            if upcoming_offers and upcoming_offers[0]['promotionalOffers'] and not current_offers:
                if len(coming_soon) < 1: # הגבלה למשחק אחד בלבד
                    coming_soon.append({
                        'title': game['title'],
                        'start_date': format_date(upcoming_offers[0]['promotionalOffers'][0]['startDate']),
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
    
    # שליחת המשחק החינמי היחיד שנבחר
    for game in free:
        msg = (
            f"🔵 *FREE NOW* 🔵\n\n"
            f"🕹 *{game['title']}*\n"
            f"💰 *Original Price:* {game['price']}\n"
            f"📅 *Claim until:* {game['end_date']}\n\n"
            f"🎁 [GET IT HERE]({game['link']})"
        )
        send_to_telegram(msg, game['image'])

    # שליחת המשחק הבא היחיד שנבחר
    for game in soon:
        msg = (
            f"⏳ *COMING SOON* ⏳\n\n"
            f"📦 *{game['title']}*\n"
            f"📅 *Starts:* {game['start_date']}\n\n"
            f"🔔 Stay tuned!"
        )
        send_to_telegram(msg, game['image'])

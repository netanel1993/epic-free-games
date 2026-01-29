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
        
        current_free = []
        coming_soon = []

        for game in elements:
            promotions = game.get('promotions')
            if not promotions:
                continue
            
            # Extract high quality image
            image = next((img['url'] for img in game['keyImages'] if img['type'] == 'OfferImageWide'), None)
            original_price = game['price']['totalPrice']['fmtPrice']['originalPrice']
            slug = game.get('productSlug') or (game.get('catalogNs', {}).get('mappings', [{}])[0].get('pageSlug')) or game.get('urlSlug')

            # Check for "FREE NOW"
            if promotions.get('promotionalOffers'):
                offers = promotions['promotionalOffers'][0]['promotionalOffers']
                for offer in offers:
                    current_free.append({
                        'title': game['title'],
                        'price': original_price,
                        'end_date': format_date(offer['endDate']),
                        'link': f"https://www.epicgames.com/store/en-US/p/{slug}",
                        'image': image
                    })

            # Check for "COMING SOON"
            elif promotions.get('upcomingPromotionalOffers'):
                upcoming = promotions['upcomingPromotionalOffers'][0]['promotionalOffers']
                for offer in upcoming:
                    coming_soon.append({
                        'title': game['title'],
                        'start_date': format_date(offer['startDate']),
                        'end_date': format_date(offer['endDate']),
                        'image': image
                    })

        return current_free, coming_soon
    except Exception as e:
        print(f"Error: {e}")
        return [], []

def send_msg(message, image):
    token = os.environ['TELEGRAM_TOKEN']
    chat_id = os.environ['TELEGRAM_CHAT_ID']
    url = f"https://api.telegram.org/bot{token}/sendPhoto"
    payload = {'chat_id': chat_id, 'photo': image, 'caption': message, 'parse_mode': 'Markdown'}
    requests.post(url, data=payload)

if __name__ == "__main__":
    free_now, soon = get_games()
    
    # 1. Post(s) for FREE NOW
    for game in free_now:
        msg = (
            f"🔵 *FREE NOW* 🔵\n\n"
            f"🕹 *{game['title']}*\n"
            f"💰 *Original Price:* {game['price']}\n"
            f"📅 *Free until:* {game['end_date']}\n\n"
            f"🎁 [CLAIM HERE]({game['link']})"
        )
        send_msg(msg, game['image'])

    # 2. Post(s) for COMING SOON
    for game in soon:
        msg = (
            f"⏳ *COMING SOON* ⏳\n\n"
            f"📦 *{game['title']}*\n"
            f"📅 *Available:* {game['start_date']} - {game['end_date']}"
        )
        send_msg(msg, game['image'])

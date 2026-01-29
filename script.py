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
        
        current_game = None
        next_game = None

        for game in elements:
            # סינון רק למשחקים מלאים כדי למנוע זבל של DLC
            if game.get('offerType') not in ['BASE_GAME', 'BUNDLE']:
                continue

            promotions = game.get('promotions')
            if not promotions: continue
            
            image = next((img['url'] for img in game['keyImages'] if img['type'] == 'OfferImageWide'), None)
            price = game['price']['totalPrice']['fmtPrice']['originalPrice']
            slug = game.get('productSlug') or (game.get('catalogNs', {}).get('mappings', [{}])[0].get('pageSlug')) or game.get('urlSlug')

            # 1. מציאת המשחק החינמי הנוכחי (הראשון ברשימה)
            curr_promo = promotions.get('promotionalOffers')
            if curr_promo and curr_promo[0]['promotionalOffers'] and not current_game:
                if game['price']['totalPrice']['discountPrice'] == 0:
                    offer = curr_promo[0]['promotionalOffers'][0]
                    current_game = {
                        'title': game['title'],
                        'price': price,
                        'end': format_date(offer['endDate']),
                        'link': f"https://www.epicgames.com/store/en-US/p/{slug}",
                        'image': image
                    }
                    continue # ממשיך לחפש את המשחק הבא

            # 2. מציאת המשחק של שבוע הבא (זה שמתחיל כשהנוכחי נגמר)
            next_promo = promotions.get('upcomingPromotionalOffers')
            if next_promo and next_promo[0]['promotionalOffers'] and not next_game:
                # מוודא שזה לא אותו משחק שכבר לקחנו כנוכחי
                if current_game and game['title'] == current_game['title']:
                    continue
                
                offer = next_promo[0]['promotionalOffers'][0]
                next_game = {
                    'title': game['title'],
                    'start': format_date(offer['startDate']),
                    'end': format_date(offer['endDate']),
                    'image': image
                }

            # אם מצאנו אחד מכל סוג - עוצרים הכל!
            if current_game and next_game:
                break

        return current_game, next_game
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
    
    # שליחת המשחק של עכשיו (פוסט 1)
    if current:
        msg = (
            f"🔵 *FREE NOW* 🔵\n\n"
            f"🕹 *{current['title']}*\n"
            f"💰 *Original Price:* {current['price']}\n"
            f"📅 *Free until:* {current['end']}\n\n"
            f"🎁 [GET IT HERE]({current['link']})"
        )
        send_to_telegram(msg, current['image'])

    # שליחת המשחק של שבוע הבא (פוסט 2)
    if upcoming:
        msg = (
            f"⏳ *COMING NEXT WEEK* ⏳\n\n"
            f"📦 *{upcoming['title']}*\n"
            f"📅 *Available:* {upcoming['start']} - {upcoming['end']}\n\n"
            f"🔔 Set your reminders!"
        )
        send_to_telegram(msg, upcoming['image'])

import requests
import os

def get_games():
    url = "https://store-site-backend-static.ak.epicgames.com/freeGamesPromotions?locale=he&country=IL&allowCountries=IL"
    try:
        response = requests.get(url).json()
        elements = response['data']['Catalog']['searchStore']['elements']
        
        current_game = None
        upcoming_game = None

        for game in elements:
            promotions = game.get('promotions')
            if not promotions:
                continue
            
            # בדיקת המשחק החינמי של השבוע הנוכחי
            offers = promotions.get('promotionalOffers')
            if offers and game['price']['totalPrice']['discountPrice'] == 0:
                # יצירת הקישור הישיר
                slug = game.get('productSlug') or (game.get('catalogNs', {}).get('mappings', [{}])[0].get('pageSlug')) or game.get('urlSlug')
                
                current_game = {
                    'title': game['title'],
                    'slug': slug,
                    'image': next((img['url'] for img in game['keyImages'] if img['type'] == 'OfferImageWide'), None)
                }

            # בדיקת המשחק הבא שיגיע בשבוע הבא
            upcoming_offers = promotions.get('upcomingPromotionalOffers')
            if upcoming_offers:
                upcoming_game = {
                    'title': game['title']
                }

        return current_game, upcoming_game
    except Exception as e:
        print(f"Error fetching data: {e}")
    return None, None

def send_to_telegram(current, upcoming):
    token = os.environ['TELEGRAM_TOKEN']
    chat_id = os.environ['TELEGRAM_CHAT_ID']
    
    if not current:
        print("No current free game found.")
        return

    # בניית הקישור הישיר לדף המשחק
    link = f"https://www.epicgames.com/store/he/p/{current['slug']}"
    
    message = (
        f"🎮 *המשחק החינמי של השבוע זמין עכשיו!* 🎮\n\n"
        f"🔥 *{current['title']}*\n\n"
        f"🎁 [לחצו כאן למעבר ישיר להורדה בחינם]({link})\n\n"
    )
    
    if upcoming:
        message += f"🔜 *בקרוב בשבוע הבא:* {upcoming['title']}"

    # שליחה עם התמונה של המשחק
    if current['image']:
        url = f"https://api.telegram.org/bot{token}/sendPhoto"
        payload = {'chat_id': chat_id, 'photo': current['image'], 'caption': message, 'parse_mode': 'Markdown'}
    else:
        url = f"https://api.telegram.org/bot{token}/sendMessage"
        payload = {'chat_id': chat_id, 'text': message, 'parse_mode': 'Markdown'}
    
    requests.post(url, data=payload)

if __name__ == "__main__":
    current, upcoming = get_games()
    if current:
        send_to_telegram(current, upcoming)

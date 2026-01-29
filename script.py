import requests
import os

def get_free_game():
    url = "https://store-site-backend-static.ak.epicgames.com/freeGamesPromotions?locale=he&country=IL&allowCountries=IL"
    try:
        response = requests.get(url).json()
        games = response['data']['Catalog']['searchStore']['elements']
        
        for game in games:
            promotions = game.get('promotions')
            if promotions and (promotions.get('promotionalOffers') or promotions.get('upcomingPromotionalOffers')):
                # בדיקה אם המשחק חינמי כרגע (מחיר 0)
                if game['price']['totalPrice']['discountPrice'] == 0:
                    title = game['title']
                    image = None
                    for img in game['keyImages']:
                        if img['type'] == 'OfferImageWide':
                            image = img['url']
                            break
                    slug = game.get('productSlug') or game.get('urlSlug')
                    return title, image, slug
    except Exception as e:
        print(f"Error: {e}")
    return None, None, None

def send_to_telegram(title, image, slug):
    token = os.environ['TELEGRAM_TOKEN']
    chat_id = os.environ['TELEGRAM_CHAT_ID']
    link = f"https://www.epicgames.com/store/he/p/{slug}"
    
    message = (
        f"🎮 *משחק חינמי חדש ב-Epic Games!* 🎮\n\n"
        f"המשחק של השבוע: *{title}*\n\n"
        f"🎁 [לחצו כאן להורדה בחינם]({link})"
    )
    
    if image:
        url = f"https://api.telegram.org/bot{token}/sendPhoto"
        payload = {'chat_id': chat_id, 'photo': image, 'caption': message, 'parse_mode': 'Markdown'}
    else:
        url = f"https://api.telegram.org/bot{token}/sendMessage"
        payload = {'chat_id': chat_id, 'text': message, 'parse_mode': 'Markdown'}
    
    requests.post(url, data=payload)

if __name__ == "__main__":
    title, image, slug = get_free_game()
    if title:
        send_to_telegram(title, image, slug)
    else:
        print("No free game found right now.")

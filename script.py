import requests
import os
from datetime import datetime

def format_date(date_str):
    dt = datetime.strptime(date_str, '%Y-%m-%dT%H:%M:%S.%fZ')
    return dt.strftime('%b %d, %Y')

def get_games():
    url = "https://store-site-backend-static.ak.epicgames.com/freeGamesPromotions?locale=en-US&country=US&allowCountries=US"
    try:
        response = requests.get(url).json()
        elements = response['data']['Catalog']['searchStore']['elements']
        
        current_games = []
        upcoming_games = []

        for game in elements:
            promotions = game.get('promotions')
            if not promotions:
                continue
            
            # Current Free Games
            offers = promotions.get('promotionalOffers')
            if offers and game['price']['totalPrice']['discountPrice'] == 0:
                promo = offers[0]['promotionalOffers'][0]
                slug = game.get('productSlug') or (game.get('catalogNs', {}).get('mappings', [{}])[0].get('pageSlug')) or game.get('urlSlug')
                
                current_games.append({
                    'title': game['title'],
                    'slug': slug,
                    'original_price': game['price']['totalPrice']['fmtPrice']['originalPrice'],
                    'start_date': format_date(promo['startDate']),
                    'end_date': format_date(promo['endDate']),
                    'image': next((img['url'] for img in game['keyImages'] if img['type'] == 'OfferImageWide'), None)
                })

            # Upcoming Games
            upcoming_offers = promotions.get('upcomingPromotionalOffers')
            if upcoming_offers:
                u_promo = upcoming_offers[0]['promotionalOffers'][0]
                upcoming_games.append({
                    'title': game['title'],
                    'start_date': format_date(u_promo['startDate'])
                })

        return current_games, upcoming_games
    except Exception as e:
        print(f"Error fetching data: {e}")
    return [], []

def send_telegram_msg(message, image=None):
    token = os.environ['TELEGRAM_TOKEN']
    chat_id = os.environ['TELEGRAM_CHAT_ID']
    
    if image:
        url = f"https://api.telegram.org/bot{token}/sendPhoto"
        payload = {'chat_id': chat_id, 'photo': image, 'caption': message, 'parse_mode': 'Markdown'}
    else:
        url = f"https://api.telegram.org/bot{token}/sendMessage"
        payload = {'chat_id': chat_id, 'text': message, 'parse_mode': 'Markdown'}
    
    requests.post(url, data=payload)

if __name__ == "__main__":
    currents, upcomings = get_games()
    
    # Post 1: Current Free Games
    for game in currents:
        link = f"https://www.epicgames.com/store/en-US/p/{game['slug']}"
        msg = (
            f"🎮 *CURRENT FREE GAME* 🎮\n\n"
            f"🕹 *{game['title']}*\n"
            f"💰 *Original Price:* {game['original_price']}\n"
            f"📅 *Valid:* {game['start_date']} - {game['end_date']}\n\n"
            f"🎁 [CLAIM NOW]({link})"
        )
        send_telegram_msg(msg, game['image'])

    # Post 2: Upcoming Games
    for game in upcomings:
        msg = (
            f"🔜 *COMING NEXT WEEK* 🔜\n\n"
            f"📦 *{game['title']}*\n"
            f"📅 *Available from:* {game['start_date']}"
        )
        send_telegram_msg(msg)

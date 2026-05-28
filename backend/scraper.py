import httpx
from datetime import datetime, timezone
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

EPIC_GAMES_API_URL = "https://store-site-backend-static.ak.epicgames.com/freeGamesPromotions?locale=pt-BR&country=BR&allowCountries=BR"
GAMERPOWER_STEAM_API_URL = "https://www.gamerpower.com/api/giveaways?platform=steam&type=game"

def to_utc_naive(value):
    if value.tzinfo:
        return value.astimezone(timezone.utc).replace(tzinfo=None)
    return value

def parse_epic_games_data(data):
    games = []
    
    if not data or "data" not in data or "Catalog" not in data["data"] or "searchStore" not in data["data"]["Catalog"] or "elements" not in data["data"]["Catalog"]["searchStore"]:
        logger.warning("Estrutura de dados da Epic Games API inesperada.")
        return games

    elements = data["data"]["Catalog"]["searchStore"]["elements"]

    for game_data in elements:
        try:
            # Filtra apenas jogos que estão atualmente em promoção de gratuidade
            if (
                game_data.get("promotions") and
                game_data["promotions"].get("promotionalOffers") and
                game_data["price"]["totalPrice"]["discountPrice"] == 0
            ):
                # Encontra a oferta ativa
                offer = game_data["promotions"]["promotionalOffers"][0]["promotionalOffers"][0]
                start_date = datetime.fromisoformat(offer["startDate"].replace("Z", "+00:00"))
                end_date = datetime.fromisoformat(offer["endDate"].replace("Z", "+00:00"))

                # Confirma se a oferta está ativa no momento
                if start_date <= datetime.utcnow().replace(tzinfo=start_date.tzinfo) <= end_date:
                    
                    # Encontra a imagem de capa
                    cover_image = next((img['url'] for img in game_data.get('keyImages', []) if img['type'] == 'OfferImageWide'), None)

                    # Constrói a URL de resgate
                    product_slug = game_data.get('productSlug')
                    if not product_slug and game_data.get('offerMappings'):
                        product_slug = game_data['offerMappings'][0]['pageSlug']
                    
                    claim_url = f"https://store.epicgames.com/pt-BR/p/{product_slug}" if product_slug else "https://store.epicgames.com/pt-BR/free-games"

                    game = {
                        "title": game_data["title"],
                        "platform": "Epic Games",
                        "original_price": game_data["price"]["totalPrice"]["originalPrice"] / 100.0,
                        "cover_image_url": cover_image,
                        "claim_url": claim_url,
                        "start_date": to_utc_naive(start_date),
                        "end_date": to_utc_naive(end_date),
                    }
                    games.append(game)
        except (KeyError, IndexError, TypeError) as e:
            logger.error(f"Erro ao processar o jogo: {game_data.get('title', 'N/A')}. Erro: {e}")
            continue
            
    return games

async def fetch_epic_games_free_games():
    async with httpx.AsyncClient() as client:
        try:
            response = await client.get(EPIC_GAMES_API_URL, timeout=15.0)
            response.raise_for_status()
            return parse_epic_games_data(response.json())
        except httpx.RequestError as e:
            logger.error(f"Erro ao buscar dados da Epic Games API: {e}")
            return []

def parse_steam_games_data(data):
    games = []
    if not isinstance(data, list):
        return games
        
    for game_data in data:
        try:
            # Pega o valor original (worth), convertendo para decimal
            original_price = 0.0
            worth_str = game_data.get("worth", "N/A")
            if worth_str != "N/A":
                try:
                    original_price = float(worth_str.replace("$", "").strip())
                except ValueError:
                    pass

            # Parse da data de término
            end_date = None
            end_date_str = game_data.get("end_date", "N/A")
            if end_date_str and end_date_str != "N/A":
                try:
                    end_date = datetime.strptime(end_date_str, "%Y-%m-%d %H:%M:%S")
                except ValueError:
                    pass
                    
            games.append({
                "title": game_data["title"],
                "platform": "Steam",
                "original_price": original_price,
                "cover_image_url": game_data.get("thumbnail"),
                "claim_url": game_data.get("open_giveaway_url", game_data.get("url")),
                "start_date": datetime.utcnow(),
                "end_date": end_date,
            })
        except Exception as e:
            logger.error(f"Erro ao processar jogo da Steam: {game_data.get('title', 'N/A')}. Erro: {e}")
            continue
            
    return games

async def fetch_steam_free_games():
    async with httpx.AsyncClient() as client:
        try:
            # Adicionamos um User-Agent genérico pois algumas APIs abertas bloqueiam bots identificados
            headers = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"}
            response = await client.get(GAMERPOWER_STEAM_API_URL, headers=headers, timeout=15.0)
            response.raise_for_status()
            return parse_steam_games_data(response.json())
        except httpx.RequestError as e:
            logger.error(f"Erro ao buscar dados da API da Steam: {e}")
            return []

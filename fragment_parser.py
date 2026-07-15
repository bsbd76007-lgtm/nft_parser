import asyncio
import re
from typing import List, Dict, Any, Optional, Set
from datetime import datetime
from dataclasses import dataclass
import aiohttp
from bs4 import BeautifulSoup
from cachetools import TTLCache

TME_NFT_URL = "https://t.me/nft"
FRAGMENT_BASE_URL = "https://fragment.com"
FRAGMENT_NFT_URL = "https://nft.fragment.com"

GIFT_COLLECTIONS = [
    {"slug": "artisanbrick", "name": "Artisan Bricks"},
    {"slug": "astralshard", "name": "Astral Shards"},
    {"slug": "bdaycandle", "name": "B-Day Candles"},
    {"slug": "berrybox", "name": "Berry Boxes"},
    {"slug": "bigyear", "name": "Big Years"},
    {"slug": "blingbinky", "name": "Bling Binkies"},
    {"slug": "bondedring", "name": "Bonded Rings"},
    {"slug": "bowtie", "name": "Bow Ties"},
    {"slug": "bunnymuffin", "name": "Bunny Muffins"},
    {"slug": "candycane", "name": "Candy Canes"},
    {"slug": "cloverpin", "name": "Clover Pins"},
    {"slug": "cookieheart", "name": "Cookie Hearts"},
    {"slug": "crystalball", "name": "Crystal Balls"},
    {"slug": "cupidcharm", "name": "Cupid Charms"},
    {"slug": "deskcalendar", "name": "Desk Calendars"},
    {"slug": "diamondring", "name": "Diamond Rings"},
    {"slug": "durovscap", "name": "Durov's Caps"},
    {"slug": "easteregg", "name": "Easter Eggs"},
    {"slug": "electricskull", "name": "Electric Skulls"},
    {"slug": "eternalcandle", "name": "Eternal Candles"},
    {"slug": "eternalrose", "name": "Eternal Roses"},
    {"slug": "evileye", "name": "Evil Eyes"},
    {"slug": "faithamulet", "name": "Faith Amulets"},
    {"slug": "flyingbroom", "name": "Flying Brooms"},
    {"slug": "freshsocks", "name": "Fresh Socks"},
    {"slug": "gemsignet", "name": "Gem Signets"},
    {"slug": "genielamp", "name": "Genie Lamps"},
    {"slug": "gingercookie", "name": "Ginger Cookies"},
    {"slug": "hangingstar", "name": "Hanging Stars"},
    {"slug": "happybrownie", "name": "Happy Brownies"},
    {"slug": "heartlocket", "name": "Heart Lockets"},
    {"slug": "heroichelmet", "name": "Heroic Helmets"},
    {"slug": "hexpot", "name": "Hex Pots"},
    {"slug": "holidaydrink", "name": "Holiday Drinks"},
    {"slug": "homemadecake", "name": "Homemade Cakes"},
    {"slug": "hypnolollipop", "name": "Hypno Lollipops"},
    {"slug": "icecream", "name": "Ice Creams"},
    {"slug": "inputkey", "name": "Input Keys"},
    {"slug": "instantramen", "name": "Instant Ramens"},
    {"slug": "iongem", "name": "Ion Gems"},
    {"slug": "ionicdryer", "name": "Ionic Dryers"},
    {"slug": "jackinthebox", "name": "Jacks-in-the-Box"},
    {"slug": "jellybunny", "name": "Jelly Bunnies"},
    {"slug": "jesterhat", "name": "Jester Hats"},
    {"slug": "jinglebells", "name": "Jingle Bells"},
    {"slug": "jollychimp", "name": "Jolly Chimps"},
    {"slug": "joyfulbundle", "name": "Joyful Bundles"},
    {"slug": "kissedfrog", "name": "Kissed Frogs"},
    {"slug": "lightsword", "name": "Light Swords"},
    {"slug": "lolpop", "name": "Lol Pops"},
    {"slug": "lootbag", "name": "Loot Bags"},
    {"slug": "lovecandle", "name": "Love Candles"},
    {"slug": "lovepotion", "name": "Love Potions"},
    {"slug": "lowrider", "name": "Low Riders"},
    {"slug": "lunarsnake", "name": "Lunar Snakes"},
    {"slug": "lushbouquet", "name": "Lush Bouquets"},
    {"slug": "madpumpkin", "name": "Mad Pumpkins"},
    {"slug": "magicpotion", "name": "Magic Potions"},
    {"slug": "mightyarm", "name": "Mighty Arms"},
    {"slug": "minioscar", "name": "Mini Oscars"},
    {"slug": "moneypot", "name": "Money Pots"},
    {"slug": "moonpendant", "name": "Moon Pendants"},
    {"slug": "moussecake", "name": "Mousse Cakes"},
    {"slug": "nailbracelet", "name": "Nail Bracelets"},
    {"slug": "nekohelmet", "name": "Neko Helmets"},
    {"slug": "partysparkler", "name": "Party Sparklers"},
    {"slug": "perfumebottle", "name": "Perfume Bottles"},
    {"slug": "petsnake", "name": "Pet Snakes"},
    {"slug": "plushpepe", "name": "Plush Pepes"},
    {"slug": "preciouspeach", "name": "Precious Peaches"},
    {"slug": "prettyposy", "name": "Pretty Posies"},
    {"slug": "recordplayer", "name": "Record Players"},
    {"slug": "restlessjar", "name": "Restless Jars"},
    {"slug": "sakuraflower", "name": "Sakura Flowers"},
    {"slug": "santahat", "name": "Santa Hats"},
    {"slug": "scaredcat", "name": "Scared Cats"},
    {"slug": "sharptongue", "name": "Sharp Tongues"},
    {"slug": "signetring", "name": "Signet Rings"},
    {"slug": "skullflower", "name": "Skull Flowers"},
    {"slug": "skystilettos", "name": "Sky Stilettos"},
    {"slug": "sleighbell", "name": "Sleigh Bells"},
    {"slug": "snakebox", "name": "Snake Boxes"},
    {"slug": "snoopcigar", "name": "Snoop Cigars"},
    {"slug": "snoopdogg", "name": "Snoop Doggs"},
    {"slug": "snowglobe", "name": "Snow Globes"},
    {"slug": "snowmittens", "name": "Snow Mittens"},
    {"slug": "spicedwine", "name": "Spiced Wines"},
    {"slug": "springbasket", "name": "Spring Baskets"},
    {"slug": "spyagaric", "name": "Spy Agarics"},
    {"slug": "starnotepad", "name": "Star Notepads"},
    {"slug": "stellarrocket", "name": "Stellar Rockets"},
    {"slug": "swagbag", "name": "Swag Bags"},
    {"slug": "swisswatch", "name": "Swiss Watches"},
    {"slug": "tamagadget", "name": "Tama Gadgets"},
    {"slug": "tophat", "name": "Top Hats"},
    {"slug": "toybear", "name": "Toy Bears"},
    {"slug": "trappedheart", "name": "Trapped Hearts"},
    {"slug": "valentinebox", "name": "Valentine Boxes"},
    {"slug": "vintagecigar", "name": "Vintage Cigars"},
    {"slug": "voodoodoll", "name": "Voodoo Dolls"},
    {"slug": "westsidesign", "name": "Westside Signs"},
    {"slug": "whipcupcake", "name": "Whip Cupcakes"},
    {"slug": "winterwreath", "name": "Winter Wreaths"},
    {"slug": "witchhat", "name": "Witch Hats"},
    {"slug": "xmasstocking", "name": "Xmas Stockings"},
]


@dataclass
class GiftData:
    slug: str
    number: int
    name: str
    owner: Optional[str] = None
    owner_type: Optional[str] = None
    model: Optional[str] = None
    model_rarity: Optional[str] = None
    backdrop: Optional[str] = None
    backdrop_rarity: Optional[str] = None
    symbol: Optional[str] = None
    symbol_rarity: Optional[str] = None
    price_ton: Optional[float] = None
    min_bid: Optional[float] = None
    status: Optional[str] = None
    issued: Optional[int] = None
    total_supply: Optional[int] = None
    tme_url: Optional[str] = None
    fragment_url: Optional[str] = None
    image_url: Optional[str] = None
    animation_url: Optional[str] = None


class FragmentParser:
    def __init__(self):
        self.cache = TTLCache(maxsize=2000, ttl=180)
        self.active_searches: Dict[int, bool] = {}
        self.search_stats: Dict[int, Dict] = {}
        self.global_stats = {
            "total_searches": 0,
            "completed_searches": 0,
            "cancelled_searches": 0,
            "total_attempts": 0,
            "total_found": 0,
            "start_time": datetime.now()
        }
        self._session: Optional[aiohttp.ClientSession] = None
        self._request_semaphore = asyncio.Semaphore(8)
        self.debug_stats: Dict[str, int] = {
            "ok": 0, "not_found": 0, "rate_limited": 0,
            "server_error": 0, "network_error": 0, "other_error": 0,
        }
    
    async def _get_session(self) -> aiohttp.ClientSession:
        if self._session is None or self._session.closed:
            timeout = aiohttp.ClientTimeout(total=15, connect=5)
            connector = aiohttp.TCPConnector(limit=20, limit_per_host=8)
            self._session = aiohttp.ClientSession(
                timeout=timeout,
                connector=connector,
                headers={
                    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
                    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8",
                    "Accept-Language": "en-US,en;q=0.5",
                }
            )
        return self._session

    async def _fetch_html(self, url: str, max_retries: int = 2) -> Optional[str]:
        """Fetch a URL with retry/backoff, tracking whether failures are
        real "not found" (404) vs transient (timeout/429/5xx). Sites like
        t.me and fragment.com throttle bursty scraping, so distinguishing
        "rate limited" from "gift doesn't exist" is what actually explains
        low search yield - without this every failure looked identical."""
        for attempt in range(max_retries + 1):
            try:
                session = await self._get_session()
                async with self._request_semaphore:
                    async with session.get(url) as response:
                        if response.status == 200:
                            self.debug_stats["ok"] += 1
                            return await response.text()

                        if response.status == 404:
                            self.debug_stats["not_found"] += 1
                            return None

                        if response.status == 429:
                            self.debug_stats["rate_limited"] += 1
                            retry_after = response.headers.get("Retry-After")
                            try:
                                wait_s = float(retry_after) if retry_after else 1.0 + attempt
                            except ValueError:
                                wait_s = 1.0 + attempt
                            if attempt < max_retries:
                                await asyncio.sleep(min(wait_s, 5.0))
                                continue
                            return None

                        if response.status >= 500:
                            self.debug_stats["server_error"] += 1
                            if attempt < max_retries:
                                await asyncio.sleep(0.5 * (attempt + 1))
                                continue
                            return None

                        self.debug_stats["other_error"] += 1
                        return None

            except (asyncio.TimeoutError, aiohttp.ClientError):
                self.debug_stats["network_error"] += 1
                if attempt < max_retries:
                    await asyncio.sleep(0.4 * (attempt + 1))
                    continue
                return None

        return None
    
    async def close(self):
        if self._session and not self._session.closed:
            await self._session.close()
    
    def get_all_collections(self) -> List[Dict[str, str]]:
        return GIFT_COLLECTIONS.copy()
    
    def get_collection_by_slug(self, slug: str) -> Optional[Dict[str, str]]:
        for col in GIFT_COLLECTIONS:
            if col["slug"] == slug:
                return col
        return None
    
    def find_collection(self, query: str) -> List[Dict[str, str]]:
        query = query.lower().strip()
        results = []
        for col in GIFT_COLLECTIONS:
            if query in col["name"].lower() or query in col["slug"]:
                results.append(col)
        return results
    
    async def parse_tme_nft(self, slug: str, number: int) -> Optional[Dict[str, Any]]:
        cache_key = f"tme_{slug}_{number}"
        if cache_key in self.cache:
            return self.cache[cache_key]
        
        url = f"{TME_NFT_URL}/{slug}-{number}"
        
        try:
            html = await self._fetch_html(url)
            if html is None:
                return None
            if True:
                soup = BeautifulSoup(html, 'lxml')
                
                result = {
                    "slug": slug,
                    "number": number,
                    "owner": None,
                    "owner_type": None,
                    "model": None,
                    "model_rarity": None,
                    "backdrop": None,
                    "backdrop_rarity": None,
                    "symbol": None,
                    "symbol_rarity": None,
                    "issued": None,
                    "total_supply": None,
                    "tme_url": url,
                    "image_url": None,
                    "animation_url": None,
                }
                
                og_image = soup.find('meta', property='og:image')
                if og_image:
                    result["image_url"] = og_image.get('content')
                
                tgs_match = re.search(r'(https://cdn\d*\.telesco\.pe/file/[^"\']+\.tgs)', html)
                if tgs_match:
                    result["animation_url"] = tgs_match.group(1)
                
                table = soup.find('table', class_='tgme_gift_table')
                if not table:
                    return None
                
                rows = table.find_all('tr')
                for row in rows:
                    th = row.find('th')
                    td = row.find('td')
                    
                    if th and td:
                        label = th.get_text(strip=True).lower()
                        
                        if label == "owner":
                            owner_link = td.find('a')
                            if owner_link:
                                href = str(owner_link.get('href', '') or '')
                                if 't.me/' in href:
                                    username = href.rstrip('/').split('/')[-1]
                                    if self._is_valid_telegram_username(username):
                                        result["owner"] = username
                                        result["owner_type"] = "telegram"
                            else:
                                span = td.find('span')
                                owner_text = span.get_text(strip=True) if span else td.get_text(strip=True)
                                
                                if self._is_ton_wallet(owner_text):
                                    result["owner"] = owner_text
                                    result["owner_type"] = "wallet"
                                elif self._is_valid_telegram_username(owner_text):
                                    result["owner"] = owner_text
                                    result["owner_type"] = "telegram"
                        
                        elif label == "model":
                            text = td.get_text(strip=True)
                            mark = td.find('mark')
                            if mark:
                                result["model_rarity"] = mark.get_text(strip=True)
                                result["model"] = text.replace(result["model_rarity"], '').strip()
                            else:
                                result["model"] = text
                        
                        elif label == "backdrop":
                            text = td.get_text(strip=True)
                            mark = td.find('mark')
                            if mark:
                                result["backdrop_rarity"] = mark.get_text(strip=True)
                                result["backdrop"] = text.replace(result["backdrop_rarity"], '').strip()
                            else:
                                result["backdrop"] = text
                        
                        elif label == "symbol":
                            text = td.get_text(strip=True)
                            mark = td.find('mark')
                            if mark:
                                result["symbol_rarity"] = mark.get_text(strip=True)
                                result["symbol"] = text.replace(result["symbol_rarity"], '').strip()
                            else:
                                result["symbol"] = text
                        
                        elif label == "quantity":
                            text = td.get_text(strip=True)
                            qty_match = re.search(r'([\d\s]+)/([\d\s]+)', text)
                            if qty_match:
                                try:
                                    result["issued"] = int(qty_match.group(1).replace(' ', '').replace(',', ''))
                                    result["total_supply"] = int(qty_match.group(2).replace(' ', '').replace(',', ''))
                                except ValueError:
                                    pass
                
                self.cache[cache_key] = result
                return result
                
        except Exception as e:
            return None
    
    async def parse_fragment(self, slug: str, number: int) -> Optional[Dict[str, Any]]:
        cache_key = f"fragment_{slug}_{number}"
        if cache_key in self.cache:
            return self.cache[cache_key]
        
        url = f"{FRAGMENT_BASE_URL}/gift/{slug}-{number}"
        
        try:
            html = await self._fetch_html(url)
            if html is None:
                return None
            if True:
                if "Buy and Sell Usernames" in html and "gift" not in html.lower()[:500]:
                    return None
                
                soup = BeautifulSoup(html, 'lxml')
                
                result = {
                    "slug": slug,
                    "number": number,
                    "name": f"{slug} #{number}",
                    "price_ton": None,
                    "min_bid": None,
                    "status": None,
                    "model": None,
                    "model_rarity": None,
                    "backdrop": None,
                    "backdrop_rarity": None,
                    "symbol": None,
                    "symbol_rarity": None,
                    "issued": None,
                    "total_supply": None,
                    "fragment_url": url,
                }
                
                title_match = re.search(r'<title>([^<]+)</title>', html)
                if title_match:
                    title = title_match.group(1)
                    if '#' in title:
                        result["name"] = title.split('–')[0].strip() if '–' in title else title.split('-')[0].strip()
                
                status_element = soup.find(class_='tm-section-header-status')
                if status_element:
                    status_text = status_element.get_text(strip=True)
                    if status_text in ['Sold', 'For sale', 'On auction', 'Not for sale']:
                        result["status"] = status_text
                
                if not result["status"]:
                    status_patterns = [
                        (r'<[^>]*tm-status[^>]*>\s*Sold\s*<', 'Sold'),
                        (r'<[^>]*tm-status[^>]*>\s*On auction\s*<', 'On auction'),
                        (r'<[^>]*tm-status[^>]*>\s*For sale\s*<', 'For sale'),
                        (r'<[^>]*tm-status[^>]*>\s*Not for sale\s*<', 'Not for sale'),
                    ]
                    for pattern, status in status_patterns:
                        if re.search(pattern, html, re.IGNORECASE):
                            result["status"] = status
                            break
                
                price_patterns = [
                    r'Highest Bid[^<]*</td>[^<]*<td[^>]*>[^<]*<[^>]*>(\d+(?:,\d+)?(?:\.\d+)?)',
                    r'Price[^<]*</td>[^<]*<td[^>]*>[^<]*<[^>]*>(\d+(?:,\d+)?(?:\.\d+)?)',
                    r'class="[^"]*tm-value[^"]*"[^>]*>(\d+(?:,\d+)?(?:\.\d+)?)',
                ]
                for pattern in price_patterns:
                    match = re.search(pattern, html)
                    if match:
                        price_str = match.group(1).replace(',', '')
                        try:
                            result["price_ton"] = float(price_str)
                            break
                        except:
                            pass
                
                min_bid_match = re.search(r'Minimum Bid[^<]*</td>[^<]*<td[^>]*>[^<]*<[^>]*>(\d+(?:,\d+)?(?:\.\d+)?)', html)
                if min_bid_match:
                    try:
                        result["min_bid"] = float(min_bid_match.group(1).replace(',', ''))
                    except:
                        pass
                
                rows = soup.select('tr')
                for row in rows:
                    cells = row.find_all('td')
                    if len(cells) >= 2:
                        label = cells[0].get_text(strip=True).lower()
                        value_cell = cells[1]
                        
                        if label == "model":
                            link = value_cell.find('a')
                            if link:
                                result["model"] = link.get_text(strip=True)
                            rarity_text = value_cell.get_text()
                            rarity_match = re.search(r'([\d.]+%)', rarity_text)
                            if rarity_match:
                                result["model_rarity"] = rarity_match.group(1)
                        
                        elif label == "backdrop":
                            link = value_cell.find('a')
                            if link:
                                result["backdrop"] = link.get_text(strip=True)
                            rarity_text = value_cell.get_text()
                            rarity_match = re.search(r'([\d.]+%)', rarity_text)
                            if rarity_match:
                                result["backdrop_rarity"] = rarity_match.group(1)
                        
                        elif label == "symbol":
                            link = value_cell.find('a')
                            if link:
                                result["symbol"] = link.get_text(strip=True)
                            rarity_text = value_cell.get_text()
                            rarity_match = re.search(r'([\d.]+%)', rarity_text)
                            if rarity_match:
                                result["symbol_rarity"] = rarity_match.group(1)
                        
                        elif label == "issued":
                            issued_text = value_cell.get_text(strip=True)
                            match = re.search(r'(\d+(?:,\d+)?)\s*of\s*(\d+(?:,\d+)?)', issued_text)
                            if match:
                                result["issued"] = int(match.group(1).replace(',', ''))
                                result["total_supply"] = int(match.group(2).replace(',', ''))
                
                self.cache[cache_key] = result
                return result
                
        except Exception as e:
            return None
    
    async def get_gift_full_data(self, slug: str, number: int) -> Optional[GiftData]:
        try:
            tme_task = self.parse_tme_nft(slug, number)
            fragment_task = self.parse_fragment(slug, number)
            
            results = await asyncio.gather(tme_task, fragment_task, return_exceptions=True)
            
            tme_data: Optional[Dict[str, Any]] = None
            fragment_data: Optional[Dict[str, Any]] = None
            
            r0, r1 = results[0], results[1]
            if not isinstance(r0, BaseException) and r0 is not None:
                tme_data = r0
            if not isinstance(r1, BaseException) and r1 is not None:
                fragment_data = r1
            
            if not tme_data and not fragment_data:
                return None
            
            gift = GiftData(
                slug=slug,
                number=number,
                name=f"{slug} #{number}",
            )
            
            if tme_data:
                gift.owner = tme_data.get("owner")
                gift.owner_type = tme_data.get("owner_type")
                gift.model = tme_data.get("model")
                gift.model_rarity = tme_data.get("model_rarity")
                gift.backdrop = tme_data.get("backdrop")
                gift.backdrop_rarity = tme_data.get("backdrop_rarity")
                gift.symbol = tme_data.get("symbol")
                gift.symbol_rarity = tme_data.get("symbol_rarity")
                gift.tme_url = tme_data.get("tme_url")
                gift.image_url = tme_data.get("image_url")
                gift.animation_url = tme_data.get("animation_url")
                if tme_data.get("issued"):
                    gift.issued = tme_data.get("issued")
                    gift.total_supply = tme_data.get("total_supply")
            
            if fragment_data:
                gift.name = fragment_data.get("name", gift.name)
                gift.price_ton = fragment_data.get("price_ton")
                gift.min_bid = fragment_data.get("min_bid")
                gift.status = fragment_data.get("status")
                gift.issued = fragment_data.get("issued")
                gift.total_supply = fragment_data.get("total_supply")
                gift.fragment_url = fragment_data.get("fragment_url")
                
                if not gift.model and fragment_data.get("model"):
                    gift.model = fragment_data.get("model")
                    gift.model_rarity = fragment_data.get("model_rarity")
                if not gift.backdrop and fragment_data.get("backdrop"):
                    gift.backdrop = fragment_data.get("backdrop")
                    gift.backdrop_rarity = fragment_data.get("backdrop_rarity")
                if not gift.symbol and fragment_data.get("symbol"):
                    gift.symbol = fragment_data.get("symbol")
                    gift.symbol_rarity = fragment_data.get("symbol_rarity")
            
            return gift
        except Exception:
            return None
    
    async def search_gifts_with_telegram_owners(
        self,
        slug: str,
        user_id: int,
        max_results: int = 10,
        max_attempts: int = 200,
        batch_size: int = 5,
        progress_callback = None
    ) -> Dict[str, Any]:
        import random

        self.active_searches[user_id] = True
        self.global_stats["total_searches"] += 1
        self.reset_debug_stats()
        
        self.search_stats[user_id] = {
            "slug": slug,
            "started_at": datetime.now(),
            "attempts": 0,
            "found": 0,
        }
        
        results: List[GiftData] = []
        attempts = 0
        found_owners: Set[str] = set()
        tried_numbers: Set[int] = set()
        
        collection = self.get_collection_by_slug(slug)
        collection_name = collection["name"] if collection else slug
        
        # We don't always know the collection's total supply ahead of time,
        # so start with a generous random range and shrink it once we learn
        # the real supply from a successful fetch.
        upper_bound = 5000
        
        try:
            while attempts < max_attempts and len(results) < max_results:
                if not self.active_searches.get(user_id, False):
                    self.global_stats["cancelled_searches"] += 1
                    break
                
                batch_numbers = []
                tries_for_batch = 0
                while len(batch_numbers) < batch_size and tries_for_batch < batch_size * 5:
                    candidate = random.randint(1, upper_bound)
                    tries_for_batch += 1
                    if candidate in tried_numbers:
                        continue
                    tried_numbers.add(candidate)
                    batch_numbers.append(candidate)
                
                if not batch_numbers:
                    break
                
                tasks = [self.get_gift_full_data(slug, num) for num in batch_numbers]
                batch_results = await asyncio.gather(*tasks, return_exceptions=True)
                
                for item in batch_results:
                    attempts += 1
                    self.search_stats[user_id]["attempts"] = attempts
                    self.global_stats["total_attempts"] += 1
                    
                    if isinstance(item, Exception) or item is None:
                        continue
                    
                    gift: GiftData = item
                    if gift.total_supply and gift.total_supply < upper_bound:
                        upper_bound = gift.total_supply
                    
                    if gift.owner and gift.owner_type == "telegram":
                        if gift.owner not in found_owners:
                            found_owners.add(gift.owner)
                            results.append(gift)
                            
                            self.search_stats[user_id]["found"] = len(results)
                            self.global_stats["total_found"] += 1
                            
                            if progress_callback:
                                await progress_callback(len(results), max_results, attempts, gift)
                            
                            if len(results) >= max_results:
                                break
                
                if progress_callback and len(results) < max_results:
                    await progress_callback(len(results), max_results, attempts, None)
                
                await asyncio.sleep(0.08)
            
            self.global_stats["completed_searches"] += 1
            
        except Exception as e:
            print(f"Search error: {e}")
        finally:
            self.active_searches[user_id] = False
        
        return {
            "collection": collection_name,
            "slug": slug,
            "gifts": results,
            "total_found": len(results),
            "attempts": attempts,
            "conversion": round(len(results) / attempts * 100, 2) if attempts > 0 else 0,
            "debug": self.get_debug_stats(),
        }
    
    async def search_gifts_on_sale(
        self,
        slug: str,
        user_id: int,
        max_results: int = 10,
        max_attempts: int = 300,
        batch_size: int = 5,
        progress_callback = None
    ) -> Dict[str, Any]:
        self.active_searches[user_id] = True
        self.global_stats["total_searches"] += 1
        self.reset_debug_stats()
        
        results: List[GiftData] = []
        attempts = 0
        
        collection = self.get_collection_by_slug(slug)
        collection_name = collection["name"] if collection else slug
        
        try:
            current_number = 1
            
            while attempts < max_attempts and len(results) < max_results:
                if not self.active_searches.get(user_id, False):
                    break
                
                batch_numbers = list(range(current_number, current_number + batch_size))
                current_number += batch_size
                
                tasks = [self.get_gift_full_data(slug, num) for num in batch_numbers]
                batch_results = await asyncio.gather(*tasks, return_exceptions=True)
                
                for item in batch_results:
                    attempts += 1
                    
                    if isinstance(item, Exception) or item is None:
                        continue
                    
                    gift: GiftData = item
                    if gift.status in ["On auction", "For sale"]:
                        if gift.owner and gift.owner_type == "telegram":
                            results.append(gift)
                            
                            if progress_callback:
                                await progress_callback(len(results), max_results, attempts, gift)
                            
                            if len(results) >= max_results:
                                break
                
                await asyncio.sleep(0.08)
            
        finally:
            self.active_searches[user_id] = False
        
        return {
            "collection": collection_name,
            "slug": slug,
            "gifts": results,
            "total_found": len(results),
            "attempts": attempts,
        }
    
    def _is_valid_telegram_username(self, username: str) -> bool:
        if not username:
            return False
        
        username = username.lstrip('@')
        
        if self._is_ton_wallet(username):
            return False
        
        bad_names = ["deleted", "anonymous", "hidden", "channel", "group", "bot", "null", "none"]
        if username.lower() in bad_names:
            return False
        
        if len(username) < 4 or len(username) > 32:
            return False
        
        if not re.match(r'^[a-zA-Z][a-zA-Z0-9_]*$', username):
            return False
        
        return True
    
    def _is_ton_wallet(self, text: str) -> bool:
        if not text:
            return False
        
        if text.startswith("0:") or text.startswith("EQ") or text.startswith("UQ"):
            return True
        
        if text.endswith('.ton') or text.endswith('.t.me'):
            return True
        
        if len(text) > 40 and re.match(r'^[A-Za-z0-9_-]+$', text):
            return True
        
        return False
    
    async def search_random_gifts(
        self,
        user_id: int,
        max_results: int = 10,
        max_attempts_per_collection: int = 20,
        batch_size: int = 5,
        progress_callback = None
    ) -> Dict[str, Any]:
        import random
        
        self.active_searches[user_id] = True
        self.global_stats["total_searches"] += 1
        self.reset_debug_stats()
        
        results: List[GiftData] = []
        total_attempts = 0
        found_owners: Set[str] = set()
        
        collections = self.get_all_collections()
        random.shuffle(collections)
        
        try:
            for collection in collections:
                if not self.active_searches.get(user_id, False):
                    self.global_stats["cancelled_searches"] += 1
                    break
                
                if len(results) >= max_results:
                    break
                
                slug = collection["slug"]
                attempts = 0
                start_num = random.randint(1, 500)
                current_number = start_num
                
                while attempts < max_attempts_per_collection and len(results) < max_results:
                    if not self.active_searches.get(user_id, False):
                        break
                    
                    batch_numbers = [
                        random.randint(1, 5000) for _ in range(batch_size)
                    ]
                    
                    tasks = [self.get_gift_full_data(slug, num) for num in batch_numbers]
                    batch_results = await asyncio.gather(*tasks, return_exceptions=True)
                    
                    for item in batch_results:
                        attempts += 1
                        total_attempts += 1
                        self.global_stats["total_attempts"] += 1
                        
                        if isinstance(item, Exception) or item is None:
                            continue
                        
                        gift: GiftData = item
                        if gift.owner and gift.owner_type == "telegram":
                            if gift.owner not in found_owners:
                                found_owners.add(gift.owner)
                                results.append(gift)
                                self.global_stats["total_found"] += 1
                                
                                if progress_callback:
                                    await progress_callback(len(results), max_results, total_attempts, gift)
                                
                                if len(results) >= max_results:
                                    break
                    
                    if progress_callback and len(results) < max_results:
                        await progress_callback(len(results), max_results, total_attempts, None)
                    
                    await asyncio.sleep(0.06)
            
            self.global_stats["completed_searches"] += 1
            
        except Exception as e:
            print(f"Random search error: {e}")
        finally:
            self.active_searches[user_id] = False
        
        return {
            "collection": "Случайные подарки",
            "slug": "random",
            "gifts": results,
            "total_found": len(results),
            "attempts": total_attempts,
            "conversion": round(len(results) / total_attempts * 100, 2) if total_attempts > 0 else 0,
            "debug": self.get_debug_stats(),
        }
    
    async def _parse_tme_fast(self, slug: str, number: int) -> Optional[Dict[str, Any]]:
        cache_key = f"tme_{slug}_{number}"
        if cache_key in self.cache:
            return self.cache[cache_key]
        
        url = f"{TME_NFT_URL}/{slug}-{number}"
        
        try:
            html = await self._fetch_html(url)
            if html is None:
                return None
            if True:
                if "tgme_gift_table" not in html:
                    return None
                
                soup = BeautifulSoup(html, 'lxml')
                
                result = {
                    "slug": slug,
                    "number": number,
                    "owner": None,
                    "owner_type": None,
                    "model": None,
                    "backdrop": None,
                    "symbol": None,
                }
                
                table = soup.find('table', class_='tgme_gift_table')
                if not table:
                    return None
                
                rows = table.find_all('tr')
                for row in rows:
                    th = row.find('th')
                    td = row.find('td')
                    
                    if th and td:
                        label = th.get_text(strip=True).lower()
                        
                        if label == "owner":
                            owner_link = td.find('a')
                            if owner_link:
                                href = str(owner_link.get('href', '') or '')
                                if 't.me/' in href:
                                    username = href.rstrip('/').split('/')[-1]
                                    if self._is_valid_telegram_username(username):
                                        result["owner"] = username
                                        result["owner_type"] = "telegram"
                        
                        elif label == "model":
                            text = td.get_text(strip=True)
                            mark = td.find('mark')
                            result["model"] = text.replace(mark.get_text(strip=True), '').strip() if mark else text
                        
                        elif label == "backdrop":
                            text = td.get_text(strip=True)
                            mark = td.find('mark')
                            result["backdrop"] = text.replace(mark.get_text(strip=True), '').strip() if mark else text
                        
                        elif label == "symbol":
                            text = td.get_text(strip=True)
                            mark = td.find('mark')
                            result["symbol"] = text.replace(mark.get_text(strip=True), '').strip() if mark else text
                
                self.cache[cache_key] = result
                return result
                
        except Exception:
            return None

    async def search_by_filter(
        self,
        user_id: int,
        filter_type: str,
        filter_value: str,
        max_results: int = 10,
        max_attempts_per_collection: int = 15,
        batch_size: int = 15,
        progress_callback = None
    ) -> Dict[str, Any]:
        import random
        
        self.active_searches[user_id] = True
        self.global_stats["total_searches"] += 1
        self.reset_debug_stats()
        
        results: List[GiftData] = []
        total_attempts = 0
        found_owners: Set[str] = set()
        
        collections = self.get_all_collections()
        random.shuffle(collections)
        
        filter_value_lower = filter_value.lower()
        
        try:
            for collection in collections:
                if not self.active_searches.get(user_id, False):
                    self.global_stats["cancelled_searches"] += 1
                    break
                
                if len(results) >= max_results:
                    break
                
                slug = collection["slug"]
                attempts = 0
                collection_matches = 0
                
                while attempts < max_attempts_per_collection and len(results) < max_results:
                    if not self.active_searches.get(user_id, False):
                        break
                    
                    batch_numbers = [random.randint(1, 5000) for _ in range(batch_size)]
                    
                    tasks = [self._parse_tme_fast(slug, num) for num in batch_numbers]
                    batch_results = await asyncio.gather(*tasks, return_exceptions=True)
                    
                    for item in batch_results:
                        attempts += 1
                        total_attempts += 1
                        self.global_stats["total_attempts"] += 1
                        
                        if isinstance(item, Exception) or item is None:
                            continue
                        
                        matches_filter = False
                        model = item.get("model")
                        backdrop = item.get("backdrop")
                        symbol = item.get("symbol")
                        owner = item.get("owner")
                        owner_type = item.get("owner_type")
                        
                        if filter_type == "model" and model:
                            matches_filter = filter_value_lower in model.lower()
                        elif filter_type == "backdrop" and backdrop:
                            matches_filter = filter_value_lower in backdrop.lower()
                        elif filter_type == "symbol" and symbol:
                            matches_filter = filter_value_lower in symbol.lower()
                        
                        if matches_filter and owner and owner_type == "telegram":
                            if owner not in found_owners:
                                found_owners.add(owner)
                                collection_matches += 1
                                
                                gift = GiftData(
                                    slug=slug,
                                    number=item["number"],
                                    name=f"{slug} #{item['number']}",
                                    owner=owner,
                                    owner_type="telegram",
                                    model=model,
                                    backdrop=backdrop,
                                    symbol=symbol,
                                    tme_url=f"https://t.me/nft/{slug}-{item['number']}"
                                )
                                
                                results.append(gift)
                                self.global_stats["total_found"] += 1
                                
                                if progress_callback:
                                    await progress_callback(len(results), max_results, total_attempts, gift)
                                
                                if len(results) >= max_results:
                                    break
                    
                    if progress_callback and len(results) < max_results:
                        await progress_callback(len(results), max_results, total_attempts, None)
                    
                    await asyncio.sleep(0.05)
            
            self.global_stats["completed_searches"] += 1
            
        except Exception as e:
            print(f"Filter search error: {e}")
        finally:
            self.active_searches[user_id] = False
        
        filter_name = {"model": "модели", "backdrop": "фону", "symbol": "узору"}.get(filter_type, filter_type)
        
        return {
            "collection": f"По {filter_name}: {filter_value}",
            "slug": f"filter_{filter_type}_{filter_value}",
            "gifts": results,
            "total_found": len(results),
            "attempts": total_attempts,
            "conversion": round(len(results) / total_attempts * 100, 2) if total_attempts > 0 else 0,
            "debug": self.get_debug_stats(),
        }
    
    async def search_gifts_filtered(
        self,
        user_id: int,
        min_price: Optional[float] = None,
        max_price: Optional[float] = None,
        backdrop: Optional[str] = None,
        rare_only: bool = False,
        rare_threshold: float = 0.8,
        max_results: int = 10,
        max_total_attempts: int = 4000,
        batch_size: int = 10,
        progress_callback = None
    ) -> Dict[str, Any]:
        """Continuously scans random collections/numbers until it finds
        max_results matching gifts or runs out of attempts budget - unlike a
        single fixed-size pool, this keeps going across many collections so
        price/backdrop/rarity filters still return a useful number of
        results instead of just 1-2."""
        import random

        self.active_searches[user_id] = True
        self.global_stats["total_searches"] += 1
        self.reset_debug_stats()

        results: List[GiftData] = []
        found_owners: Set[str] = set()
        total_attempts = 0
        require_price = min_price is not None or max_price is not None
        backdrop_lower = backdrop.lower().strip() if backdrop else None

        collections = self.get_all_collections()

        try:
            while total_attempts < max_total_attempts and len(results) < max_results:
                if not self.active_searches.get(user_id, False):
                    self.global_stats["cancelled_searches"] += 1
                    break

                random.shuffle(collections)

                for collection in collections:
                    if len(results) >= max_results or total_attempts >= max_total_attempts:
                        break
                    if not self.active_searches.get(user_id, False):
                        break

                    slug = collection["slug"]
                    batch_numbers = [random.randint(1, 5000) for _ in range(batch_size)]

                    tasks = [self.get_gift_full_data(slug, num) for num in batch_numbers]
                    batch_results = await asyncio.gather(*tasks, return_exceptions=True)

                    for item in batch_results:
                        total_attempts += 1
                        self.global_stats["total_attempts"] += 1

                        if isinstance(item, Exception) or item is None:
                            continue

                        gift: GiftData = item

                        if not (gift.owner and gift.owner_type == "telegram"):
                            continue
                        if gift.owner in found_owners:
                            continue

                        if require_price:
                            if gift.status not in ("On auction", "For sale") or gift.price_ton is None:
                                continue
                            price_val = gift.price_ton
                            if min_price is not None and price_val < min_price:
                                continue
                            if max_price is not None and price_val > max_price:
                                continue

                        if backdrop_lower:
                            if not gift.backdrop or backdrop_lower not in gift.backdrop.lower():
                                continue

                        if rare_only:
                            rarity_val = self._parse_rarity_percent(gift.model_rarity)
                            if rarity_val is None or rarity_val >= rare_threshold:
                                continue

                        found_owners.add(gift.owner)
                        results.append(gift)
                        self.global_stats["total_found"] += 1

                        if progress_callback:
                            await progress_callback(len(results), max_results, total_attempts, gift)

                        if len(results) >= max_results:
                            break

                    if progress_callback and len(results) < max_results:
                        await progress_callback(len(results), max_results, total_attempts, None)

                    await asyncio.sleep(0.05)

            self.global_stats["completed_searches"] += 1

        except Exception as e:
            print(f"Filtered search error: {e}")
        finally:
            self.active_searches[user_id] = False

        return {
            "collection": "Фильтрованный поиск",
            "slug": "filtered",
            "gifts": results,
            "total_found": len(results),
            "attempts": total_attempts,
            "conversion": round(len(results) / total_attempts * 100, 2) if total_attempts > 0 else 0,
            "debug": self.get_debug_stats(),
        }

    @staticmethod
    def _parse_rarity_percent(raw: Optional[str]) -> Optional[float]:
        if not raw:
            return None
        cleaned = raw.replace("%", "").replace(",", ".").strip()
        try:
            return float(cleaned)
        except ValueError:
            return None

    def stop_search(self, user_id: int) -> bool:
        if user_id in self.active_searches:
            self.active_searches[user_id] = False
            return True
        return False
    
    def is_searching(self, user_id: int) -> bool:
        return self.active_searches.get(user_id, False)
    
    def get_search_stats(self, user_id: int) -> Optional[Dict]:
        return self.search_stats.get(user_id)
    
    def get_global_stats(self) -> Dict:
        uptime = datetime.now() - self.global_stats["start_time"]
        return {
            **self.global_stats,
            "uptime_seconds": int(uptime.total_seconds()),
            "active_searches": sum(1 for v in self.active_searches.values() if v)
        }

    def get_debug_stats(self) -> Dict[str, int]:
        return dict(self.debug_stats)

    def reset_debug_stats(self):
        for key in self.debug_stats:
            self.debug_stats[key] = 0


fragment_parser = FragmentParser()

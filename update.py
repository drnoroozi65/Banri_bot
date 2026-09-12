import json
import urllib.request
import urllib.parse
import os
import sys
import re
import time

SCRAPER_KEY = os.environ.get('SCRAPER_API_KEY', '')
API_BASE = "https://banriland.com/wp-json/wc/store/v1/products"

def fetch_page(target_url, retries=3):
    for attempt in range(retries):
        try:
            params = {
                'api_key': SCRAPER_KEY,
                'url': target_url,
                'country_code': 'ir',
                'render': 'false',
            }
            url = 'https://api.scraperapi.com/?' + urllib.parse.urlencode(params)
            req = urllib.request.Request(url, headers={'User-Agent': 'Mozilla/5.0'})
            with urllib.request.urlopen(req, timeout=120) as r:
                text = r.read().decode('utf-8')
                data = json.loads(text)
                return data
        except Exception as e:
            print(f"    attempt {attempt+1} failed: {e}")
            if attempt < retries - 1:
                time.sleep(5)
    return None

def fetch_all():
    if not SCRAPER_KEY:
        print("SCRAPER_API_KEY not set")
        return []
    all_products = []
    for page in range(1, 11):
        target = f"{API_BASE}?per_page=100&page={page}"
        print(f"Fetching page {page}...")
        data = fetch_page(target)
        if data is None:
            print(f"  page {page}: FAILED after retries, skipping")
            continue
        if not isinstance(data, list):
            print(f"  page {page}: not a list, skipping")
            continue
        print(f"  page {page}: {len(data)} items")
        if len(data) == 0:
            print(f"  page {page}: empty, stopping")
            break
        all_products.extend(data)
        time.sleep(2)
    return all_products

def build_db(products):
    db = []
    seen = set()
    for p in products:
        if not p.get('prices') or not p['prices'].get('price'):
            continue
        try:
            price = int(p['prices']['price'])
        except:
            continue
        if price <= 0:
            continue
        name = p['name']
        if name in seen:
            continue
        seen.add(name)
        
        in_stock = bool(p.get('is_in_stock', True))
        regular_price = 0
        try:
            if p['prices'].get('regular_price'):
                regular_price = int(p['prices']['regular_price'])
        except:
            pass
        
        db.append({
            'name': name,
            'price': price,
            'regular_price': regular_price,
            'link': p['permalink'],
            'img': (p['images'][0]['src'] if p.get('images') else '') or '',
            'sale': bool(p.get('on_sale')),
            'cat': [c['name'] for c in p.get('categories', [])],
            'stock': in_stock
        })
    return db

def update_html(db):
    with open('index.html', encoding='utf-8') as f:
        content = f.read()
    data_json = json.dumps(db, ensure_ascii=False).replace('</', '<\\/')
    new_content = re.sub(r'var DB\s*=\s*\[.*?\];', f'var DB = {data_json};', content, count=1, flags=re.DOTALL)
    if new_content == content:
        return False
    with open('index.html', 'w', encoding='utf-8') as f:
        f.write(new_content)
    return True

def main():
    print("Fetching products...")
    products = fetch_all()
    print(f"Total fetched: {len(products)}")
    if not products:
        print("No products")
        sys.exit(0)
    db = build_db(products)
    print(f"{len(db)} valid products")
    if len(db) < 10:
        print("Too few, aborting")
        sys.exit(0)
    if update_html(db):
        print(f"Updated: {len(db)} products")
    else:
        print("No changes")

if __name__ == '__main__':
    main()
